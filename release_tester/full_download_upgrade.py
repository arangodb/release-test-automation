#!/usr/bin/python3
""" fetch nightly packages, process upgrade """
import sys

# pylint: disable=duplicate-code
from copy import deepcopy
from pathlib import Path

import click

import tools.loghelper as lh
from arangodb.installers import EXECUTION_PLAN, HotBackupCliCfg, InstallerBaseConfig
from common_options import very_common_options, common_options, download_options, full_common_options, hotbackup_options
from download import (
    get_tar_file_path,
    read_versions_tar,
    write_version_tar,
    touch_all_tars_in_dir,
    Download,
    DownloadOptions,
)
from test_driver import TestDriver
from tools.killall import list_all_processes
from write_result_table import write_table


# pylint: disable=too-many-arguments disable=too-many-locals disable=too-many-branches, disable=too-many-statements
def upgrade_package_test(
    dl_opts: DownloadOptions, new_version, old_version, new_dlstage, old_dlstage, git_version, editions, test_driver
):
    """process fetch & tests"""

    test_driver.set_r_limits()
    lh.configure_logging(test_driver.base_config.verbose)
    list_all_processes()
    test_dir = test_driver.base_config.test_data_dir

    versions = {}
    fresh_versions = {}
    version_state_tar = get_tar_file_path(
        test_driver.launch_dir, [old_version, new_version], test_driver.get_packaging_shorthand()
    )
    read_versions_tar(version_state_tar, versions)
    print(versions)

    results = []
    # do the actual work:
    for props in EXECUTION_PLAN:
        print("Cleaning up" + props.testrun_name)
        test_driver.run_cleanup(props)
    print("Cleanup done")

    versions = []

    for props in EXECUTION_PLAN:
        if props.directory_suffix not in editions:
            continue
        # pylint: disable=unused-variable
        dl_old = Download(
            dl_opts,
            test_driver.base_config.hb_cli_cfg,
            old_version,
            props.enterprise,
            test_driver.base_config.zip_package,
            test_driver.base_config.src_testing,
            old_dlstage,
            versions,
            fresh_versions,
            git_version,
        )
        dl_new = Download(
            dl_opts,
            test_driver.base_config.hb_cli_cfg,
            new_version,
            props.enterprise,
            test_driver.base_config.zip_package,
            test_driver.base_config.src_testing,
            new_dlstage,
            versions,
            fresh_versions,
            git_version,
        )
        if not dl_new.is_different() or not dl_old.is_different():
            print("we already tested this version. bye.")
            return 0
        dl_old.get_packages(dl_old.is_different())
        dl_new.get_packages(dl_new.is_different())

        this_test_dir = test_dir / props.directory_suffix
        test_driver.reset_test_data_dir(this_test_dir)

        results.append(test_driver.run_upgrade([dl_old.cfg.version, dl_new.cfg.version], props))
        versions.append([dl_new.cfg.version, dl_old.cfg.version])
    enterprise_packages_are_present = "EE" in editions or "EP" in editions
    community_packages_are_present = "C" in editions

    params = deepcopy(test_driver.cli_test_suite_params)
    params.new_version = dl_new.cfg.version
    params.old_version = dl_old.cfg.version
    if enterprise_packages_are_present and community_packages_are_present:
        params.enterprise = True
        results.append(
            test_driver.run_test_suites(
                include_suites=("EnterprisePackageInstallationTestSuite",),
                params=params,
            )
        )
        params.enterprise = False
        results.append(
            test_driver.run_test_suites(
                include_suites=("CommunityPackageInstallationTestSuite",),
                params=params,
            )
        )

    if enterprise_packages_are_present:
        params.enterprise = True
        results.append(
            test_driver.run_test_suites(
                include_suites=("DebuggerTestSuite", "BasicLicenseManagerTestSuite", "UpgradeLicenseManagerTestSuite"),
                params=params,
            )
        )

    if community_packages_are_present:
        params.enterprise = False
        results.append(
            test_driver.run_test_suites(
                include_suites=("DebuggerTestSuite",),
                params=params,
            )
        )

    print("V" * 80)
    if not write_table(results):
        print("exiting with failure")
        return 1

    if dl_opts.force:
        touch_all_tars_in_dir(version_state_tar)
    else:
        write_version_tar(version_state_tar, fresh_versions)
    return 0


@click.command()
@click.option(
    "--version-state-tar",
    default="/home/release-test-automation/versions.tar",
    help="tar file with the version combination in.",
)
@full_common_options
@very_common_options()
@hotbackup_options()
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

    test_driver = None
    ret = 1
    try:
        test_driver = TestDriver(**kwargs)
        ret = upgrade_package_test(
            dl_opts,
            kwargs["new_version"],
            kwargs["old_version"],
            kwargs["new_source"],
            kwargs["old_source"],
            kwargs["git_version"],
            kwargs["editions"],
            test_driver,
        )
    finally:
        test_driver.destructor()
    return ret


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter # fix clickiness.
    sys.exit(main())
