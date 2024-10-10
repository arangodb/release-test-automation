#!/usr/bin/env python3

"""License manager tests runner script"""
# pylint: disable=duplicate-code
from pathlib import Path

import click

from arangodb.installers import HotBackupCliCfg, InstallerBaseConfig
from common_options import very_common_options, common_options, hotbackup_options
from test_driver import TestDriver
from test_suites_core.cli_test_suite import CliTestSuiteParameters
import reporting.reporting_utils


@click.command()
# pylint: disable=too-many-arguments disable=too-many-locals disable=unused-argument
@very_common_options()
@common_options(support_old=True, interactive=True)
@hotbackup_options()
def main(**kwargs):
    """main"""
    kwargs["interactive"] = False
    kwargs["abort_on_error"] = False
    kwargs["package_dir"] = Path(kwargs["package_dir"])
    kwargs["test_data_dir"] = Path(kwargs["test_data_dir"])
    kwargs["alluredir"] = Path(kwargs["alluredir"])

    kwargs["hb_cli_cfg"] = HotBackupCliCfg.from_dict(**kwargs)
    kwargs["base_config"] = InstallerBaseConfig.from_dict(**kwargs)

    reporting.reporting_utils.init_archive_count_limit(int(kwargs["tarball_count_limit"]))

    test_driver = TestDriver(**kwargs)
    try:
        test_driver.set_r_limits()
        results = test_driver.run_test_suites(
            include_suites=("BasicLicenseManagerTestSuite", "UpgradeLicenseManagerTestSuite"),
            params=CliTestSuiteParameters.from_dict(**kwargs),
        )
        for result in results:
            if not result["success"]:
                raise Exception("There are failed tests")
    finally:
        test_driver.destructor()


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter # fix clickiness.
    main()
