#!/usr/bin/env python3

""" Release testing script"""
# pylint: disable=duplicate-code
from pathlib import Path
import sys

import click
import semver

from common_options import very_common_options, common_options, hotbackup_options
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

    kwargs["hb_cli_cfg"] = HotBackupCliCfg.from_dict(**kwargs)
    kwargs["base_config"] = InstallerBaseConfig.from_dict(**kwargs)

    test_driver = TestDriver(**kwargs)

    test_driver.set_r_limits()
    results = test_driver.run_perf_test(
        kwargs["mode"],
        [semver.VersionInfo.parse(kwargs["new_version"])],
        # pylint: disable=too-many-function-args
        kwargs['frontends'],
        kwargs['scenario'],
        RunProperties(kwargs['enterprise'],
                      kwargs['encryption_at_rest'],
                      kwargs['ssl']))
    print("V" * 80)
    status = True
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
