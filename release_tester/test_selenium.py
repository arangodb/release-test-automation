#!/usr/bin/env python3

""" Release testing script"""
from pathlib import Path

import click
from common_options import very_common_options, common_options
from arangodb.installers import create_config_installer_set, RunProperties
from arangodb.starter.deployments import RunnerType, make_runner, STARTER_MODES
import tools.loghelper as lh

# pylint: disable=too-many-arguments disable=too-many-locals disable=too-many-locals
def run_upgrade(
    old_version,
    new_version,
    verbose,
    package_dir,
    test_data_dir,
    zip_package,
    hot_backup,
    interactive,
    starter_mode,
    stress_upgrade,
    abort_on_error,
    publicip,
    selenium,
    selenium_driver_args,
    run_props: RunProperties,
):
    """execute upgrade tests"""
    lh.configure_logging(verbose)

    lh.section("startup")

    for runner_type in STARTER_MODES[starter_mode]:
        if not run_props.enterprise and runner_type == RunnerType.DC2DC:
            continue
        # pylint: disable=too-many-function-args
        installers = create_config_installer_set(
            [old_version, new_version],
            verbose,
            zip_package,
            hot_backup,
            Path(package_dir),
            Path(test_data_dir),
            "all",  # deployment_mode
            publicip,
            interactive,
            stress_upgrade,
            run_props,
        )
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
        runner = None
        installers[0][0].add_frontend("http", "127.0.0.1", "8529")
        runner = None
        if runner_type:
            runner = make_runner(runner_type, abort_on_error, selenium, selenium_driver_args, installers, run_props)

            if runner:
                runner.run_selenium()


@click.command()
@very_common_options()
@common_options(support_old=True)
# fmt: off
# pylint: disable=too-many-arguments disable=unused-argument
def main(
        #very_common_options
        new_version, verbose, enterprise, package_dir, zip_package, hot_backup,
        # common_options
        old_version, test_data_dir, encryption_at_rest, interactive,
        starter_mode, stress_upgrade, abort_on_error, publicip,
        selenium, selenium_driver_args, ssl):
    """ main trampoline """
    return run_upgrade(old_version, new_version, verbose,
                       package_dir, test_data_dir,
                       zip_package, hot_backup, interactive,
                       starter_mode, stress_upgrade, abort_on_error,
                       publicip, selenium, selenium_driver_args,
                       RunProperties(enterprise,
                                     encryption_at_rest,
                                     ssl))
# fmt: on

if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter # fix clickiness.
    main()
