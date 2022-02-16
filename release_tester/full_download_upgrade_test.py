#!/usr/bin/python3
""" fetch nightly packages, process upgrade """
from pathlib import Path
from copy import copy
import sys

import click
from common_options import very_common_options, common_options, download_options, full_common_options, hotbackup_options

from beautifultable import BeautifulTable, ALIGN_LEFT

import tools.loghelper as lh
from download import Download, DownloadOptions
from test_driver import TestDriver
from tools.killall import list_all_processes

from arangodb.installers import EXECUTION_PLAN, HotBackupCliCfg, InstallerBaseConfig

# pylint: disable=too-many-arguments disable=too-many-locals disable=too-many-branches, disable=too-many-statements
def upgrade_package_test(
    dl_opts: DownloadOptions,
    primary_version: str,
    primary_dlstage: str,
    upgrade_matrix: str,
    other_source,
    git_version,
    editions,
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
    new_versions = []
    old_versions = []
    old_dlstages = []
    new_dlstages = []

    for version_pair in upgrade_matrix.split(";"):
        print("Adding: '" + version_pair + "'")
        old, new = version_pair.split(":")
        old_versions.append(old)
        new_versions.append(new)
        if old == primary_version:
            old_dlstages.append(primary_dlstage)
            new_dlstages.append(other_source)
        else:
            old_dlstages.append(other_source)
            new_dlstages.append(primary_dlstage)

    for default_props in EXECUTION_PLAN:
        props = copy(default_props)
        props.testrun_name = "test_" + props.testrun_name
        props.directory_suffix = props.directory_suffix + "_t"

        test_driver.run_cleanup(props)
        print("Cleanup done")
        if props.directory_suffix not in editions:
            continue
        # pylint: disable=unused-variable
        dl_new = Download(
            dl_opts,
            test_driver.base_config.hb_cli_cfg,
            primary_version,
            props.enterprise,
            test_driver.base_config.zip_package,
            test_driver.base_config.src_testing,
            primary_dlstage,
            versions,
            fresh_versions,
            git_version,
        )
        dl_new.get_packages(dl_opts.force)

        this_test_dir = test_dir / props.directory_suffix
        test_driver.reset_test_data_dir(this_test_dir)

        results.append(test_driver.run_test("all", [dl_new.cfg.version], props))

    for j in range(len(new_versions)):
        for props in EXECUTION_PLAN:
            print("Cleaning up" + props.testrun_name)
            test_driver.run_cleanup(props)
        print("Cleanup done")

    # Configure Chrome to accept self-signed SSL certs and certs signed by unknown CA.
    # FIXME: Add custom CA to Chrome to properly validate server cert.
    # if props.ssl:
    #    selenium_driver_args += ("ignore-certificate-errors",)

    for props in EXECUTION_PLAN:
        if props.directory_suffix not in editions:
            print("skipping " + props.directory_suffix)
            continue
        # pylint: disable=unused-variable
        dl_old = Download(
            dl_opts,
            test_driver.base_config.hb_cli_cfg,
            old_versions[j],
            props.enterprise,
            test_driver.base_config.zip_package,
            test_driver.base_config.src_testing,
            old_dlstages[j],
            versions,
            fresh_versions,
            git_version,
        )
        dl_new = Download(
            dl_opts,
            test_driver.base_config.hb_cli_cfg,
            new_versions[j],
            props.enterprise,
            test_driver.base_config.zip_package,
            test_driver.base_config.src_testing,
            new_dlstages[j],
            versions,
            fresh_versions,
            git_version,
        )
        dl_old.get_packages(dl_opts.force_dl)
        dl_new.get_packages(dl_opts.force_dl)

        this_test_dir = test_dir / props.directory_suffix
        test_driver.reset_test_data_dir(this_test_dir)

        results.append(test_driver.run_upgrade([dl_old.cfg.version, dl_new.cfg.version], props))

    for use_enterprise in [True, False]:
        results.append(
            test_driver.run_conflict_tests(
                [dl_old.cfg.version, dl_new.cfg.version],
                enterprise=use_enterprise,
            )
        )

    print("V" * 80)
    status = True
    table = BeautifulTable(maxwidth=140)
    for one_suite_result in results:
        if len(one_suite_result) > 0:
            for one_result in one_suite_result:
                if one_result["success"]:
                    table.rows.append(
                        [
                            one_result["testrun name"],
                            one_result["testscenario"],
                            # one_result['success'],
                            "\n".join(one_result["messages"]),
                        ]
                    )
                else:
                    table.rows.append(
                        [
                            one_result["testrun name"],
                            one_result["testscenario"],
                            # one_result['success'],
                            "\n".join(one_result["messages"]) + "\n" + "H" * 40 + "\n" + one_result["progress"],
                        ]
                    )
                status = status and one_result["success"]
    table.columns.header = [
        "Testrun",
        "Test Scenario",
        # 'success', we also have this in message.
        "Message + Progress",
    ]
    table.columns.alignment["Message + Progress"] = ALIGN_LEFT

    tablestr = str(table)
    print(tablestr)
    Path("testfailures.txt").write_text(tablestr, encoding="utf8")
    if not status:
        print("exiting with failure")
        sys.exit(1)

    return 0


@click.command()
@full_common_options
@click.option(
    "--upgrade-matrix", default="", help="list of upgrade operations ala '3.6.15:3.7.15;3.7.14:3.7.15;3.7.15:3.8.1'"
)
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
        test_driver
    )

if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter # fix clickiness.
    sys.exit(main())
