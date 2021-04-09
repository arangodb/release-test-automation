#!/usr/bin/env python3

""" Release testing script"""
from pathlib import Path

import sys
import click

from arangodb.installers import make_installer, InstallerConfig
from arangodb.starter.deployments import RunnerType, make_runner
import tools.loghelper as lh

# pylint: disable=R0913 disable=R0914
def run_upgrade(old_version, new_version, verbose,
                package_dir, test_data_dir,
                enterprise, encryption_at_rest,
                zip_package, interactive,
                starter_mode, stress_upgrade,
                publicip, selenium, selenium_driver_args):
    """ execute upgrade tests """
    lh.configure_logging(verbose)
    lh.section("configuration")
    print("old version: " + str(old_version))
    print("version: " + str(new_version))
    print("using enterpise: " + str(enterprise))
    print("using zip: " + str(zip_package))
    print("package directory: " + str(package_dir))
    print("starter mode: " + str(starter_mode))
    print("public ip: " + str(publicip))
    print("interactive: " + str(interactive))
    print("verbose: " + str(verbose))

    lh.section("startup")

    if starter_mode == 'all':
        starter_mode = [RunnerType.LEADER_FOLLOWER,
                        RunnerType.ACTIVE_FAILOVER,
                        RunnerType.CLUSTER]
        if enterprise:
            starter_mode.append(RunnerType.DC2DC)
    elif starter_mode == 'LF':
        starter_mode = [RunnerType.LEADER_FOLLOWER]
    elif starter_mode == 'AFO':
        starter_mode = [RunnerType.ACTIVE_FAILOVER]
    elif starter_mode == 'CL':
        starter_mode = [RunnerType.CLUSTER]
    elif starter_mode == 'DC':
        if enterprise:
            starter_mode = [RunnerType.DC2DC]
        else:
            starter_mode = [None]
    elif starter_mode == 'none':
        starter_mode = [None]
    else:
        raise Exception("invalid starter mode: " + starter_mode)

    for runner_type in starter_mode:

        install_config_old = InstallerConfig(old_version,
                                             verbose,
                                             enterprise,
                                             encryption_at_rest,
                                             zip_package,
                                             Path(package_dir),
                                             Path(test_data_dir),
                                             'all',
                                             publicip,
                                             interactive,
                                             stress_upgrade)
        old_inst = make_installer(install_config_old)
        install_config_new = InstallerConfig(new_version,
                                             verbose,
                                             enterprise,
                                             encryption_at_rest,
                                             zip_package,
                                             Path(package_dir),
                                             Path(test_data_dir),
                                             'all',
                                             publicip,
                                             interactive,
                                             stress_upgrade)
        new_inst = make_installer(install_config_new)
        install_config_old.add_frontend("http", "127.0.0.1", "8529")
        runner = None
        if runner_type:
            runner = make_runner(runner_type,
                                 selenium,
                                 selenium_driver_args,
                                 install_config_old,
                                 old_inst,
                                 install_config_new,
                                 new_inst)

            if runner:
                runner.run_selenium()


@click.command()
@click.option('--old-version', help='old ArangoDB version number.', default="3.7.0-nightly")
@click.option('--new-version', help='ArangoDB version number.', default="3.8.0-nightly")
@click.option('--verbose/--no-verbose',
              is_flag=True,
              default=False,
              help='switch starter to verbose logging mode.')
@click.option('--package-dir',
              default='/tmp/',
              help='directory to load the packages from.')
@click.option('--test-data-dir',
              default='/tmp/',
              help='directory create databases etc. in.')
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
@click.option('--starter-mode',
              default='all',
              help='which starter environments to start - ' +
              '[all|LF|AFO|CL|DC|none].')
@click.option('--stress-upgrade',
              is_flag=True,
              default=False,
              help='launch arangobench before starting the upgrade')
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
# pylint: disable=R0913
def main(old_version, new_version, verbose,
         package_dir, test_data_dir,
         enterprise, encryption_at_rest,
         zip_package, interactive,
         starter_mode, stress_upgrade, publicip, selenium, selenium_driver_args):
    """ main trampoline """
    return run_upgrade(old_version, new_version, verbose,
                       package_dir, test_data_dir,
                       enterprise, encryption_at_rest,
                       zip_package, interactive,
                       starter_mode, stress_upgrade,
                       publicip, selenium, selenium_driver_args)

if __name__ == "__main__":
# pylint: disable=E1120 # fix clickiness.
    main()
