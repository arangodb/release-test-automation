#!/usr/bin/env python3

""" Release testing script"""
from pathlib import Path
import sys
import click
from tools.killall import kill_all_processes
from arangodb.installers import make_installer, InstallerConfig
from arangodb.starter.deployments import (
    RunnerType,
    make_runner,
    STARTER_MODES
)
import tools.loghelper as lh

@click.command()
@click.option('--old-version', help='unused')
@click.option('--new-version', help='ArangoDB version number.', default="3.8.0-nightly")
@click.option('--verbose/--no-verbose',
              is_flag=True,
              default=False,
              help='switch starter to verbose logging mode.')
@click.option('--enterprise/--no-enterprise',
              is_flag=True,
              default=False,
              help='Enterprise or community?')
@click.option('--encryption-at-rest/--no-encryption-at-rest',
              is_flag=True,
              default=False,
              help='turn on encryption at rest for Enterprise packages')
@click.option('--zip/--no-zip', "zip_package",
              is_flag=True,
              default=False,
              help='switch to zip or tar.gz package instead of default OS package')
@click.option('--interactive/--no-interactive',
              is_flag=True,
              default=sys.stdout.isatty(),
              help='wait for the user to hit Enter?')
@click.option('--package-dir',
              default='/tmp/',
              help='directory to load the packages from.')
@click.option('--test-data-dir',
              default='/tmp/',
              help='directory create databases etc. in.')
@click.option('--mode',
              type=click.Choice(["all", "install", "uninstall", "tests", ]),
              default='all',
              help='operation mode.')
@click.option('--starter-mode',
              default='all',
              type=click.Choice(STARTER_MODES.keys()),
              help='which starter deployments modes to use')
@click.option('--publicip',
              default='127.0.0.1',
              help='IP for the click to browser hints.')
@click.option('--selenium',
              default='none',
              help='if non-interactive chose the selenium target')
@click.option('--selenium-driver-args',
              default=[],
              multiple=True,
              help='options to the selenium web driver')
# pylint: disable=R0913 disable=R0914
def run_test(old_version, new_version, verbose,
             package_dir, test_data_dir,
             enterprise, encryption_at_rest,
             zip_package, interactive, mode,
             starter_mode, publicip,
             selenium, selenium_driver_args):
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
