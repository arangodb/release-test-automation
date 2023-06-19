#!/usr/bin/python3
""" fetch nightly packages, process upgrade """
import sys
from copy import copy, deepcopy

# pylint: disable=duplicate-code
from pathlib import Path

import click

import tools.loghelper as lh
from arangodb.installers import EXECUTION_PLAN, HotBackupCliCfg, InstallerBaseConfig
from common_options import (
    very_common_options,
    common_options,
    download_options,
    full_common_options,
    hotbackup_options,
    matrix_options,
)
from download import Download, DownloadOptions
from test_driver import TestDriver
from tools.killall import list_all_processes
from write_result_table import write_table

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
    for v_sequence in upgrade_matrix.split(";"):
        versions_list = v_sequence.split(":")
        upgrade_scenarios.append(versions_list)
        for version_name in versions_list:
            print(version_name)
            if version_name in packages:
                continue
            packages[version_name] = {}
            for default_props in EXECUTION_PLAN:
                props = copy(default_props)
                if props.directory_suffix not in editions:
                    continue
                props.testrun_name = "test_" + props.testrun_name
                # Verify that all required packages are exist or can be downloaded
                source = primary_dlstage if primary_version == version_name else other_source
                res = Download(
                    dl_opts,
                    test_driver.base_config.hb_cli_cfg,
                    version_name,
                    props.enterprise,
                    test_driver.base_config.zip_package,
                    test_driver.base_config.src_testing,
                    source,
                    versions,
                    fresh_versions,
                    git_version,
                )
                packages[version_name][props.directory_suffix] = res
                res.get_packages(dl_opts.force)

    params = deepcopy(test_driver.cli_test_suite_params)

    # STEP 2: Run test for primary version
    if run_test:
        for default_props in EXECUTION_PLAN:
            if default_props.directory_suffix not in editions:
                continue
            props = copy(default_props)
            if props.directory_suffix not in editions:
                continue

            props.testrun_name = "test_" + props.testrun_name

            test_driver.run_cleanup(props)
            print("Cleanup done")

            this_test_dir = test_dir / props.directory_suffix
            test_driver.reset_test_data_dir(this_test_dir)

            results.append(
                test_driver.run_test(
                    "all",
                    params.base_cfg.starter_mode,
                    [packages[primary_version][props.directory_suffix].cfg.version],
                    props,
                )
            )

    # STEP 3: Run upgrade tests
    for scenario in upgrade_scenarios:

        for props in EXECUTION_PLAN:
            if props.directory_suffix not in editions:
                continue

            this_test_dir = test_dir / props.directory_suffix
            print("Cleaning up" + props.testrun_name)
            test_driver.run_cleanup(props)
            test_driver.reset_test_data_dir(this_test_dir)
            print("Cleanup done")

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
        enterprise_packages_are_present = "EE" in editions or "EP" in editions
        community_packages_are_present = "C" in editions

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
                        ),
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

    test_driver.destructor()
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
@download_options(default_source="ftp:stage2", other_source=True)
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

    kwargs['hb_cli_cfg'] = HotBackupCliCfg.from_dict(**kwargs)
    kwargs['base_config'] = InstallerBaseConfig.from_dict(**kwargs)
    dl_opts = DownloadOptions.from_dict(**kwargs)

    test_driver = TestDriver(**kwargs)

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
        test_driver
    )

if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter # fix clickiness.
    sys.exit(main())
