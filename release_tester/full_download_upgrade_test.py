#!/usr/bin/python3
""" fetch nightly packages, process upgrade """
from pathlib import Path
from copy import copy
import sys

import click
from common_options import very_common_options, common_options, download_options, full_common_options

from beautifultable import BeautifulTable, ALIGN_LEFT

import tools.loghelper as lh
from download import Download, DownloadOptions
from test_driver import TestDriver
from conflict_checking import run_conflict_tests
from tools.killall import list_all_processes

from arangodb.installers import EXECUTION_PLAN

# pylint: disable=R0913 disable=R0914 disable=R0912, disable=R0915
def upgrade_package_test(
    dl_opts: DownloadOptions,
    primary_version: str,
    primary_dlstage: str,
    upgrade_matrix: str,
    other_source,
    git_version,
    editions,
    test_driver
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
        # pylint: disable=W0612
        dl_new = Download(
            dl_opts,
            primary_version,
            props.enterprise,
            test_driver.base_config.zip_package,
            primary_dlstage,
            versions,
            fresh_versions,
            git_version,
        )
        dl_new.get_packages(dl_opts.force)

        this_test_dir = test_dir / props.directory_suffix
        test_driver.reset_test_data_dir(this_test_dir)

        results.append(
            test_driver.run_test(
                "all",
                [dl_new.cfg.version],
                props
            )
        )

    for j in range(len(new_versions)):
        for props in EXECUTION_PLAN:
            print("Cleaning up" + props.testrun_name)
            test_driver.run_cleanup(props)
        print("Cleanup done")

    # Configure Chrome to accept self-signed SSL certs and certs signed by unknown CA.
    # FIXME: Add custom CA to Chrome to properly validate server cert.
    #if props.ssl:
    #    selenium_driver_args += ("ignore-certificate-errors",)

    for props in EXECUTION_PLAN:
        if props.directory_suffix not in editions:
            print("skipping " + props.directory_suffix)
            continue
        # pylint: disable=W0612
        dl_old = Download(
            dl_opts,
            old_versions[j],
            props.enterprise,
            test_driver.base_config.zip_package,
            old_dlstages[j],
            versions,
            fresh_versions,
            git_version,
        )
        dl_new = Download(
            dl_opts,
            new_versions[j],
            props.enterprise,
            test_driver.base_config.zip_package,
            new_dlstages[j],
            versions,
            fresh_versions,
            git_version,
        )
        dl_old.get_packages(dl_opts.force)
        dl_new.get_packages(dl_opts.force)

        this_test_dir = test_dir / props.directory_suffix
        test_driver.reset_test_data_dir(this_test_dir)

        results.append(
            test_driver.run_upgrade(
                [
                    dl_old.cfg.version,
                    dl_new.cfg.version
                ],
                props
            )
        )

    for use_enterprise in [True, False]:
        results.append(
            run_conflict_tests(
                old_version=str(dl_old.cfg.version),
                new_version=str(dl_new.cfg.version),
                verbose=test_driver.base_config.verbose,
                package_dir=test_driver.package_dir,
                alluredir=test_driver.alluredir,
                clean_alluredir=test_driver.clean_alluredir,
                enterprise=use_enterprise,
                zip_package=test_driver.base_config.zip_package,
                interactive=False,
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
    Path("testfailures.txt").write_text(tablestr, encoding='utf8')
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
@common_options(
    support_multi_version=False,
    support_old=False,
    interactive=False,
    test_data_dir="/home/test_dir",
)
@download_options(default_source="ftp:stage2", other_source=True)
# fmt: off
# pylint: disable=R0913, disable=W0613
def main(
        git_version,
        editions,
        upgrade_matrix,
        #very_common_options
        new_version, verbose, enterprise, package_dir, zip_package, hot_backup,
        # common_options
        # old_version,
        test_data_dir, encryption_at_rest, alluredir, clean_alluredir, ssl, use_auto_certs,
        # no-interactive!
        starter_mode, abort_on_error, publicip,
        selenium, selenium_driver_args,
        # download options:
        enterprise_magic, force, source,
        other_source,
        # new_source, old_source,
        httpuser, httppassvoid, remote_host):
# fmt: on
    """ main """
    dl_opts = DownloadOptions(force,
                              verbose,
                              package_dir,
                              enterprise_magic,
                              httpuser,
                              httppassvoid,
                              remote_host)

    test_driver = TestDriver(
        verbose,
        Path(package_dir),
        Path(test_data_dir),
        Path(alluredir),
        clean_alluredir,
        zip_package,
        hot_backup,
        False,  # interactive
        starter_mode,
        False,  # stress_upgrade,
        False,  # abort_on_error
        publicip,
        selenium,
        selenium_driver_args,
        use_auto_certs)

    return upgrade_package_test(
        dl_opts,
        new_version,
        source,
        upgrade_matrix,
        other_source,
        git_version,
        editions,
        test_driver
    )


if __name__ == "__main__":
    # pylint: disable=E1120 # fix clickiness.
    sys.exit(main())
