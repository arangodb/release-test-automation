#!/usr/bin/env python3

""" Release testing script"""
from pathlib import Path
import sys
import click
from allure_commons.model2 import Status, Label
from allure_commons.types import LabelType

from common_options import very_common_options, common_options
from reporting.reporting_utils import RtaTestcase, configure_allure
from tools.killall import kill_all_processes
from arangodb.installers import create_config_installer_set
from arangodb.starter.deployments import (
    RunnerType,
    make_runner,
    STARTER_MODES,
    runner_strings
)
import tools.loghelper as lh

@click.command()
@click.option('--mode',
              type=click.Choice(["all", "install", "uninstall", "tests", ]),
              default='all',
              help='operation mode.')
@very_common_options
@common_options(support_old=False)
# pylint: disable=R0913 disable=R0914, disable=W0703
def run_test(mode,
             #very_common_options
             new_version, verbose, enterprise, package_dir, zip_package,
             # common_options
             alluredir, clean_alluredir, ssl,
             # old_version,
             test_data_dir, encryption_at_rest, interactive, starter_mode,
             # stress_upgrade,
             abort_on_error, publicip, selenium, selenium_driver_args):
    """ main """
    lh.configure_logging(verbose)

    configure_allure(alluredir, clean_alluredir, enterprise, zip_package, new_version)

    do_install = mode in ["all", "install"]
    do_uninstall = mode in ["all", "uninstall"]

    installers = create_config_installer_set([new_version],
                                             verbose,
                                             enterprise,
                                             encryption_at_rest,
                                             zip_package,
                                             Path(package_dir),
                                             Path(test_data_dir),
                                             mode,
                                             publicip,
                                             interactive,
                                             False)
    lh.section("configuration")
    print("""
    mode: {mode}
    {cfg_repr}
    """.format(**{
        "mode": str(mode),
        "cfg_repr": repr(installers[0][0])}))

    count = 1
    failed = False
    for runner_type in STARTER_MODES[starter_mode]:
        with RtaTestcase(runner_strings[runner_type]) as testcase:
            if not enterprise and runner_type == RunnerType.DC2DC:
                testcase.context.status = Status.SKIPPED
                continue
            testcase.add_label(Label(name=LabelType.SUB_SUITE,
                                     value=installers[0][1].installer_type))
            runner = make_runner(runner_type,
                                 abort_on_error,
                                 selenium,
                                 selenium_driver_args,
                                 installers,
                                 ssl=ssl)
            # install on first run:
            runner.do_install = (count == 1) and do_install
            # only uninstall after the last test:
            runner.do_uninstall = (count == len(STARTER_MODES[starter_mode])) and do_uninstall
            try:
                if not runner.run():
                    failed = True
                    testcase.context.status = Status.FAILED
            except Exception as ex:
                failed = True
                testcase.context.status = Status.FAILED
                if abort_on_error:
                    raise ex
                print(ex)

            kill_all_processes()
            count += 1

            testcase.context.status = Status.PASSED

    return 0 if not failed else 1


if __name__ == "__main__":
# pylint: disable=E1120 # fix clickiness.
    sys.exit(run_test())
