#!/usr/bin/env python3
"""test drivers"""
import os
import platform
import re
import shutil
import sys
import time
import traceback
from pathlib import Path

import psutil

from allure_commons._allure import attach
from allure_commons.model2 import Status, StatusDetails, Label
from allure_commons.types import LabelType

from arangodb.installers import create_config_installer_set, RunProperties
from arangodb.starter.deployments import (
    RunnerType,
    make_runner,
    runner_strings,
    STARTER_MODES,
)
from arangodb.starter.deployments.cluster_perf import ClusterPerf
from debugger_tests.debugger_test_suite import DebuggerTestSuite
from license_manager_tests.basic_test_suite import BasicLicenseManagerTestSuite
from license_manager_tests.upgrade.upgrade_test_suite import UpgradeLicenseManagerTestSuite
from package_installation_tests.community_package_installation_test_suite import CommunityPackageInstallationTestSuite
from package_installation_tests.enterprise_package_installation_test_suite import EnterprisePackageInstallationTestSuite
from reporting.reporting_utils import RtaTestcase, AllureTestSuiteContext, init_allure
from reporting.reporting_utils2 import generate_suite_name
from siteconfig import SiteConfig
from test_suites.misc.binary_test_suite import BinaryComplianceTestSuite
from test_suites_core.cli_test_suite import CliTestSuiteParameters
from overload_thread import spawn_overload_watcher_thread, shutdown_overload_watcher_thread

import tools.loghelper as lh
from tools.killall import kill_all_processes
HAVE_SAN = False
for varname in [
    'TSAN_OPTIONS', 'UBSAN_OPTIONS', 'LSAN_OPTIONS', 'ASAN_OPTIONS'
]:
    HAVE_SAN = HAVE_SAN or varname in os.environ
try:
    # pylint: disable=unused-import
    from tools.external_helpers.license_generator.license_generator import create_license

    EXTERNAL_HELPERS_LOADED = True
except ModuleNotFoundError as exc:
    print("External helpers not found. License manager tests will not run.")
    EXTERNAL_HELPERS_LOADED = False

IS_WINDOWS = platform.win32_ver()[0] != ""
IS_LINUX = sys.platform == "linux"

FULL_TEST_SUITE_LIST = [
    EnterprisePackageInstallationTestSuite,
    CommunityPackageInstallationTestSuite,
    BasicLicenseManagerTestSuite,
    UpgradeLicenseManagerTestSuite,
    DebuggerTestSuite,
    BinaryComplianceTestSuite,
]


