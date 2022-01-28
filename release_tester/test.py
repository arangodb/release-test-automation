#!/usr/bin/env python3

""" Release testing script"""
from pathlib import Path
import sys

import click
import semver

from common_options import very_common_options, common_options
from test_driver import TestDriver
from arangodb.installers import RunProperties


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
         src_testing, hot_backup,
         # common_options
         alluredir, clean_alluredir, ssl, use_auto_certs,
         # old_version,
         test_data_dir, encryption_at_rest, interactive, starter_mode,
         # stress_upgrade,
         abort_on_error, publicip, selenium, selenium_driver_args):
    # fmt: on
    """ main trampoline """
    test_driver = TestDriver(
        verbose,
        Path(package_dir),
        Path(test_data_dir),
        Path(alluredir),
        clean_alluredir,
        zip_package,
        src_testing,
        hot_backup,
        interactive,
        starter_mode,
        False, # stress_upgrade
        abort_on_error,
        publicip,
        selenium,
        selenium_driver_args,
        use_auto_certs)
    test_driver.set_r_limits()
    results = test_driver.run_test(
        mode,
        [semver.VersionInfo.parse(new_version)],
        # pylint: disable=too-many-function-args
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
    sys.exit(main())
