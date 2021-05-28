#!/usr/bin/env python3

""" Release testing script"""
from pathlib import Path
import sys
import click
from common_options import very_common_options, common_options
from tools.killall import kill_all_processes
from arangodb.installers import make_installer, InstallerConfig
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
@common_options(support_old=True)
# pylint: disable=R0913 disable=R0914
def run_test(mode,
             #very_common_options
             new_version,
             verbose,
             enterprise,
             package_dir,
             zip_package,
             # common_options
             old_version,
             test_data_dir,
             encryption_at_rest,
             interactive,
             starter_mode,
             stress_upgrade,
             abort_on_error,
             publicip,
             selenium,
             selenium_driver_args):
    """ main """
    lh.configure_logging(verbose)
    lh.section("configuration")
    print("version: " + str(new_version))
    print("using enterpise: " + str(enterprise))
    print("using encryption at rest: " + str(encryption_at_rest))
    print("using zip: " + str(zip_package))
    print("package directory: " + str(package_dir))
    print("mode: " + str(mode))
    print("starter mode: " + str(starter_mode))
    print("public ip: " + str(publicip))
    print("interactive: " + str(interactive))
    print("verbose: " + str(verbose))

    do_install = mode in ["all", "install"]
    do_uninstall = mode in ["all", "uninstall"]

    install_config = InstallerConfig(new_version,
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

    inst = make_installer(install_config)

    count = 1
    for runner_type in STARTER_MODES[starter_mode]:
        if not enterprise and runner_type == RunnerType.DC2DC:
            continue
        runner = make_runner(runner_type, selenium, selenium_driver_args, inst.cfg, inst, None)
        # install on first run:
        runner.do_install = (count == 1) and do_install
        # only uninstall after the last test:
        runner.do_uninstall = (count == len(starter_mode)) and do_uninstall
        failed = False
        if not runner.run():
            failed = True

        kill_all_processes()
        count += 1

    return 0 if not failed else 1


if __name__ == "__main__":
# pylint: disable=E1120 # fix clickiness.
    sys.exit(run_test())
