#!/usr/bin/env python3

""" Release testing script"""
from pathlib import Path
import platform
import sys
import traceback

import click
import semver
from allure_commons.model2 import Status, StatusDetails

from common_options import very_common_options, common_options
from reporting.reporting_utils import RtaTestcase, AllureTestSuiteContext
from tools.killall import kill_all_processes
from arangodb.installers import create_config_installer_set, RunProperties
from arangodb.starter.deployments import (
    RunnerType,
    make_runner,
    runner_strings,
    STARTER_MODES,
)
import tools.loghelper as lh

is_windows = platform.win32_ver()[0] != ""



@click.command()
# pylint: disable=R0913
@very_common_options()
@common_options(support_old=True, interactive=True)
# fmt: off
def main(
        #very_common_options
        new_version, verbose, enterprise, package_dir, zip_package,
        hot_backup,
        # common_options
        old_version, test_data_dir, encryption_at_rest, interactive,
        starter_mode, stress_upgrade, abort_on_error, publicip,
        selenium, selenium_driver_args, alluredir, clean_alluredir,
        ssl, use_auto_certs):
    # fmt: on
    """ main trampoline """
    lh.configure_logging(verbose)
    results = run_upgrade(
        [
            semver.VersionInfo.parse(old_version),
            semver.VersionInfo.parse(new_version)
        ],
        verbose,
        package_dir,
        test_data_dir,
        alluredir,
        clean_alluredir,
        zip_package,
        hot_backup,
        interactive,
        starter_mode,
        stress_upgrade,
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
    main()
