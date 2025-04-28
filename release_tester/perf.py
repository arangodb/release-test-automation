#!/usr/bin/env python3

""" Release testing script"""
# pylint: disable=duplicate-code
from pathlib import Path
import sys

import click
import semver

from common_options import very_common_options, common_options, hotbackup_options
from test_driver import TestDriver
from arangodb.hot_backup_cfg import HotBackupCliCfg
from arangodb.installers import RunProperties, InstallerBaseConfig
import reporting.reporting_utils

from write_result_table import write_table


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
@click.option(
    "--scenario",
    default="scenarios/cluster_replicated.yml",
    help="test configuration yaml file, default written & exit if not there.",
)
@click.option("--frontends", multiple=True, help="Connection strings of remote clusters")
@very_common_options()
@hotbackup_options()
@common_options(support_old=False)
def main(**kwargs):
    """main"""
    kwargs["stress_upgrade"] = False
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
        results = test_driver.run_perf_test(
            kwargs["mode"],
            [semver.VersionInfo.parse(kwargs["new_version"])],
            # pylint: disable=too-many-function-args
            kwargs["frontends"],
            kwargs["scenario"],
            "",
            RunProperties(kwargs["enterprise"], kwargs["encryption_at_rest"], kwargs["ssl"]),
        )
        print("V" * 80)
    finally:
        test_driver.destructor()
    print("V" * 80)
    print(results)
    if not write_table([results]):
        print("exiting with failure")
        return 1
    return 0


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter # fix clickiness.
    sys.exit(main())
