#!/usr/bin/env python3

""" Release testing script"""
# pylint: disable=duplicate-code
from pathlib import Path
import sys

import click
import semver

from common_options import very_common_options, common_options, hotbackup_options, ui_test_suite_filtering_options
from test_driver import TestDriver
from arangodb.installers import RunProperties, HotBackupCliCfg, InstallerBaseConfig


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
@hotbackup_options()
@common_options(support_old=False)
@ui_test_suite_filtering_options()
def main(**kwargs):
    """main"""
    kwargs["stress_upgrade"] = False
    kwargs["package_dir"] = Path(kwargs["package_dir"])
    kwargs["test_data_dir"] = Path(kwargs["test_data_dir"])
    kwargs["alluredir"] = Path(kwargs["alluredir"])

    kwargs["hb_cli_cfg"] = HotBackupCliCfg.from_dict(**kwargs)
    kwargs["base_config"] = InstallerBaseConfig.from_dict(**kwargs)

    test_driver = TestDriver(**kwargs)
    try:
        test_driver.set_r_limits()
        results = test_driver.run_test(
            kwargs["mode"],
            kwargs["starter_mode"],
            [semver.VersionInfo.parse(kwargs["new_version"])],
            # pylint: disable=too-many-function-args
            RunProperties(
                kwargs["enterprise"],
                True,
                kwargs["encryption_at_rest"],
                kwargs["ssl"],
                kwargs["replication2"],
                kwargs["one_shard"],
            ),
        )
        print("V" * 80)
        status = True
    finally:
        test_driver.destructor()
    for one_result in results:
        print(one_result)
        status = status and one_result["success"]
    if not status:
        print("exiting with failure")
        sys.exit(1)


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter # fix clickiness.
    sys.exit(main())
