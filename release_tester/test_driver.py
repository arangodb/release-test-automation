#!/usr/bin/env python3
"""test drivers"""
from pathlib import Path
import platform
import os
import sys
import time
import traceback

import shutil
import distro

from allure_commons.model2 import Status, StatusDetails

from reporting.reporting_utils import RtaTestcase, AllureTestSuiteContext
from tools.killall import kill_all_processes
from arangodb.installers import create_config_installer_set, RunProperties, InstallerBaseConfig
from arangodb.starter.deployments import (
    RunnerType,
    make_runner,
    runner_strings,
    STARTER_MODES,
)
import tools.loghelper as lh

IS_WINDOWS = platform.win32_ver()[0] != ""
IS_LINUX = sys.platform == "linux"

class TestDriver:
    """driver base class to run different tests"""
    # pylint: disable=too-many-arguments disable=too-many-locals
    def __init__(
            self,
            verbose,
            package_dir: Path,
            test_data_dir: Path,
            alluredir: Path,
            clean_alluredir,
            zip_package,
            hot_backup,
            interactive,
            starter_mode,
            stress_upgrade,
            abort_on_error,
            publicip,
            selenium,
            selenium_driver_args,
            use_auto_certs,
            ):
        if not test_data_dir.is_absolute():
            test_data_dir = Path.cwd() / test_data_dir
        os.chdir(test_data_dir)

        self.base_config = InstallerBaseConfig(verbose,
                                               zip_package,
                                               hot_backup,
                                               package_dir,
                                               test_data_dir,
                                               starter_mode,
                                               publicip,
                                               interactive,
                                               stress_upgrade)
        lh.configure_logging(verbose)
        self.abort_on_error = abort_on_error
        self.alluredir = alluredir
        self.clean_alluredir = clean_alluredir
        self.use_auto_certs = use_auto_certs
        self.selenium = selenium
        self.selenium_driver_args = selenium_driver_args

    # pylint: disable=no-self-use
    def set_r_limits(self):
        """on linux manipulate ulimit values"""
        # pylint: disable=C0415
        if not IS_WINDOWS:
            import resource
            resource.setrlimit(resource.RLIMIT_CORE,
                               (resource.RLIM_INFINITY,
                                resource.RLIM_INFINITY))

    def reset_test_data_dir(self, test_data_dir):
        """set the test data directory for the next testrun, make sure its clean."""
        self.base_config.test_data_dir = test_data_dir
        if test_data_dir.exists():
            shutil.rmtree(test_data_dir)
            if "REQUESTS_CA_BUNDLE" in os.environ:
                del os.environ["REQUESTS_CA_BUNDLE"]
        test_data_dir.mkdir()
        while not test_data_dir.exists():
            time.sleep(1)

    # pylint: disable=W0703
    def run_cleanup(self, run_properties: RunProperties):
        """main"""
        installer_set = create_config_installer_set(
            ["3.3.3"],
            self.base_config,
            "all",
            run_properties
        )
        inst = installer_set[0][1]
        if inst.calc_config_file_name().is_file():
            inst.load_config()
            inst.cfg.interactive = False
            inst.stop_service()
            installer_set[0][0].set_directories(inst.cfg)
        kill_all_processes()
        kill_all_processes()
        starter_mode = [
            RunnerType.LEADER_FOLLOWER,
            RunnerType.ACTIVE_FAILOVER,
            RunnerType.CLUSTER,
            RunnerType.DC2DC,
        ]
        for runner_type in starter_mode:
            assert runner_type
            runner = make_runner(runner_type, False, "none", [], installer_set, run_properties)
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

    # pylint: disable=R0913 disable=R0914, disable=W0703, disable=R0912, disable=R0915
    def run_upgrade(self,
                    versions: list,
                    run_props: RunProperties):
        """execute upgrade tests"""
        lh.section("startup")
        results = []
        for runner_type in STARTER_MODES[self.base_config.starter_mode]:
            installers = create_config_installer_set(
                versions,
                self.base_config,
                "all",
                run_props,
            )
            old_inst = installers[0][1]
            new_inst = installers[1][1]

            with AllureTestSuiteContext(
                self.alluredir,
                self.clean_alluredir,
                run_props,
                self.base_config.zip_package,
                versions,
                None,
                True,
                runner_strings[runner_type],
                None,
                new_inst.installer_type,
            ):
                with RtaTestcase(runner_strings[runner_type] + " main flow") as testcase:
                    if (not run_props.enterprise or IS_WINDOWS) and runner_type == RunnerType.DC2DC:
                        testcase.context.status = Status.SKIPPED
                        testcase.context.statusDetails = StatusDetails(
                            message="DC2DC is not applicable to Community packages."
                        )
                        continue
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
                        if runner_type:
                            runner = make_runner(
                                runner_type,
                                self.abort_on_error,
                                self.selenium,
                                self.selenium_driver_args,
                                installers,
                                run_props,
                                use_auto_certs=self.use_auto_certs,
                            )
                            if runner:
                                try:
                                    runner.run()
                                    runner.cleanup()
                                    testcase.context.status = Status.PASSED
                                except Exception as ex:
                                    one_result["success"] = False
                                    one_result["messages"].append(str(ex))
                                    one_result["progress"] += runner.get_progress()
                                    runner.take_screenshot()
                                    runner.agency_acquire_dump()
                                    runner.search_for_warnings()
                                    runner.quit_selenium()
                                    kill_all_processes()
                                    runner.zip_test_dir()
                                    testcase.context.status = Status.FAILED
                                    testcase.context.statusDetails = StatusDetails(
                                        message=str(ex),
                                        trace="".join(traceback.TracebackException.from_exception(ex).format()),
                                    )
                                    if self.abort_on_error:
                                        raise ex
                                    traceback.print_exc()
                                    lh.section("uninstall on error")
                                    old_inst.un_install_debug_package()
                                    old_inst.un_install_server_package()
                                    old_inst.cleanup_system()
                                    try:
                                        runner.cleanup()
                                    finally:
                                        pass
                                    continue
                                if runner.ui_tests_failed:
                                    failed_test_names = [
                                        f'"{row["Name"]}"'
                                        for row in runner.ui_test_results_table
                                        if not row["Result"] == "PASSED"
                                    ]
                                    one_result["success"] = False
                                    one_result["messages"].append(
    f'The following UI tests failed: {", ".join(failed_test_names)}. See allure report for details.'
                                    )
                        lh.section("uninstall")
                        new_inst.un_install_server_package()
                        lh.section("check system")
                        new_inst.check_uninstall_cleanup()
                        lh.section("remove residuals")
                        try:
                            old_inst.cleanup_system()
                        except Exception:
                            print("Ignoring old cleanup error!")
                        try:
                            print("Ignoring new cleanup error!")
                            new_inst.cleanup_system()
                        except Exception:
                            print("Ignoring general cleanup error!")
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
                            old_inst.un_install_debug_package()
                            old_inst.un_install_server_package()
                            old_inst.cleanup_system()
                        except Exception:
                            print("Ignoring old cleanup error!")
                        try:
                            print("Ignoring new cleanup error!")
                            new_inst.un_install_debug_package()
                            new_inst.un_install_server_package()
                            new_inst.cleanup_system()
                        except Exception:
                            print("Ignoring new cleanup error!")
                    results.append(one_result)
        return results

    # fmt: off
    # pylint: disable=R0913 disable=R0914
    def run_test(self,
                 deployment_mode,
                 versions: list,
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
            run_props
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

        count = 1
        for runner_type in STARTER_MODES[self.base_config.starter_mode]:
            with AllureTestSuiteContext(self.alluredir,
                                        self.clean_alluredir,
                                        run_props,
                                        self.base_config.zip_package,
                                        versions,
                                        True,
                                        None,
                                        runner_strings[runner_type],
                                        None,
                                        installers[0][1].installer_type):
                with RtaTestcase(runner_strings[runner_type] + " main flow") as testcase:
                    if (runner_type == RunnerType.DC2DC and
                        (not run_props.enterprise or IS_WINDOWS)):
                        testcase.context.status = Status.SKIPPED
                        testcase.context.statusDetails = StatusDetails(
                            message="DC2DC is not applicable to Community packages.")
                        continue
                    runner = make_runner(
                        runner_type,
                        self.abort_on_error,
                        self.selenium,
                        self.selenium_driver_args,
                        installers,
                        run_props,
                        use_auto_certs=self.use_auto_certs,
                    )
                    # install on first run:
                    runner.do_install = (count == 1) and do_install
                    # only uninstall after the last test:
                    runner.do_uninstall = (count == len(STARTER_MODES[deployment_mode])) and do_uninstall
                    one_result = {
                        "testrun name": run_props.testrun_name,
                        "testscenario": runner_strings[runner_type],
                        "success": True,
                        "messages": [],
                        "progress": "",
                    }
                    try:
                        runner.run()
                        runner.cleanup()
                        testcase.context.status = Status.PASSED
                    # pylint: disable=W0703
                    except Exception as ex:
                        one_result["success"] = False
                        one_result["messages"].append(str(ex))
                        one_result["progress"] += runner.get_progress()
                        runner.take_screenshot()
                        runner.agency_acquire_dump()
                        runner.search_for_warnings()
                        runner.quit_selenium()
                        kill_all_processes()
                        runner.zip_test_dir()
                        testcase.context.status = Status.FAILED
                        testcase.context.statusDetails = StatusDetails(message=str(ex),
                                                                       trace="".join(
                                                                           traceback.TracebackException.from_exception(
                                                                               ex).format()))
                        if self.abort_on_error:
                            raise ex
                        traceback.print_exc()
                        lh.section("uninstall on error")
                        try:
                            runner.cleanup()
                        finally:
                            pass
                        continue

                    if runner.ui_tests_failed:
                        failed_test_names = [f'"{row["Name"]}"' for row in
                                             runner.ui_test_results_table if
                                             not row["Result"] == "PASSED"]
                        one_result["success"] = False
                        one_result[
                            "messages"].append(
    f'The following UI tests failed: {", ".join(failed_test_names)}. See allure report for details.')

                    kill_all_processes()
                    count += 1

        return results

    # pylint: disable=R0913 disable=R0914, disable=W0703, disable=R0912, disable=R0915
    def run_conflict_tests(
            self,
            versions: list,
            enterprise: bool
    ):
        """run package conflict tests"""
        # disable conflict tests for Windows and MacOS
        if not IS_LINUX:
            return [
                {
                    "testrun name": "Package installation/uninstallation tests were skipped because OS is not Linux.",
                    "testscenario": "",
                    "success": True,
                    "messages": [],
                    "progress": "",
                }
            ]
        # disable conflict tests for zip packages
        if self.base_config.zip_package:
            return [
                {
                    "testrun name": "Package installation/uninstallation tests were skipped for zip packages.",
                    "testscenario": "",
                    "success": True,
                    "messages": [],
                    "progress": "",
                }
            ]
        # disable conflict tests for deb packages for now.
        if distro.linux_distribution(full_distribution_name=False)[0] in ["debian", "ubuntu"]:
            return [
                {
                    "testrun name": "Package installation/uninstallation tests are temporarily" +
                      "disabled for debian-based linux distros. Waiting for BTS-684",
                    "testscenario": "",
                    "success": True,
                    "messages": [],
                    "progress": "",
                }
            ]
        suite = None
        # pylint: disable=import-outside-toplevel
        if enterprise:
            from package_installation_tests.enterprise_package_installation_test_suite import \
                EnterprisePackageInstallationTestSuite as testSuite
        else:
            from package_installation_tests.community_package_installation_test_suite import \
                CommunityPackageInstallationTestSuite as testSuite
        suite = testSuite(
            old_version=versions[0],
            new_version=versions[1],
            alluredir=self.alluredir,
            clean_alluredir=self.clean_alluredir,
            basecfg=self.base_config
        )
        suite.run()
        result = {
            "testrun name": suite.suite_name,
            "testscenario": "",
            "success": True,
            "messages": [],
            "progress": "",
        }
        if suite.there_are_failed_tests():
            result["success"] = False
            for one_result in suite.test_results:
                result["messages"].append(one_result.message)
        return [result]
