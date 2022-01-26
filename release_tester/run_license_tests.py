#!/usr/bin/env python3

"""License manager tests runner script"""
from pathlib import Path

import click

from common_options import very_common_options, common_options
from test_driver import TestDriver


@click.command()
# pylint: disable=R0913
# pylint: disable=R0914
@very_common_options()
@common_options(support_old=True, interactive=True)
# fmt: off
def main(
        # very_common_options
        new_version, verbose, enterprise, package_dir, zip_package,
        # common_options
        # pylint: disable=W0613
        hot_backup, old_version, test_data_dir, encryption_at_rest, interactive,
        starter_mode, stress_upgrade, abort_on_error, publicip,
        selenium, selenium_driver_args, alluredir, clean_alluredir, ssl, use_auto_certs):
    # fmt: on
    """ main trampoline """
    test_driver = TestDriver(
        verbose=verbose,
        package_dir=Path(package_dir),
        test_data_dir=Path(test_data_dir),
        alluredir=alluredir,
        clean_alluredir=clean_alluredir,
        zip_package=zip_package,
        hot_backup=hot_backup,
        interactive=interactive,
        starter_mode=starter_mode,
        stress_upgrade=False,
        abort_on_error=abort_on_error,
        publicip=publicip,
        selenium="none",
        selenium_driver_args=[],
        use_auto_certs=use_auto_certs,
    )
    test_driver.set_r_limits()
    results = test_driver.run_license_manager_tests(new_version)
    for result in results:
        if not result["success"]:
            raise Exception("There are failed tests")


if __name__ == "__main__":
    # pylint: disable=E1120 # fix clickiness.
    main()
