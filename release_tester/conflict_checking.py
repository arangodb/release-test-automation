#!/usr/bin/env python3

"""Release testing script"""
from pathlib import Path

import click
import semver

from common_options import very_common_options, common_options
from test_driver import TestDriver



@click.command()
# we ignore some params, since this is a test-only toplevel tool:
# pylint: disable=R0913 disable=too-many-locals
@very_common_options()
@common_options(support_old=True, interactive=True)
# fmt: off
# pylint: disable=unused-argument
def main(
        # very_common_options
        new_version, verbose, enterprise, package_dir, zip_package,
        # common_options
        hot_backup, old_version, test_data_dir, encryption_at_rest, interactive,
        starter_mode, stress_upgrade, abort_on_error, publicip,
        selenium, selenium_driver_args, alluredir, clean_alluredir, ssl, use_auto_certs):
    # fmt: on
    """ main trampoline """
    test_driver = TestDriver(
        verbose,
        Path(package_dir),
        Path(test_data_dir),
        Path(alluredir),
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
        use_auto_certs)
    test_driver.set_r_limits()

    results = test_driver.run_conflict_tests(
        [
            semver.VersionInfo.parse(old_version),
            semver.VersionInfo.parse(new_version)
        ],
        enterprise)
    for result in results:
        if not result["success"]:
            raise Exception("There are failed tests")


if __name__ == "__main__":
    # pylint: disable=E1120 # fix clickiness.
    main()