class TestDriver:
    """driver base class to run different tests"""

    # pylint: disable=too-many-arguments disable=too-many-locals disable=too-many-instance-attributes
    def __init__(self, **kwargs):
        self.sitecfg = SiteConfig("")
        self.use_monitoring = kwargs["monitoring"]
        if self.use_monitoring:
            spawn_overload_watcher_thread(self.sitecfg)
        self.launch_dir = Path.cwd()
        if IS_WINDOWS and "PYTHONUTF8" not in os.environ:
            raise Exception("require PYTHONUTF8=1 in the environment")
        if "WORKSPACE" in os.environ:
            self.launch_dir = Path(os.environ["WORKSPACE"])

        if not kwargs["test_data_dir"].is_absolute():
            kwargs["test_data_dir"] = self.launch_dir / kwargs["test_data_dir"]
        if not kwargs["test_data_dir"].exists():
            kwargs["test_data_dir"].mkdir(parents=True, exist_ok=True)
        os.chdir(kwargs["test_data_dir"])

        if not kwargs["package_dir"].is_absolute():
            kwargs["package_dir"] = (self.launch_dir / kwargs["package_dir"]).resolve()
        if not kwargs["package_dir"].exists():
            kwargs["package_dir"].mkdir(parents=True, exist_ok=True)
        kwargs["base_config"].package_dir = kwargs["package_dir"]
        self.cluster_nodes = kwargs["cluster_nodes"]
        self.base_config = kwargs["base_config"]
        self.arangods = []
        self.base_config.arangods = self.arangods

        lh.configure_logging(kwargs["verbose"])
        self.abort_on_error = kwargs["abort_on_error"]

        self.use_auto_certs = kwargs["use_auto_certs"]
        self.selenium = kwargs["selenium"]
        self.selenium_driver_args = kwargs["selenium_driver_args"]
        self.selenium_include_suites = (
            [] if "ui_include_test_suites" not in kwargs else kwargs["ui_include_test_suites"]
        )
        init_allure(
            results_dir=kwargs["alluredir"], clean=kwargs["clean_alluredir"], zip_package=self.base_config.zip_package
        )
        self.installer_type = None

        self.cli_test_suite_params = CliTestSuiteParameters.from_dict(**kwargs)
        if HAVE_SAN:
            symbolizer = Path('/work/ArangoDB/utils/llvm-symbolizer-server.py')
            if not symbolizer.exists():
                raise Exception(f"couldn't locate symbolizer {str(symbolizer)}")
            print(f"launching symbolizer {str(symbolizer)}")
            self.symbolizer = psutil.Popen(str(symbolizer), cwd=Path('/work/ArangoDB'))

    def __del__(self):
        self.destructor()

    def destructor(self):
        """shutdown this environment"""
        self._stop_monitor()
        if HAVE_SAN:
            self.symbolizer.kill()
            self.symbolizer.wait()

    def _stop_monitor(self):
        if self.use_monitoring:
            shutdown_overload_watcher_thread()

    def set_r_limits(self):
        """on linux manipulate ulimit values"""
        # pylint: disable=import-outside-toplevel
        if not IS_WINDOWS:
            import resource

            resource.setrlimit(resource.RLIMIT_CORE, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))

    def copy_packages_to_result(self, installers):
        """copy packages in test to the report directory (including debug symbols)"""
        if not installers[0][1].copy_for_result:
            print("Skipping copy_packages_to_result for this installer")
            return

        if not installers[0][1].find_crash(installers[0][0].base_test_dir):
            return
        for installer_set in installers:
            for package in [
                installer_set[1].server_package,
                installer_set[1].debug_package,
                installer_set[1].client_package,
            ]:
                if package is not None:
                    print(Path.cwd())
                    print(
                        "Copying package into result: "
                        + str(installer_set[1].cfg.package_dir / package)
                        + " => "
                        + str(Path.cwd())
                    )
                    shutil.copyfile(installer_set[1].cfg.package_dir / package, Path.cwd() / package)
                    attach.file(
                        Path.cwd() / package,
                        "source archive used in tests: " + str(package),
                        installer_set[1].extension,
                    )

    def get_packaging_shorthand(self):
        """get the [DEB|RPM|EXE|DMG|ZIP|targz] from the installer"""
        if self.installer_type:
            return self.installer_type
        installers = create_config_installer_set(
            ["3.3.3"], self.base_config, "all", RunProperties(False, False, False, False), False
        )
        self.installer_type = installers[0][1].installer_type.split(" ")[0].replace(".", "")
        return self.installer_type

    def reset_test_data_dir(self, test_data_dir):
        """set the test data directory for the next testrun, make sure its clean."""
        self.base_config.test_data_dir = test_data_dir
        if test_data_dir.exists():
            shutil.rmtree(test_data_dir)
            if "REQUESTS_CA_BUNDLE" in os.environ:
                del os.environ["REQUESTS_CA_BUNDLE"]
        test_data_dir.mkdir(exist_ok=True)
        while not test_data_dir.exists():
            time.sleep(1)

    # pylint: disable=broad-except
    def run_cleanup(self, run_properties: RunProperties, versions=None):
        """main"""
        if versions is None:
            versions = ["3.3.3"]
        installer_set = create_config_installer_set(versions, self.base_config, "all", run_properties, False)
        inst = installer_set[0][1]
        if inst.calc_config_file_name().is_file():
            inst.load_config()
            inst.cfg.interactive = False
            inst.stop_service()
            installer_set[0][0].set_directories(inst.cfg)
        kill_all_processes()
        kill_all_processes()
        starter_mode = [
            RunnerType.SINGLE,
            RunnerType.LEADER_FOLLOWER,
            RunnerType.ACTIVE_FAILOVER,
            RunnerType.CLUSTER,
            RunnerType.DC2DC,
        ]
        for runner_type in starter_mode:
            assert runner_type
            runner = make_runner(runner_type, False, "none", [], [], installer_set, run_properties, self.cluster_nodes)
            runner.cleanup()
        if inst.calc_config_file_name().is_file():
            try:
                inst.un_install_debug_package()
            except Exception:
                print("nothing to uninstall")
            try:
                inst.un_install_client_package()
            except Exception:
                print("nothing to uninstall")
            inst.un_install_server_package()
        else:
            print("Cannot uninstall package without config.yml!")
        inst.cleanup_system()

    # pylint: disable=too-many-arguments disable=too-many-locals,
    # pylint: disable=broad-except, disable=too-many-branches, disable=too-many-statements
    def run_upgrade(self, versions: list, run_props: RunProperties):
        """execute upgrade tests"""
        lh.section("startup")
        results = []
        for runner_type in STARTER_MODES[self.base_config.starter_mode]:
            installers = create_config_installer_set(versions, self.base_config, "all", run_props, self.use_auto_certs)
            # pylint: disable=unused-variable
            old_inst = installers[0][1]
            new_inst = installers[1][1]

            parent_test_suite_name = generate_suite_name(
                properties=run_props, versions=versions, runner_type=None, installer_type=new_inst.installer_type
            )

            with AllureTestSuiteContext(
                parent_test_suite_name=parent_test_suite_name,
                suite_name=runner_strings[runner_type],
                labels=[Label(name=LabelType.TAG, value=f"HB: {self.get_hb_provider()}")]
                if self.get_hb_provider() is not None
                else None,
            ):
                with RtaTestcase(runner_strings[runner_type] + " main flow") as testcase:
                    one_result = {
                        "testrun name": run_props.testrun_name,
                        "testscenario": runner_strings[runner_type],
                        "success": True,
                        "messages": [],
                        "progress": "",
                    }
                    try:
                        kill_all_processes()
                        runner = None
                        lh.section("configuration")
                        print(
                            """
                        starter mode: {starter_mode}
                        old version: {old_version}
                        {cfg_repr}
                        """.format(
                                **{
                                    "starter_mode": str(self.base_config.starter_mode),
                                    "old_version": str(versions[0]),
                                    "cfg_repr": repr(installers[1][0]),
                                }
                            )
                        )
                        runner = make_runner(
                            runner_type,
                            self.abort_on_error,
                            self.selenium,
                            self.selenium_driver_args,
                            self.selenium_include_suites,
                            installers,
                            run_props,
                            use_auto_certs=self.use_auto_certs,
                            cluster_nodes=self.cluster_nodes,
                        )
                        if not runner or runner.runner_type == RunnerType.NONE:
                            testcase.context.status = Status.SKIPPED
                            one_result["message"] = f"Skipping {runner_type}"
                            if runner:
                                one_result["message"] += runner.msg
                            print(f"Skipping {runner_type}")
                            continue
                        if run_props.force_one_shard and not runner.force_one_shard:
                            testcase.context.status = Status.SKIPPED
                            testcase.context.statusDetails = StatusDetails(
                                message=f"One shard is not supported for {runner.name}"
                            )
                            runner.cleanup()
                            continue

                        try:
                            runner.run()
                            runner.cleanup()
                            testcase.context.status = Status.PASSED
                        except Exception as ex:
                            one_result["success"] = False
                            one_result["messages"].append("\n" + str(ex))
                            one_result["progress"] += runner.get_progress()
                            runner.take_screenshot()
                            if runner.agency:
                                runner.agency.acquire_dump()
                            runner.search_for_warnings()
                            runner.quit_selenium()
                            kill_all_processes()
                            runner.zip_test_dir()
                            self.copy_packages_to_result(installers)
                            testcase.context.status = Status.FAILED
                            testcase.context.statusDetails = StatusDetails(
                                message=str(ex),
                                trace="".join(traceback.TracebackException.from_exception(ex).format()),
                            )
                            if self.abort_on_error:
                                raise ex
                            one_result["progress"] += (
                                "\n -> "
                                + str(ex)
                                + "\n"
                                + "".join(traceback.TracebackException.from_exception(ex).format())
                            )
                            traceback.print_exc()
                            lh.section("uninstall on error")
                            # pylint: disable=consider-using-enumerate
                            for i in range(len(installers)):
                                installer = installers[i][1]
                                installer.un_install_debug_package()
                                installer.un_install_server_package()
                                installer.cleanup_system()
                            try:
                                runner.cleanup()
                            finally:
                                pass
                            results.append(one_result)
                            continue
                        if runner.ui_tests_failed:
                            failed_test_names = [
                                f'"{row["Name"]}"'
                                for row in runner.ui_test_results_table
                                if not row["Result"] == "PASSED"
                            ]
                            one_result["success"] = False
                            one_result["messages"].append(
                                f'The following UI tests failed: {", ".join(failed_test_names)}.'
                                + "See allure report for details."
                            )
                        lh.section("uninstall")
                        # pylint: disable=consider-using-enumerate
                        for i in range(len(installers)):
                            installer = installers[i][1]
                            installer.un_install_server_package()
                            lh.section("check system")
                            installer.check_uninstall_cleanup()
                            try:
                                lh.section("remove residuals")
                                installer.cleanup_system()
                            except Exception:
                                print("Ignoring cleanup error!")

                    except Exception as ex:
                        print("Caught. " + str(ex))
                        one_result["success"] = False
                        one_result["messages"].append(str(ex))
                        one_result["progress"] += "\naborted outside of testcodes"
                        if self.abort_on_error:
                            print("re-throwing.")
                            raise ex
                        traceback.print_exc()
                        kill_all_processes()
                        if runner:
                            try:
                                runner.cleanup()
                            except Exception as exception:
                                print("Ignoring runner cleanup error! Exception:")
                                print(str(exception))
                                print("".join(traceback.TracebackException.from_exception(exception).format()))
                        try:
                            print("Cleaning up system after error:")
                            # pylint: disable=consider-using-enumerate
                            for i in range(len(installers)):
                                installer = installers[i][1]
                                installer.un_install_debug_package()
                                installer.un_install_server_package()
                                installer.cleanup_system()
                        except Exception:
                            print("Ignoring old cleanup error!")

                    results.append(one_result)
        return results

    # fmt: off
    # pylint: disable=too-many-arguments disable=too-many-locals
    def run_test(self,
                 test_mode,
                 deployment_mode,
                 versions: list,
                 run_props: RunProperties):
        # fmt: on
        """ main """
        results = []

        do_install = test_mode in ["all", "install"]
        do_uninstall = test_mode in ["all", "uninstall"]
        do_tests = test_mode in ["all", "tests"]

        installers = create_config_installer_set(
            versions,
            self.base_config,
            deployment_mode,
            run_props,
            self.use_auto_certs
        )
        lh.section("configuration")
        print(
            """
        mode: {mode}
        {cfg_repr}
        """.format(
                **{"mode": str(test_mode), "cfg_repr": repr(installers[0][0])}
            )
        )

        count = 1
        for runner_type in STARTER_MODES[self.base_config.starter_mode]:
            parent_test_suite_name = generate_suite_name(properties=run_props, versions=versions, runner_type=None,
                                                         installer_type=installers[0][1].installer_type)
            with AllureTestSuiteContext(parent_test_suite_name=parent_test_suite_name,
                                        suite_name=runner_strings[runner_type],
                                        labels=[Label(name=LabelType.TAG, value=f"HB: {self.get_hb_provider()}")]
                                        if self.get_hb_provider() is not None else None):
                with RtaTestcase(runner_strings[runner_type] + " main flow") as testcase:
                    one_result = {
                        "testrun name": run_props.testrun_name,
                        "testscenario": runner_strings[runner_type],
                        "success": True,
                        "messages": [],
                        "progress": "",
                    }
                    runner = make_runner(
                        runner_type,
                        self.abort_on_error,
                        self.selenium,
                        self.selenium_driver_args,
                        self.selenium_include_suites,
                        installers,
                        run_props,
                        use_auto_certs=self.use_auto_certs,
                        cluster_nodes=self.cluster_nodes
                    )
                    if not runner or runner.runner_type == RunnerType.NONE:
                        testcase.context.status = Status.SKIPPED
                        one_result["message"] = f"Skipping {runner_type}"
                        if runner:
                            one_result["message"] += runner.msg
                        print(f"Skipping {runner_type}")
                        continue
                    if run_props.force_one_shard and not runner.force_one_shard:
                        testcase.context.status = Status.SKIPPED
                        testcase.context.statusDetails = StatusDetails(
                        message=f"One shard is not supported for {runner.name}"
                        )
                        runner.cleanup()
                        continue
                    if run_props.replication2 and not runner.replication2:
                        testcase.context.status = Status.SKIPPED
                        testcase.context.statusDetails = StatusDetails(
                        message=f"Replication v. 2 is not supported for {runner.name}, version {runner.versionstr}"
                        )
                        runner.cleanup()
                        continue
                    # install on first run:
                    runner.do_install = (count == 1) and do_install
                    # only uninstall after the last test:
                    must_uninstall_after_this_run = (count == len(
                        STARTER_MODES[deployment_mode]))
                    runner.do_uninstall = must_uninstall_after_this_run and do_uninstall
                    runner.do_starter_test = do_tests

                    try:
                        runner.run()
                        runner.cleanup()
                        testcase.context.status = Status.PASSED
                    # pylint: disable=broad-except
                    except Exception as ex:
                        one_result["success"] = False
                        one_result["messages"].append(str(ex))
                        one_result["progress"] += runner.get_progress()
                        runner.take_screenshot()
                        if runner.agency:
                            runner.agency.acquire_dump()
                        runner.search_for_warnings()
                        runner.quit_selenium()
                        kill_all_processes()
                        runner.zip_test_dir()
                        self.copy_packages_to_result(installers)
                        testcase.context.status = Status.FAILED
                        testcase.context.statusDetails = StatusDetails(message=str(ex),
                                                                       trace="".join(
                                                                           traceback.TracebackException.from_exception(
                                                                               ex).format()))
                        if must_uninstall_after_this_run and do_uninstall:
                            lh.section("uninstall on error")
                            installers[0][1].un_install_debug_package()
                            installers[0][1].un_install_server_package()
                            installers[0][1].cleanup_system()
                            lh.section("uninstall on error")
                        if self.abort_on_error:
                            raise ex
                        traceback.print_exc()
                        try:
                            runner.cleanup()
                        finally:
                            pass
                        results.append(one_result)
                        kill_all_processes()
                        count += 1
                        continue

                    if runner.ui_tests_failed:
                        failed_test_names = [f'"{row["Name"]}"' for row in
                                             runner.ui_test_results_table if
                                             not row["Result"] == "PASSED"]
                        one_result["success"] = False
                        # pylint: disable=line-too-long
                        one_result[
                            "messages"].append(
                            f'The following UI tests failed: {", ".join(failed_test_names)}. See allure report for details.')
                    results.append(one_result)
                    kill_all_processes()
                    count += 1

        lh.section("uninstall")
        installers[0][1].un_install_server_package()
        lh.section("check system")
        installers[0][1].check_uninstall_cleanup()
        lh.section("remove residuals")
        try:
            # pylint: disable=consider-using-enumerate
            for i in range(len(installers)):
                installer = installers[i][1]
                installer.cleanup_system()
        except Exception:
            print("Ignoring cleanup error!")

        return results

    # fmt: off
    # pylint: disable=too-many-arguments disable=too-many-locals
    def run_perf_test(self,
                      deployment_mode,
                      versions: list,
                      frontends,
                      scenario,
                      run_props: RunProperties):
        # fmt: on
        """ main """
        results = []
        do_install = deployment_mode in ["all", "install"]
        do_uninstall = deployment_mode in ["all", "uninstall"]

        installers = create_config_installer_set(
            versions,
            self.base_config,
            deployment_mode,
            run_props,
            self.use_auto_certs
        )
        lh.section("configuration")
        print(
            """
        mode: {mode}
        {cfg_repr}
        """.format(
                **{"mode": str(deployment_mode), "cfg_repr": repr(installers[0][0])}
            )
        )
        inst = installers[0][1]

        split_host = re.compile(r"([a-z]*)://([0-9.:]*):(\d*)")

        if len(frontends) > 0:
            for frontend in frontends:
                print("remote")
                host_parts = re.split(split_host, frontend)
                inst.cfg.add_frontend(host_parts[1], host_parts[2], host_parts[3])
        inst.cfg.scenario = self.launch_dir / scenario
        runner = ClusterPerf(
            RunnerType.CLUSTER,
            self.abort_on_error,
            installers,
            self.selenium,
            self.selenium_driver_args,
            "perf",
            run_props.ssl,
            run_props.replication2,
            use_auto_certs=self.use_auto_certs
        )
        runner.do_install = do_install
        runner.do_uninstall = do_uninstall
        failed = False
        try:
            if not runner.run():
                failed = True
                results.append({
                    "testrun name": runner.testrun_name,
                    "testscenario": runner_strings[RunnerType.CLUSTER],
                    "success": not failed,
                    "messages": [],
                    "progress": "",
                })
        except Exception as ex:
            failed = True
            print("".join(traceback.TracebackException.from_exception(ex).format()))
            results.append({
                "testrun name": runner.testrun_name,
                "testscenario": runner_strings[RunnerType.CLUSTER],
                "success": False,
                "messages": [str(ex)],
                "trace": "".join(traceback.TracebackException.from_exception(ex).format()),
                "progress": "",
            })
        if len(frontends) == 0:
            kill_all_processes()
        return results

    def run_test_suites(self, include_suites: tuple = (), exclude_suites: tuple = (),
                        params: CliTestSuiteParameters = None):
        """run a testsuite"""
        if not params:
            params = self.cli_test_suite_params
        suite_classes=[]
        if len(include_suites) == 0 and len(exclude_suites) == 0:
            suite_classes.extend(FULL_TEST_SUITE_LIST)
        if len(include_suites) > 0 and len(exclude_suites) == 0:
            for suite_class in FULL_TEST_SUITE_LIST:
                if suite_class.__name__ in include_suites:
                    suite_classes.append(suite_class)
        elif len(exclude_suites) > 0 and len(include_suites) == 0:
            suite_classes.extend(FULL_TEST_SUITE_LIST)
            for exclude_suite_class in exclude_suites:
                for suite_class in suite_classes.copy():
                    if suite_class.__name__ == exclude_suite_class:
                        suite_classes.remove(suite_class)
                        break
        else:
            raise Exception(
                "Please specify one or none of the following parameters: --exclude-test-suite, --include-test-suite.")

        results = []
        for suite_class in suite_classes:
            suite = suite_class(params)
            suite.run()
            result = {
                "testrun name": suite.suite_name,
                "testscenario": "",
                "success": True,
                "messages": [],
                "progress": "",
            }
            if suite.there_are_failed_tests() or suite.is_broken():
                result["success"] = False
                for one_result in suite.test_results:
                    result["messages"].append(one_result.message)
            results.append(result)
        return results

    def get_hb_provider(self):
        """ get HB provider value """
        hb_provider = None
        try:
            hb_provider = self.base_config.hb_cli_cfg.hb_provider
        except AttributeError:
            pass
        return hb_provider
