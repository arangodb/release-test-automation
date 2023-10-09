#!/usr/bin/env python3

"""Release testing script"""
# pylint: disable=duplicate-code
from pathlib import Path
from copy import deepcopy

import click

from arangodb.installers import HotBackupCliCfg, InstallerBaseConfig
from common_options import very_common_options, common_options, hotbackup_options, download_options, test_suite_filtering_options
from download import Download, DownloadOptions
from test_driver import TestDriver


@click.command()
# we ignore some params, since this is a test-only toplevel tool:
# pylint: disable=too-many-arguments disable=too-many-locals
@very_common_options()
@hotbackup_options()
@test_suite_filtering_options()
@common_options(support_old=True, interactive=True)
@common_options(
    support_multi_version=False,
    support_old=True,
    interactive=False,
    test_data_dir="/home/test_dir",
)
@download_options(default_source="ftp:stage2", double_source=True)
def main(**kwargs):
    """main"""
    kwargs["interactive"] = False
    kwargs["abort_on_error"] = False
    kwargs["package_dir"] = Path(kwargs["package_dir"])
    kwargs["test_data_dir"] = Path(kwargs["test_data_dir"])
    kwargs["alluredir"] = Path(kwargs["alluredir"])

    kwargs["hb_cli_cfg"] = HotBackupCliCfg.from_dict(**kwargs)
    kwargs["base_config"] = InstallerBaseConfig.from_dict(**kwargs)
    dl_opts = DownloadOptions.from_dict(**kwargs)
    test_driver = TestDriver(**kwargs)
    fresh_versions = {}
    dl_opt = deepcopy(dl_opts)
    dl_opt.force = dl_opts.force and props.force_dl
    dl_old = Download(
        dl_opt,
        test_driver.base_config.hb_cli_cfg,
        kwargs["old_version"],
        True,
        test_driver.base_config.zip_package,
        test_driver.base_config.src_testing,
        kwargs["old_source"],
        kwargs["old_version"],
        fresh_versions,
        "",
    )
    dl_old.get_packages(dl_old.is_different())
    dl_old = Download(
        dl_opt,
        test_driver.base_config.hb_cli_cfg,
        kwargs["old_version"],
        False,
        test_driver.base_config.zip_package,
        test_driver.base_config.src_testing,
        kwargs["old_source"],
        kwargs["old_version"],
        fresh_versions,
        "",
    )
    dl_old.get_packages(dl_old.is_different())
    dl_new = Download(
        dl_opt,
        test_driver.base_config.hb_cli_cfg,
        kwargs["new_version"],
        True,
        test_driver.base_config.zip_package,
        test_driver.base_config.src_testing,
        kwargs["new_source"],
        kwargs["new_version"],
        fresh_versions,
        "",
    )
    dl_new.get_packages(dl_new.is_different())
    dl_new = Download(
        dl_opt,
        test_driver.base_config.hb_cli_cfg,
        kwargs["new_version"],
        False,
        test_driver.base_config.zip_package,
        test_driver.base_config.src_testing,
        kwargs["new_source"],
        kwargs["new_version"],
        fresh_versions,
        "",
    )
    dl_new.get_packages(dl_new.is_different())
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
            raise Exception("There are failed tests")


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter # fix clickiness.
    main()
