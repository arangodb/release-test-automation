#!/usr/bin/env python3

""" Release testing script"""
from pathlib import Path
import platform
import traceback

import sys
import click
from allure_commons.model2 import Status, StatusDetails

from common_options import very_common_options, common_options
from reporting.reporting_utils import RtaTestcase, AllureTestSuiteContext
from tools.killall import kill_all_processes
from arangodb.installers import create_config_installer_set, RunProperties
from arangodb.starter.deployments import (
    RunnerType,
    make_runner,
    STARTER_MODES,
    runner_strings,
)
import tools.loghelper as lh

WINVER = platform.win32_ver()

# fmt: off
# pylint: disable=R0913 disable=R0914
def run_test(mode,
             new_version,
             verbose,
             package_dir,
             test_data_dir,
             alluredir,
             clean_alluredir,
             zip_package,
             hot_backup,
             interactive,
             starter_mode,
             abort_on_error,
             publicip,
             selenium,
             selenium_driver_args,
             use_auto_certs,
             run_props: RunProperties
):
# fmt: on
    """ main """
    lh.configure_logging(verbose)
    results = []

    do_install = mode in ["all", "install"]
    do_uninstall = mode in ["all", "uninstall"]

    installers = create_config_installer_set(
        [new_version],
        verbose,
        run_props.enterprise,
        run_props.encryption_at_rest,
        zip_package,
        hot_backup,
        Path(package_dir),
        Path(test_data_dir),
        mode,
        publicip,
        interactive,
        False,
        run_props.ssl
    )
    lh.section("configuration")
    print(
        """
    mode: {mode}
    {cfg_repr}
    """.format(
            **{"mode": str(mode), "cfg_repr": repr(installers[0][0])}
        )
    )

    count = 1
    for runner_type in STARTER_MODES[starter_mode]:
        with AllureTestSuiteContext(alluredir,
                                    clean_alluredir,
                                    run_props.enterprise,
                                    zip_package,
                                    new_version,
                                    run_props.encryption_at_rest,
                                    None,
                                    True,
                                    None,
                                    runner_strings[runner_type],
                                    None,
                                    installers[0][1].installer_type,
                                    run_props.ssl):
            with RtaTestcase(runner_strings[runner_type] + " main flow") as testcase:
                if (runner_type == RunnerType.DC2DC and
                    (not run_props.enterprise or WINVER[0] != "")):
                    testcase.context.status = Status.SKIPPED
                    testcase.context.statusDetails = StatusDetails(
                        message="DC2DC is not applicable to Community packages.")
                    continue
                runner = make_runner(
                    runner_type,
                    abort_on_error,
                    selenium,
                    selenium_driver_args,
                    installers,
                    ssl=run_props.ssl,
                    use_auto_certs=use_auto_certs,
                )
                # install on first run:
                runner.do_install = (count == 1) and do_install
                # only uninstall after the last test:
                runner.do_uninstall = (count == len(STARTER_MODES[starter_mode])) and do_uninstall
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
                    if abort_on_error:
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

@click.command()
@click.option(
    "--mode",
    type=click.Choice(
        [
            "all",
            "install",
            "uninstall",
            "tests",
        ]
    ),
    default="all",
    help="operation mode.",
)
@very_common_options()
@common_options(support_old=False)
# pylint: disable=R0913 disable=R0914, disable=W0703
# fmt: off
def main(mode,
         #very_common_options
         new_version, verbose, enterprise, package_dir, zip_package,
         hot_backup,
         # common_options
         alluredir, clean_alluredir, ssl, use_auto_certs,
         # old_version,
         test_data_dir, encryption_at_rest, interactive, starter_mode,
         # stress_upgrade,
         abort_on_error, publicip, selenium, selenium_driver_args):
    # fmt: on
    """ main trampoline """
    lh.configure_logging(verbose)
    results = run_test(mode,
                       new_version,
                       verbose,
                       Path(package_dir),
                       Path(test_data_dir),
                       alluredir,
                       clean_alluredir,
                       zip_package,
                       hot_backup,
                       interactive,
                       starter_mode,
                       abort_on_error,
                       publicip,
                       selenium,
                       selenium_driver_args,
                       use_auto_certs,
                       RunProperties(enterprise,
                                     encryption_at_rest,
                                     ssl))
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
    sys.exit(main())
