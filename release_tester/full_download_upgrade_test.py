#!/usr/bin/python3
""" fetch nightly packages, process upgrade """
import sys
from copy import deepcopy

# pylint: disable=duplicate-code
from pathlib import Path

import click

import tools.loghelper as lh
from arangodb.hot_backup_cfg import HotBackupCliCfg
from arangodb.installers import EXECUTION_PLAN, InstallerBaseConfig
from common_options import (
    very_common_options,
    common_options,
    download_options,
    full_common_options,
    hotbackup_options,
    matrix_options,
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
    primary_version: str,
    primary_dlstage: str,
    upgrade_matrix: str,
    other_source,
    git_version,
    editions,
    run_test,
    run_test_suites,
    test_driver,
    kwargs,
):
    """process fetch & tests"""

    test_driver.set_r_limits()

    lh.configure_logging(test_driver.base_config.verbose)
    list_all_processes()
    test_dir = test_driver.base_config.test_data_dir

    versions = {}
    fresh_versions = {}

    results = []

    upgrade_scenarios = []
    packages = {}

    # STEP 1: Prepare. Download all required packages for current launch
    enterprise_packages_are_present = False
    community_packages_are_present = False
    for v_sequence in upgrade_matrix.split(";"):
        versions_list = v_sequence.split(":")
        upgrade_scenarios.append(versions_list)
        for version_name in versions_list:
            print(version_name)
            if version_name in packages:
                continue
            packages[version_name] = {}
            for default_props in EXECUTION_PLAN:
                props = deepcopy(default_props)
                if props.directory_suffix not in editions:
                    continue
                props.set_kwargs(kwargs)
                dl_opt = deepcopy(dl_opts)
                dl_opt.force = dl_opts.force and props.force_dl
                props.testrun_name = "test_" + props.testrun_name
                # Verify that all required packages are exist or can be downloaded
                source = primary_dlstage if primary_version == version_name else other_source
                res = Download(
                    test_driver.base_config,
                    dl_opt,
                    version_name,
                    props.enterprise,
                    source,
                    versions,
                    fresh_versions,
                    git_version,
                )
                packages[version_name][props.directory_suffix] = res
                res.get_packages(dl_opts.force)
                if props.enterprise:
                    enterprise_packages_are_present = True
                else:
                    community_packages_are_present = True
                # No server package, no install/upgrade tests for these:
                if res.inst.server_package is None:
                    print("skipping server package tests")
                    run_test = False
                    upgrade_scenarios = []

    params = deepcopy(test_driver.cli_test_suite_params)

    # STEP 2: Run test for primary version
    if run_test:
        for default_props in EXECUTION_PLAN:
            if default_props.directory_suffix not in editions:
                continue
            if default_props.only_zip_src and not ( kwargs["zip_package"] or kwargs["src_testing"]):
                print("skipping " + str(default_props))
                continue
            props = deepcopy(default_props)
            props.set_kwargs(kwargs)
            if props.directory_suffix not in editions:
                continue

            if props.is_version_not_supported(packages[primary_version][props.directory_suffix].cfg.version):
                continue

            props.testrun_name = "test_" + props.testrun_name

            test_driver.run_cleanup(props)
            print("Cleanup done")

            this_test_dir = test_dir / props.directory_suffix
            test_driver.reset_test_data_dir(this_test_dir)
            results.append(
                [
                    {
                        "messages": [str(packages[primary_version][props.directory_suffix].cfg.version)],
                        "testrun name": "",
                        "progress": "",
                        "success": True,
                        "testscenario": "",
                    }
                ]
            )
            results.append(
                test_driver.run_test(
                    params.base_cfg.starter_mode,
                    [packages[primary_version][props.directory_suffix].cfg.version],
                    props,
                )
            )

    # STEP 3: Run upgrade tests
    for scenario in upgrade_scenarios:

        for default_props in EXECUTION_PLAN:
            if default_props.only_zip_src and not ( kwargs["zip_package"] or kwargs["src_testing"]):
                print("skipping " + str(default_props))
                continue
            props = deepcopy(default_props)
            props.set_kwargs(kwargs)

            if props.directory_suffix not in editions:
                continue

            skip = False
            for version in scenario:
                if props.is_version_not_supported(version):
                    skip = True
            if skip:
                print(f"Skipping {str(props)}")
                continue
            this_test_dir = test_dir / props.directory_suffix
            print("Cleaning up" + props.testrun_name)
            test_driver.run_cleanup(props)
            test_driver.reset_test_data_dir(this_test_dir)
            print("Cleanup done")
            results.append(
                [
                    {
                        "messages": [" => ".join([str(ver) for ver in scenario])],
                        "testrun name": "",
                        "progress": "",
                        "success": True,
                        "testscenario": "",
                    }
                ]
            )
            results.append(test_driver.run_upgrade(scenario, props))

    upgrade_pairs = []
    for scenario in upgrade_scenarios:
        for i in range(len(scenario) - 1):
            old_version = scenario[i]
            new_version = scenario[i + 1]
            pair = [new_version, old_version]
            if pair not in upgrade_pairs:
                upgrade_pairs.append(pair)

    # STEP 4: Run other test suites
    if run_test_suites:
        for pair in upgrade_pairs:
            params.new_version = pair[0]
            params.old_version = pair[1]

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
                        include_suites=("CommunityPackageInstallationTestSuite",), params=params
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
        return 1
    return 0


@click.command()
@full_common_options
@matrix_options()
@very_common_options()
@hotbackup_options()
@common_options(
    support_multi_version=False,
    support_old=False,
    interactive=False,
    test_data_dir="/home/test_dir",
)
@download_options(default_source="nightlypublic", other_source=True)
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
        return upgrade_package_test(
            dl_opts,
            kwargs['new_version'],
            kwargs['source'],
            kwargs['upgrade_matrix'],
            kwargs['other_source'],
            kwargs['git_version'],
            kwargs['editions'],
            kwargs['run_test'],
            kwargs['run_test_suites'],
            test_driver,
            kwargs
        )
    finally:
        test_driver.destructor()

if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter # fix clickiness.
    sys.exit(main())
