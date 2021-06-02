#!/usr/bin/env python3

""" Release testing script"""
from pathlib import Path

import click
from common_options import very_common_options, common_options
from arangodb.installers import create_config_installer_set
from arangodb.starter.deployments import (
    RunnerType,
    make_runner,
    STARTER_MODES
)
import tools.loghelper as lh

# pylint: disable=R0913 disable=R0914 disable=R0914
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

    for runner_type in STARTER_MODES[starter_mode]:
        if not enterprise and runner_type == RunnerType.DC2DC:
            continue
        installers = create_config_installer_set([old_version, new_version],
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
        runner = None
        installers[0][0].add_frontend("http", "127.0.0.1", "8529")
        runner = None
        if runner_type:
            runner = make_runner(runner_type,
                                 selenium,
                                 selenium_driver_args,
                                 installers)

            if runner:
                runner.run_selenium()


@click.command()
@very_common_options
@common_options(support_old=True)
# pylint: disable=R0913 disable=W0613
def main(
        #very_common_options
        new_version, verbose, enterprise, package_dir, zip_package,
        # common_options
        old_version, test_data_dir, encryption_at_rest, interactive,
        starter_mode, stress_upgrade, abort_on_error, publicip,
        selenium, selenium_driver_args):
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
