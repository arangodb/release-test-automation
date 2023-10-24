#!/usr/bin/python3
""" fetch nightly packages, process upgrade """
import sys
from copy import copy, deepcopy

# pylint: disable=duplicate-code
from pathlib import Path

import click

import tools.loghelper as lh
from arangodb.installers import EXECUTION_PLAN, HotBackupCliCfg, make_installer, InstallerBaseConfig, InstallerConfig
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


class DownloadDummy:
    """mimic download class interface for source directory"""

    # pylint: disable=too-many-arguments disable=too-many-instance-attributes disable=unused-argument disable=too-few-public-methods
    def __init__(
        self,
        options: DownloadOptions,
        hb_cli_cfg: HotBackupCliCfg,
        version: str,
        enterprise: bool,
        zip_package: bool,
        src_testing: bool,
        source,
        existing_version_states=None,
        new_version_states=None,
        git_version="",
        force_arch="",
        force_os="",
        arangods=None,
    ):
        """main"""
        if existing_version_states is None:
            existing_version_states = {}
        if new_version_states is None:
            new_version_states = {}
        self.cfg = InstallerConfig(
            version=version,
            verbose=options.verbose,
            enterprise=enterprise,
            encryption_at_rest=False,
            zip_package=zip_package,
            src_testing=src_testing,
            hb_cli_cfg=hb_cli_cfg,
            package_dir=options.package_dir,
            test_dir=Path("/"),
            deployment_mode="all",
            publicip="127.0.0.1",
            interactive=False,
            stress_upgrade=False,
            ssl=False,
            use_auto_certs=False,
            test="",
            arangods=[] if arangods is None else arangods,
        )

        self.inst = make_installer(self.cfg)


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
    map_versions = {}

    # STEP 1: Prepare. Download all required packages for current launch
    for v_sequence in upgrade_matrix.split(";"):
        versions_list = v_sequence.split(":")
        upgrade_scenarios.append(versions_list)
        for version_name in versions_list:
            print(version_name)
            if version_name in packages:
                print("already there" + version_name)
                continue
            ver = {}
            for default_props in EXECUTION_PLAN:
                props = copy(default_props)
                if props.directory_suffix not in editions:
                    continue
                props.testrun_name = "test_" + props.testrun_name
                if version_name == primary_version:
                    print("skipping source package download")
                    ver[props.directory_suffix] = DownloadDummy(
                        dl_opts,
                        test_driver.base_config.hb_cli_cfg,
                        version_name,
                        props.enterprise,
                        False,  # test_driver.base_config.zip_package,
                        True,  # test_driver.base_config.src_testing,
                        source,
                        versions,
                        fresh_versions,
                        git_version,
                    )
                    packages[version_name] = ver
                    continue
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
                new_version_name = str(res.cfg.version)
                if version_name != new_version_name:
                    map_versions[version_name] = new_version_name
                    print(f"mapping {version_name} to {new_version_name}")
                    version_name = new_version_name
                ver[props.directory_suffix] = res
                res.get_packages(dl_opts.force)
                packages[version_name] = res
    params = deepcopy(test_driver.cli_test_suite_params)
    # STEP 2: Run test for primary version
    if run_test:
        print("running tests")
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
            print("launching test")
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
            for i in [0, 1]:
                if scenario[i] in map_versions:
                    print(f"remapping {scenario[i]} to {map_versions[scenario[i]]}!")
                    scenario[i] = map_versions[scenario[i]]
            results.append(test_driver.run_upgrade(scenario, props))

    upgrade_pairs = []
    for scenario in upgrade_scenarios:
        for i in range(len(scenario) - 1):
            old_version = scenario[i]
            new_version = scenario[i + 1]
            if old_version in map_versions:
                print(f"remapping {old_version} to {map_versions[old_version]}!")
                old_version = map_versions[old_version]
            if new_version in map_versions:
                print(f"remapping {new_version} to {map_versions[new_version]}!")
                new_version = map_versions[new_version]
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

    print("V" * 80)
    if not write_table(results):
        print("exiting with failure")
        return 1
    return 0


@click.command()
@full_common_options
@matrix_options(test_default_value=True)
@very_common_options()
@hotbackup_options()
@common_options(
    support_multi_version=False,
    support_old=False,
    interactive=False,
    test_data_dir="/home/test_dir",
    test_suites_default_value=False,
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
    kwargs['zip_package'] = True
    kwargs['src_testing'] = False
    kwargs['base_config'] = InstallerBaseConfig.from_dict(**kwargs)
    kwargs['zip_package'] = False
    kwargs['src_testing'] = True
    kwargs['base_config_src'] = InstallerBaseConfig.from_dict(**kwargs)
    dl_opts = DownloadOptions.from_dict(**kwargs)
    # we run either enterprise or community:
    if len(kwargs['editions']) == 3:
        kwargs['editions'] = ["EP"]

    test_driver = TestDriver(**kwargs)
    try:
        if 'src' not in kwargs['new_version']:
            kwargs['new_version'] = kwargs['new_version'] + '-src'
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
    finally:
        test_driver.destructor()


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter # fix clickiness.
    sys.exit(main())
