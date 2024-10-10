#!/usr/bin/env python3

""" Release testing script"""
# pylint: disable=duplicate-code
from pathlib import Path

import click
from common_options import very_common_options, common_options, ui_test_suite_filtering_options
from arangodb.installers import create_config_installer_set, RunProperties
from arangodb.starter.deployments import RunnerType, make_runner, STARTER_MODES
import tools.loghelper as lh
import reporting.reporting_utils


# pylint: disable=too-many-arguments disable=too-many-locals disable=too-many-locals
def run_upgrade(
    old_version,
    new_version,
    verbose,
    package_dir,
    test_data_dir,
    zip_package,
    hot_backup,
    hb_provider,
    hb_storage_path_prefix,
    interactive,
    starter_mode,
    stress_upgrade,
    abort_on_error,
    publicip,
    selenium,
    selenium_driver_args,
    ui_include_test_suites,
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
            hb_provider,
            hb_storage_path_prefix,
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
            runner = make_runner(
                runner_type,
                abort_on_error,
                selenium,
                selenium_driver_args,
                ui_include_test_suites,
                installers,
                run_props,
            )

            if runner:
                runner.run_selenium()


@click.command()
@very_common_options()
@common_options(support_old=True)
@ui_test_suite_filtering_options()
# fmt: off
# pylint: disable=too-many-arguments disable=unused-argument
def main(
        #very_common_options
        new_version, verbose, enterprise, package_dir, zip_package, src_testing,
        hot_backup, hb_provider, hb_storage_path_prefix,
        hb_aws_access_key_id, hb_aws_secret_access_key, hb_aws_region, hb_aws_acl,
        # common_options
        old_version, test_data_dir, encryption_at_rest, interactive,
        starter_mode, stress_upgrade, abort_on_error, publicip,
        selenium, selenium_driver_args, ui_include_test_suites, ssl, tarball_count_limit):
    """ main trampoline """

    reporting.reporting_utils.init_archive_count_limit(int(tarball_count_limit))

    return run_upgrade(old_version, new_version, verbose,
                       package_dir, test_data_dir,
                       zip_package, hot_backup, hb_provider, hb_storage_path_prefix, interactive,
                       starter_mode, stress_upgrade, abort_on_error,
                       publicip, selenium, selenium_driver_args, ui_include_test_suites,
                       RunProperties(enterprise,
                                     encryption_at_rest,
                                     ssl))
# fmt: on

if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter # fix clickiness.
    main()
