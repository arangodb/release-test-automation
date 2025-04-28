#!/usr/bin/python3 -u
""" fetch nightly packages, process upgrade """
import sys

# pylint: disable=duplicate-code
from copy import deepcopy
from pathlib import Path
import traceback

import click
import semver

import tools.loghelper as lh
from arangodb.hot_backup_cfg import HotBackupCliCfg
from arangodb.installers import EXECUTION_PLAN, InstallerBaseConfig
from arangodb.instance import dump_instance_registry
from common_options import (
    very_common_options,
    common_options,
    download_options,
    full_common_options,
    hotbackup_options,
    ui_test_suite_filtering_options,
)
from download import Download, DownloadOptions
from test_driver import TestDriver
from tools.killall import list_all_processes
from write_result_table import write_table
import reporting.reporting_utils


# pylint: disable=too-many-arguments disable=too-many-locals disable=too-many-branches, disable=too-many-statements
def upgrade_package_test(
        dl_opts: DownloadOptions,
        new_version,
        old_version,
        new_dlstage,
        old_dlstage,
        git_version,
        editions,
        test_driver,
        kwargs
):
    """process fetch & tests"""

    test_driver.set_r_limits()
    lh.configure_logging(test_driver.base_config.verbose)
    list_all_processes()
    test_dir = test_driver.base_config.test_data_dir

    fresh_versions = {}

    results = []
    # do the actual work:
    for props in EXECUTION_PLAN:
        print("Cleaning up" + props.testrun_name)
        test_driver.run_cleanup(props)
    print("Cleanup done")

    versions = []
    enterprise_packages_are_present = False
    community_packages_are_present = False
    count = 0
    for _props in EXECUTION_PLAN:
        if _props.directory_suffix not in editions:
            continue
        props = deepcopy(_props)
        props.set_kwargs(kwargs)

        count += 1
        # pylint: disable=unused-variable
        dl_opt = deepcopy(dl_opts)
        dl_opt.force = dl_opts.force and props.force_dl
        dl_old = Download(
            test_driver.base_config,
            dl_opt,
            old_version,
            props.enterprise,
            old_dlstage,
            versions,
            fresh_versions,
            git_version,
        )
        dl_new = Download(
            test_driver.base_config,
            dl_opt,
            new_version,
            props.enterprise,
            new_dlstage,
            versions,
            fresh_versions,
            git_version,
        )
        if not dl_new.is_different() or not dl_old.is_different():
            print("we already tested this version. bye.")
            return 0
        try:
            dl_old.get_packages(dl_old.is_different())
            dl_new.get_packages(dl_new.is_different())

            this_test_dir = test_dir / props.directory_suffix
            test_driver.reset_test_data_dir(this_test_dir)
            skip = False
            for version in [new_version, old_version]:
                if semver.VersionInfo.parse(version) < props.minimum_supported_version:
                    skip = True
            if skip:
                print(f"Skipping {str(props)}")
                continue
            results.append(test_driver.run_upgrade([dl_old.cfg.version, dl_new.cfg.version], props))
            versions.append([dl_new.cfg.version, dl_old.cfg.version])
            if props.enterprise:
                enterprise_packages_are_present = True
            else:
                community_packages_are_present = True
        except PermissionError as ex:
            enterprise_packages_are_present = False
            community_packages_are_present = False
            print(f"Failed to download file: {ex} ")
            print("".join(traceback.TracebackException.from_exception(ex).format()))
            results.append(
                [
                    {
                        "messages": [f"Failed to download file: {ex} "],
                        "error": True,
                        "success": False,
                        "testrun name": "",
                        "progress": "",
                        "testscenario": "",
                    }
                ]
            )
    if count == 0:
        raise Exception("Unknown edition specified")
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
                include_suites=(
                    "DebuggerTestSuite",
                    "BasicLicenseManagerTestSuite",
                    "UpgradeLicenseManagerTestSuite",
                    "BinaryComplianceTestSuite",
                ),
                params=params,
            )
        )

    if community_packages_are_present:
        params.enterprise = False
        results.append(
            test_driver.run_test_suites(
                include_suites=(
                    "DebuggerTestSuite",
                    "BinaryComplianceTestSuite",
                ),
                params=params,
            )
        )

    print("V" * 80)
    if not write_table(results):
        print("exiting with failure")
        dump_instance_registry("instances.txt")
        return 1
    dump_instance_registry("instances.txt")

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
@download_options(default_source="nightlypublic", double_source=True)
@ui_test_suite_filtering_options()
def main(**kwargs):
    """main"""
    kwargs["interactive"] = False
    kwargs["abort_on_error"] = False
    kwargs["package_dir"] = Path(kwargs["package_dir"])
    kwargs["test_data_dir"] = Path(kwargs["test_data_dir"])
    kwargs["alluredir"] = Path(kwargs["alluredir"])
    kwargs['is_instrumented'] = False

    kwargs["hb_cli_cfg"] = HotBackupCliCfg.from_dict(**kwargs)
    kwargs["base_config"] = InstallerBaseConfig.from_dict(**kwargs)
    dl_opts = DownloadOptions.from_dict(**kwargs)

    reporting.reporting_utils.init_archive_count_limit(int(kwargs["tarball_count_limit"]))

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
            kwargs
        )
    finally:
        test_driver.destructor()
    return ret


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter # fix clickiness.
    sys.exit(main())
