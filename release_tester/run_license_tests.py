#!/usr/bin/env python3

"""License manager tests runner script"""
#pylint: disable=duplicate-code
from pathlib import Path

import click

from common_options import very_common_options, common_options, hotbackup_options
from test_driver import TestDriver
from arangodb.installers import HotBackupCliCfg, InstallerBaseConfig


@click.command()
# pylint: disable=too-many-arguments disable=too-many-locals disable=unused-argument
@very_common_options()
@common_options(support_old=True, interactive=True)
@hotbackup_options()
def main(**kwargs):
    """main"""
    kwargs["stress_upgrade"] = False
    kwargs["selenium"] = "none"
    kwargs["selenium_driver_args"] = []
    kwargs["package_dir"] = Path(kwargs["package_dir"])
    kwargs["test_data_dir"] = Path(kwargs["test_data_dir"])
    kwargs["alluredir"] = Path(kwargs["alluredir"])

    kwargs["hb_cli_cfg"] = HotBackupCliCfg.from_dict(**kwargs)
    kwargs["base_config"] = InstallerBaseConfig.from_dict(**kwargs)

    test_driver = TestDriver(**kwargs)
    test_driver.set_r_limits()
    versions = []
    if kwargs["old_version"]:
        versions.append(kwargs["old_version"])
    if kwargs["new_version"]:
        versions.append(kwargs["new_version"])
    results = test_driver.run_license_manager_tests(versions)
    for result in results:
        if not result["success"]:
            raise Exception("There are failed tests")


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter # fix clickiness.
    main()
