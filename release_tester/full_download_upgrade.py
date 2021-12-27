#!/usr/bin/python3
""" fetch nightly packages, process upgrade """
from pathlib import Path
import sys

import click
from common_options import very_common_options, common_options, download_options, full_common_options

from beautifultable import BeautifulTable, ALIGN_LEFT

import tools.loghelper as lh
from download import (
    get_tar_file_path,
    read_versions_tar,
    write_version_tar,
    touch_all_tars_in_dir,
    Download,
    DownloadOptions)
from test_driver import TestDriver
from tools.killall import list_all_processes

from arangodb.installers import EXECUTION_PLAN

# pylint: disable=R0913 disable=R0914 disable=R0912, disable=R0915
def upgrade_package_test(
    dl_opts: DownloadOptions,
    new_version,
    old_version,
    new_dlstage,
    old_dlstage,
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
    version_state_tar = get_tar_file_path(test_driver.launch_dir,
                                          [old_version, new_version],
                                          test_driver.get_packaging_shorthand())
    read_versions_tar(version_state_tar, versions)
    print(versions)

    results = []
    # do the actual work:
    for props in EXECUTION_PLAN:
        print("Cleaning up" + props.testrun_name)
        test_driver.run_cleanup(props)
    print("Cleanup done")

    for props in EXECUTION_PLAN:
        if props.directory_suffix not in editions:
            continue
        # pylint: disable=W0612
        dl_old = Download(
            dl_opts,
            old_version,
            props.enterprise,
            test_driver.base_config.zip_package,
            old_dlstage,
            versions,
            fresh_versions,
            git_version,
        )
        dl_new = Download(
            dl_opts,
            new_version,
            props.enterprise,
            test_driver.base_config.zip_package,
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
            test_driver.run_conflict_tests(
                [
                    dl_old.cfg.version,
                    dl_new.cfg.version
                ],
                enterprise=use_enterprise,
            )
        )

    results.append(
        test_driver.run_license_manager_tests(dl_new.cfg.version)
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

    if dl_opts.force_dl:
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
@common_options(
    support_multi_version=False,
    support_old=True,
    interactive=False,
    test_data_dir="/home/test_dir",
)
@download_options(default_source="ftp:stage2", double_source=True)
# fmt: off
# pylint: disable=R0913, disable=W0613
def main(
        version_state_tar,
        git_version,
        editions,
        #very_common_options
        new_version, verbose, enterprise, package_dir, zip_package, hot_backup,
        # common_options
        old_version, test_data_dir, encryption_at_rest, alluredir, clean_alluredir, ssl, use_auto_certs,
        # no-interactive!
        starter_mode, stress_upgrade, abort_on_error, publicip,
        selenium, selenium_driver_args,
        # download options:
        enterprise_magic, force, new_source, old_source,
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
        stress_upgrade,
        False,  # abort_on_error
        publicip,
        selenium,
        selenium_driver_args,
        use_auto_certs)

    return upgrade_package_test(
        dl_opts,
        new_version,
        old_version,
        new_source,
        old_source,
        git_version,
        editions,
        test_driver
    )


if __name__ == "__main__":
    # pylint: disable=E1120 # fix clickiness.
    sys.exit(main())
