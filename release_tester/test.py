#!/usr/bin/env python3

""" Release testing script"""
from pathlib import Path
import traceback

import sys
import click
from allure_commons.model2 import Status, StatusDetails

from common_options import very_common_options, common_options
from reporting.reporting_utils import RtaTestcase, AllureTestSuiteContext
from tools.killall import kill_all_processes
from arangodb.installers import create_config_installer_set
from arangodb.starter.deployments import (
    RunnerType,
    make_runner,
    STARTER_MODES,
    runner_strings,
)
import tools.loghelper as lh

# fmt: off
def run_test(mode,
             new_version,
             verbose,
             package_dir,
             test_data_dir,
             alluredir,
             clean_alluredir,
             enterprise,
             encryption_at_rest,
             zip_package,
             interactive,
             starter_mode,
             abort_on_error,
             publicip,
             selenium,
             selenium_driver_args,
             testrun_name,
             ssl,
             use_auto_certs,
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
        enterprise,
        encryption_at_rest,
        zip_package,
        Path(package_dir),
        Path(test_data_dir),
        mode,
        publicip,
        interactive,
        False,
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
                                    enterprise,
                                    zip_package,
                                    new_version,
                                    encryption_at_rest,
                                    None,
                                    True,
                                    None,
                                    runner_strings[runner_type],
                                    None,
                                    installers[0][1].installer_type,
                                    ssl):
            with RtaTestcase(runner_strings[runner_type] + " main flow") as testcase:
                if not enterprise and runner_type == RunnerType.DC2DC:
                    testcase.context.status = Status.SKIPPED
                    testcase.context.statusDetails = StatusDetails(message="DC2DC is not applicable to Community packages.")
                    continue
                runner = make_runner(
                    runner_type,
                    abort_on_error,
                    selenium,
                    selenium_driver_args,
                    installers,
                    ssl=ssl,
                    use_auto_certs=use_auto_certs,
                )
                # install on first run:
                runner.do_install = (count == 1) and do_install
                # only uninstall after the last test:
                runner.do_uninstall = (count == len(STARTER_MODES[starter_mode])) and do_uninstall
                one_result = {
                    "testrun name": testrun_name,
                    "testscenario": runner_strings[runner_type],
                    "success": True,
                    "messages": [],
                    "progress": "",
                }
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
                    failed_test_names = [f'"{row["Name"]}"' for row in runner.ui_test_results_table if not row["Result"] == "PASSED"]
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
                       enterprise,
                       encryption_at_rest,
                       zip_package,
                       interactive,
                       starter_mode,
                       abort_on_error,
                       publicip,
                       selenium,
                       selenium_driver_args,
                       "",
                       ssl,
                       use_auto_certs)
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
