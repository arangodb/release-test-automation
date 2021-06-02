#!/usr/bin/env python3

""" Release testing script"""
from pathlib import Path
import sys
import click
from common_options import very_common_options, common_options
from tools.killall import kill_all_processes
from arangodb.installers import create_config_installer_set
from arangodb.starter.deployments import (
    RunnerType,
    make_runner,
    STARTER_MODES
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
             # old_version,
             test_data_dir, encryption_at_rest, interactive, starter_mode,
             # stress_upgrade,
             abort_on_error, publicip, selenium, selenium_driver_args):
    """ main """
    lh.configure_logging(verbose)

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
    for runner_type in STARTER_MODES[starter_mode]:
        if not enterprise and runner_type == RunnerType.DC2DC:
            continue
        runner = make_runner(runner_type, selenium, selenium_driver_args, installers)
        # install on first run:
        runner.do_install = (count == 1) and do_install
        # only uninstall after the last test:
        runner.do_uninstall = (count == len(starter_mode)) and do_uninstall
        failed = False
        try:
            if not runner.run():
                failed = True
        except Exception as ex:
            failed = True
            if abort_on_error:
                raise ex
            print(ex)

        kill_all_processes()
        count += 1

    return 0 if not failed else 1


if __name__ == "__main__":
# pylint: disable=E1120 # fix clickiness.
    sys.exit(run_test())
