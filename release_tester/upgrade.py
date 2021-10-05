#!/usr/bin/env python3

""" Release testing script"""
from pathlib import Path
import traceback

import sys
import platform
import click
from allure_commons.model2 import Status, Label
from allure_commons.types import LabelType

from common_options import very_common_options, common_options
from reporting.reporting_utils import configure_allure, RtaTestcase
from tools.killall import kill_all_processes
from arangodb.installers import create_config_installer_set
from arangodb.starter.deployments import (
    RunnerType,
    make_runner,
    runner_strings,
    STARTER_MODES,
)
import tools.loghelper as lh

is_windows = platform.win32_ver()[0] != ""

# pylint: disable=R0913 disable=R0914, disable=W0703, disable=R0912, disable=R0915
def run_upgrade(
    old_version,
    new_version,
    verbose,
    package_dir,
    test_data_dir,
    enterprise,
    encryption_at_rest,
    zip_package,
    interactive,
    starter_mode,
    stress_upgrade,
    abort_on_error,
    publicip,
    selenium,
    selenium_driver_args,
    testrun_name,
    ssl,
    use_auto_certs,
):
    """execute upgrade tests"""
    lh.section("startup")
    results = []
    for runner_type in STARTER_MODES[starter_mode]:
        with RtaTestcase(runner_strings[runner_type]) as testcase:
            if (not enterprise or is_windows) and runner_type == RunnerType.DC2DC:
                testcase.context.status = Status.SKIPPED
                continue
            one_result = {
                "testrun name": testrun_name,
                "testscenario": runner_strings[runner_type],
                "success": True,
                "message": "success",
                "progress": "success",
            }
            try:
                kill_all_processes()
                installers = create_config_installer_set(
                    [old_version, new_version],
                    verbose,
                    enterprise,
                    encryption_at_rest,
                    zip_package,
                    Path(package_dir),
                    Path(test_data_dir),
                    "all",
                    publicip,
                    interactive,
                    stress_upgrade,
                )
                runner = None
                old_inst = installers[0][1]
                new_inst = installers[1][1]
                lh.section("configuration")
                print(
                    """
                starter mode: {starter_mode}
                old version: {old_version}
                {cfg_repr}
                """.format(
                        **{
                            "starter_mode": str(starter_mode),
                            "old_version": old_version,
                            "cfg_repr": repr(installers[1][0]),
                        }
                    )
                )
                testcase.add_label(Label(name=LabelType.SUB_SUITE, value=new_inst.installer_type))
                if runner_type:
                    runner = make_runner(
                        runner_type,
                        abort_on_error,
                        selenium,
                        selenium_driver_args,
                        installers,
                        testrun_name,
                        ssl=ssl,
                        use_auto_certs=use_auto_certs,
                    )
                    if runner:
                        try:
                            runner.run()
                            runner.cleanup()
                            testcase.context.status = Status.PASSED
                        except Exception as ex:
                            one_result = {
                                "testrun name": testrun_name,
                                "testscenario": runner_strings[runner_type],
                                "success": False,
                                "message": str(ex),
                                "progress": runner.get_progress(),
                            }
                            results.append(one_result)
                            runner.take_screenshot()
                            runner.agency_acquire_dump()
                            runner.search_for_warnings()
                            kill_all_processes()
                            runner.zip_test_dir()
                            testcase.context.status = Status.FAILED
                            if abort_on_error:
                                raise ex
                            traceback.print_exc()
                            lh.section("uninstall on error")
                            old_inst.un_install_debug_package()
                            old_inst.un_install_package()
                            old_inst.cleanup_system()
                            try:
                                runner.cleanup()
                            finally:
                                pass
                            continue

                lh.section("uninstall")
                new_inst.un_install_package()
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
                one_result = {
                    "testrun name": testrun_name,
                    "testscenario": runner_strings[runner_type],
                    "success": False,
                    "message": str(ex),
                    "progress": "aborted outside of testcodes",
                }
                if abort_on_error:
                    print("re-throwing.")
                    raise ex
                traceback.print_exc()
                kill_all_processes()
                if runner:
                    try:
                        runner.cleanup()
                    except Exception:
                        print("Ignoring runner cleanup error!")
                try:
                    print("Cleaning up system after error:")
                    old_inst.un_install_debug_package()
                    old_inst.un_install_package()
                    old_inst.cleanup_system()
                except Exception:
                    print("Ignoring old cleanup error!")
                try:
                    print("Ignoring new cleanup error!")
                    new_inst.un_install_debug_package()
                    new_inst.un_install_package()
                    new_inst.cleanup_system()
                except Exception:
                    print("Ignoring new cleanup error!")
            results.append(one_result)
    return results


@click.command()
# pylint: disable=R0913
@very_common_options()
@common_options(support_old=True, interactive=True)
# fmt: off
def main(
        #very_common_options
        new_version, verbose, enterprise, package_dir, zip_package,
        # common_options
        old_version, test_data_dir, encryption_at_rest, interactive,
        starter_mode, stress_upgrade, abort_on_error, publicip,
        selenium, selenium_driver_args, alluredir, clean_alluredir, ssl, use_auto_certs):
    # fmt: on
    """ main trampoline """
    lh.configure_logging(verbose)
    configure_allure(alluredir, clean_alluredir, enterprise, zip_package, new_version, old_version)
    results = run_upgrade(
        old_version,
        new_version,
        verbose,
        package_dir,
        test_data_dir,
        enterprise,
        encryption_at_rest,
        zip_package,
        interactive,
        starter_mode,
        stress_upgrade,
        abort_on_error,
        publicip,
        selenium,
        selenium_driver_args,
        "",
        ssl,
        use_auto_certs,
    )
    print("V" * 80)
    status = True
    for one_result in results:
        print(one_result)
        status = status and one_result["success"]
    if not status:
        print("exiting with failure")
        sys.exit(1)


if __name__ == "__main__":
    # pylint: disable=E1120 # fix clickiness.
    main()
