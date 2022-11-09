#!/usr/bin/env python3

"""Release testing script"""
# pylint: disable=duplicate-code
from pathlib import Path

import click
import semver

from arangodb.installers import HotBackupCliCfg, InstallerBaseConfig
from common_options import very_common_options, common_options, hotbackup_options
from test_driver import TestDriver


@click.command()
# we ignore some params, since this is a test-only toplevel tool:
# pylint: disable=too-many-arguments disable=too-many-locals
@very_common_options()
@hotbackup_options()
@common_options(support_old=True, interactive=True)
def main(**kwargs):
    """main"""
    kwargs["interactive"] = False
    kwargs["abort_on_error"] = False
    kwargs["package_dir"] = Path(kwargs["package_dir"])
    kwargs["test_data_dir"] = Path(kwargs["test_data_dir"])
    kwargs["alluredir"] = Path(kwargs["alluredir"])

    kwargs["hb_cli_cfg"] = HotBackupCliCfg.from_dict(**kwargs)
    kwargs["base_config"] = InstallerBaseConfig.from_dict(**kwargs)

    test_driver = TestDriver(**kwargs)

    test_driver.set_r_limits()

    results = test_driver.run_conflict_tests(
        [semver.VersionInfo.parse(kwargs["old_version"]), semver.VersionInfo.parse(kwargs["new_version"])],
        kwargs["enterprise"],
    )
    for result in results:
        if not result["success"]:
            raise Exception("There are failed tests")


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter # fix clickiness.
    main()
