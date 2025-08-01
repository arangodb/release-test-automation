#!/usr/bin/python3
""" fetch nightly packages, process upgrade """
# pylint: disable=duplicate-code
from copy import deepcopy
from pathlib import Path
import sys

import click

import reporting.reporting_utils
from common_options import (
    very_common_options,
    common_options,
    download_options,
    full_common_options,
    hotbackup_options,
    ui_test_suite_filtering_options,
)

from write_result_table import write_table

import tools.loghelper as lh
from download import Download, DownloadOptions

from test_driver import TestDriver
from tools.killall import list_all_processes

from arangodb.hot_backup_cfg import HotBackupCliCfg
from arangodb.installers import EXECUTION_PLAN, InstallerBaseConfig


# pylint: disable=too-many-arguments disable=too-many-locals disable=too-many-branches, disable=too-many-statements
def package_test(
    dl_opts: DownloadOptions, new_version, new_dlstage, git_version, editions, run_test_suites, test_driver, kwargs
):
    """process fetch & tests"""

    test_driver.set_r_limits()

    lh.configure_logging(test_driver.base_config.verbose)
    list_all_processes()
    test_dir = test_driver.base_config.test_data_dir

    fresh_versions = {}
    versions = {}
    results = []
    # do the actual work:
    for props in EXECUTION_PLAN:
        test_driver.run_cleanup(props)

    print("Cleanup done")

    # pylint: disable=fixme
    # FIXME: replication2 parameter must be passed from CLI to the runner class
    # in every entrypoint script without need for manual fixes like this one
    enterprise_packages_are_present = False
    community_packages_are_present = False
    for init_props in EXECUTION_PLAN:
        props = deepcopy(init_props)
        if props.directory_suffix not in editions:
            continue
        if props.is_version_not_supported(new_version):
            print(f"skipping {repr(props)}")
            continue
        props.set_kwargs(kwargs)
        dl_opt = deepcopy(dl_opts)
        dl_opt.force = dl_opts.force and props.force_dl
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

        if not dl_new.is_different() and not dl_opts.force:
            print("we already tested this version. bye.")
            sys.exit(0)
        dl_new.get_packages(dl_new.is_different())
        if props.enterprise:
            enterprise_packages_are_present = True
        else:
            community_packages_are_present = True
        this_test_dir = test_dir / props.directory_suffix
        test_driver.reset_test_data_dir(this_test_dir)
        results.append(
            [
                {
                    "messages": [str(dl_new.cfg.version)],
                    "testrun name": "",
                    "progress": "",
                    "success": True,
                    "testscenario": "",
                }
            ]
        )
        results.append(test_driver.run_test("all", [dl_new.cfg.version], props))

    if dl_new is None:
        print("no suites found")
        return 1

    if run_test_suites:
        results.append(
            [
                {
                    "messages": ["Testsuites:"],
                    "error": False,
                    "success": True,
                    "testrun name": "",
                    "progress": "",
                    "testscenario": "",
                }
            ]
        )
        params = deepcopy(test_driver.cli_test_suite_params)
        params.new_version = dl_new.cfg.version
        if enterprise_packages_are_present:
            params.enterprise = True
            results.append(
                test_driver.run_test_suites(
                    include_suites=(
                        "DebuggerTestSuite",
                        "BasicLicenseManagerTestSuite",
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
        return 1
    return 0


@click.command()
@full_common_options
@very_common_options()
@hotbackup_options()
@common_options(
    support_old=False,
    interactive=False,
    test_data_dir="/home/test_dir",
)
@download_options(default_source="nightlypublic", double_source=True)
@ui_test_suite_filtering_options()
# fmt: off
# pylint: disable=too-many-arguments, disable=unused-argument
def main(**kwargs):
    """ main """
    kwargs['interactive'] = False
    kwargs['abort_on_error'] = False
    kwargs['stress_upgrade'] = False
    kwargs['package_dir'] = Path(kwargs['package_dir'])
    kwargs['test_data_dir'] = Path(kwargs['test_data_dir'])
    kwargs['alluredir'] = Path(kwargs['alluredir'])
    kwargs['is_instrumented'] = False

    kwargs['hb_cli_cfg'] = HotBackupCliCfg.from_dict(**kwargs)
    kwargs['base_config'] = InstallerBaseConfig.from_dict(**kwargs)
    dl_opts = DownloadOptions.from_dict(**kwargs)

    reporting.reporting_utils.init_archive_count_limit(int(kwargs["tarball_count_limit"]))

    test_driver = TestDriver(**kwargs)
    try:
        return package_test(
            dl_opts,
            kwargs['new_version'],
            kwargs['new_source'],
            kwargs['git_version'],
            kwargs['editions'],
            kwargs['run_test_suites'],
            test_driver,
            kwargs
        )
    finally:
        test_driver.destructor()

if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter # fix clickiness.
    sys.exit(main())
