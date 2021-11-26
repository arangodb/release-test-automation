#!/usr/bin/python3
""" fetch nightly packages, process upgrade """
from pathlib import Path

import os
import sys

import shutil
import time

import click
from common_options import very_common_options, common_options, download_options, full_common_options

from beautifultable import BeautifulTable, ALIGN_LEFT

import tools.loghelper as lh
from download import Download
from upgrade import run_upgrade
from conflict_checking import run_conflict_tests
from test import run_test
from cleanup import run_cleanup
from tools.killall import list_all_processes


def set_r_limits():
    """on linux manipulate ulimit values"""
    # pylint: disable=C0415
    import platform

    if not platform.win32_ver()[0]:
        import resource

        resource.setrlimit(resource.RLIMIT_CORE, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))


def workaround_nightly_versioning(ver):
    """adjust package names of nightlies to be semver parseable"""
    # return ver.replace("-nightly", ".9999999-nightly")
    return ver


# pylint: disable=R0913 disable=R0914 disable=R0912, disable=R0915
def upgrade_package_test(
    verbose,
    primary_version,
    primary_dlstage,
    upgrade_matrix,
    package_dir,
    enterprise_magic,
    zip_package,
    other_source,
    git_version,
    httpusername,
    httppassvoid,
    test_data_dir,
    remote_host,
    force,
    starter_mode,
    editions,
    publicip,
    selenium,
    selenium_driver_args,
    alluredir,
    clean_alluredir,
    use_auto_certs,
):
    """process fetch & tests"""

    set_r_limits()
    if not test_data_dir.is_absolute():
        test_data_dir = Path.cwd() / test_data_dir

    lh.configure_logging(verbose)
    list_all_processes()
    os.chdir(test_data_dir)

    versions = {}
    fresh_versions = {}

    results = []
    # do the actual work:
    execution_plan = [
        (True, True, True, "EE", "Enterprise\nEnc@REST"),
        (True, False, False, "EP", "Enterprise"),
        (False, False, False, "C", "Community"),
    ]
    for (
        enterprise,
        encryption_at_rest,
        ssl,
        directory_suffix,
        testrun_name,
    ) in execution_plan:
        run_cleanup(zip_package, "test_" + testrun_name)
        print("Cleanup done")
        if directory_suffix not in editions:
            continue
        # pylint: disable=W0612
        dl_new = Download(
            primary_version,
            verbose,
            package_dir,
            enterprise,
            enterprise_magic,
            zip_package,
            primary_dlstage,
            httpusername,
            httppassvoid,
            remote_host,
            versions,
            fresh_versions,
            git_version,
        )
        dl_new.get_packages(force)
        test_dir = Path(test_data_dir) / (directory_suffix + "_t")
        if test_dir.exists():
            shutil.rmtree(test_dir)
            if "REQUESTS_CA_BUNDLE" in os.environ:
                del os.environ["REQUESTS_CA_BUNDLE"]
        test_dir.mkdir()
        while not test_dir.exists():
            time.sleep(1)
        results.append(
            run_test(
                starter_mode,
                str(dl_new.cfg.version),
                verbose,
                package_dir,
                test_dir,
                alluredir,
                clean_alluredir,
                enterprise,
                encryption_at_rest,
                zip_package,
                False,  # interactive
                starter_mode,
                False,  # abort_on_error
                publicip,
                selenium,
                selenium_driver_args,
                testrun_name,
                ssl,
                use_auto_certs,
            )
        )

    new_versions = []
    old_versions = []
    old_dlstages = []
    new_dlstages = []

    for version_pair in upgrade_matrix.split(";"):
        old, new = version_pair.split(":")
        old_versions.append(old)
        new_versions.append(new)
        if old == primary_version:
            old_dlstages.append(primary_dlstage)
            new_dlstages.append(other_source)
        else:
            old_dlstages.append(other_source)
            new_dlstages.append(primary_dlstage)

    for j in range(len(new_versions)):
        for (enterprise, encryption_at_rest, ssl, directory_suffix, testrun_name) in execution_plan:
            print("Cleaning up" + testrun_name)
            run_cleanup(zip_package, testrun_name)
        print("Cleanup done")

    # Configure Chrome to accept self-signed SSL certs and certs signed by unknown CA.
    # FIXME: Add custom CA to Chrome to properly validate server cert.
    if ssl:
        selenium_driver_args += ("ignore-certificate-errors",)

    for (enterprise, encryption_at_rest, ssl, directory_suffix, testrun_name) in execution_plan:
        if directory_suffix not in editions:
            print("skipping " + directory_suffix)
            continue
        # pylint: disable=W0612
        dl_old = Download(
            old_versions[j],
            verbose,
            package_dir,
            enterprise,
            enterprise_magic,
            zip_package,
            old_dlstages[j],
            httpusername,
            httppassvoid,
            remote_host,
            versions,
            fresh_versions,
            git_version,
        )
        dl_new = Download(
            new_versions[j],
            verbose,
            package_dir,
            enterprise,
            enterprise_magic,
            zip_package,
            new_dlstages[j],
            httpusername,
            httppassvoid,
            remote_host,
            versions,
            fresh_versions,
            git_version,
        )
        dl_old.get_packages(force)
        dl_new.get_packages(force)
        test_dir = Path(test_data_dir) / directory_suffix
        if test_dir.exists():
            shutil.rmtree(test_dir)
            if "REQUESTS_CA_BUNDLE" in os.environ:
                del os.environ["REQUESTS_CA_BUNDLE"]
        test_dir.mkdir(parents=True)
        while not test_dir.exists():
            time.sleep(1)
        results.append(
            run_upgrade(
                str(dl_old.cfg.version),
                str(dl_new.cfg.version),
                verbose,
                package_dir,
                test_dir,
                alluredir,
                clean_alluredir,
                enterprise,
                encryption_at_rest,
                zip_package,
                False,  # interactive_mode
                starter_mode,
                False,  # stress_upgrade,
                False,  # abort_on_error
                publicip,
                selenium,
                selenium_driver_args,
                testrun_name,
                ssl,
                use_auto_certs,
            )
        )

    for enterprise in [True, False]:
        run_conflict_tests(
            old_version=str(dl_old.cfg.version),
            new_version=str(dl_new.cfg.version),
            verbose=verbose,
            package_dir=package_dir,
            alluredir=alluredir,
            clean_alluredir=clean_alluredir,
            enterprise=enterprise,
            zip_package=zip_package,
            interactive=False,
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
    Path("testfailures.txt").write_text(tablestr)
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
        new_version, verbose, enterprise, package_dir, zip_package,
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

    return upgrade_package_test(
        verbose,
        new_version,
        source,
        upgrade_matrix,
        package_dir,
        enterprise_magic,
        zip_package,
        other_source,
        git_version,
        httpuser,
        httppassvoid,
        Path(test_data_dir),
        remote_host,
        force,
        starter_mode,
        editions,
        publicip,
        selenium,
        selenium_driver_args,
        alluredir,
        clean_alluredir,
        use_auto_certs,
    )


if __name__ == "__main__":
    # pylint: disable=E1120 # fix clickiness.
    sys.exit(main())
