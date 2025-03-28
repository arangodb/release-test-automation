#!/usr/bin/env python3

"""Release testing script"""
# pylint: disable=duplicate-code
from pathlib import Path

import click

from arangodb.hot_backup_cfg import HotBackupCliCfg
from arangodb.installers import InstallerBaseConfig
from common_options import (
    very_common_options,
    common_options,
    hotbackup_options,
    test_suite_filtering_options,
    ui_test_suite_filtering_options,
)
from test_driver import TestDriver
import reporting.reporting_utils


@click.command()
# we ignore some params, since this is a test-only toplevel tool:
# pylint: disable=too-many-arguments disable=too-many-locals
@very_common_options()
@hotbackup_options()
@test_suite_filtering_options()
@ui_test_suite_filtering_options()
@common_options(support_old=True, interactive=True)
def main(**kwargs):
    """main"""
    kwargs["interactive"] = False
    kwargs["abort_on_error"] = False
    kwargs["monitoring"] = False
    kwargs["package_dir"] = Path(kwargs["package_dir"])
    kwargs["test_data_dir"] = Path(kwargs["test_data_dir"])
    kwargs["alluredir"] = Path(kwargs["alluredir"])
    kwargs['is_instrumented'] = False

    kwargs["hb_cli_cfg"] = HotBackupCliCfg.from_dict(**kwargs)
    kwargs["base_config"] = InstallerBaseConfig.from_dict(**kwargs)

    reporting.reporting_utils.init_archive_count_limit(int(kwargs["tarball_count_limit"]))

    test_driver = TestDriver(**kwargs)
    try:
        test_driver.set_r_limits()

        results = test_driver.run_test_suites(
            include_suites=kwargs["include_test_suites"],
            exclude_suites=kwargs["exclude_test_suites"],
        )
    finally:
        test_driver.destructor()
    for result in results:
        if not result["success"]:
            raise Exception("There are failed or broken tests")


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter # fix clickiness.
    main()
