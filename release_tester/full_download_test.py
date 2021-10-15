#!/usr/bin/python3
""" fetch nightly packages, process upgrade """
from pathlib import Path

import os
import sys

import shutil
import time

import click
from common_options import very_common_options, common_options, download_options

from beautifultable import BeautifulTable, ALIGN_LEFT

import tools.loghelper as lh
from download import read_versions_tar, write_version_tar, Download
from reporting.reporting_utils import AllureTestSuiteContext
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
def package_test(
    verbose,
    new_version,
    package_dir,
    enterprise_magic,
    zip_package,
    new_dlstage,
    git_version,
    httpusername,
    httppassvoid,
    test_data_dir,
    version_state_tar,
    remote_host,
    force,
    starter_mode,
    publicip,
    selenium,
    selenium_driver_args,
    alluredir,
    clean_alluredir,
    ssl,
    use_auto_certs,
):
    """process fetch & tests"""

    set_r_limits()

    lh.configure_logging(verbose)
    list_all_processes()
    os.chdir(test_data_dir)

    versions = {}
    fresh_versions = {}
    read_versions_tar(version_state_tar, versions)
    print(versions)

    results = []
    # do the actual work:
    execution_plan = [
        (True, True, "EE", "Enterprise\nEnc@REST"),
        (True, False, "EP", "Enterprise"),
        (False, False, "C", "Community"),
    ]

    for j in range(len(new_version)):
        for (
            enterprise,
            encryption_at_rest,
            directory_suffix,
            testrun_name,
        ) in execution_plan:
            run_cleanup(zip_package, testrun_name)

        print("Cleanup done")

        for (
            enterprise,
            encryption_at_rest,
            directory_suffix,
            testrun_name,
        ) in execution_plan:
            # pylint: disable=W0612
            with AllureTestSuiteContext(
                alluredir,
                clean_alluredir,
                enterprise,
                zip_package,
                new_version[j],
                None,  # was: old version
                testrun_name,
            ) as suite_context:
                dl_new = Download(
                    new_version[j],
                    verbose,
                    package_dir,
                    enterprise,
                    enterprise_magic,
                    zip_package,
                    new_dlstage[j],
                    httpusername,
                    httppassvoid,
                    remote_host,
                    versions,
                    fresh_versions,
                    git_version,
                )

                if not dl_new.is_different() and not force:
                    print("we already tested this version. bye.")
                    return 0
                dl_new.get_packages(dl_new.is_different())

                test_dir = Path(test_data_dir) / directory_suffix
                if test_dir.exists():
                    shutil.rmtree(test_dir)
                    if "REQUESTS_CA_BUNDLE" in os.environ:
                        del os.environ["REQUESTS_CA_BUNDLE"]
                test_dir.mkdir()
                while not test_dir.exists():
                    time.sleep(1)
                results.append(
                    run_test(
                        "all",
                        str(dl_new.cfg.version),
                        verbose,
                        package_dir,
                        test_dir,
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
                            one_result["message"],
                        ]
                    )
                else:
                    table.rows.append(
                        [
                            one_result["testrun name"],
                            one_result["testscenario"],
                            # one_result['success'],
                            one_result["message"] + "\n" + "H" * 40 + "\n" + one_result["progress"],
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

    if not force:
        write_version_tar(version_state_tar, fresh_versions)


@click.command()
@click.option(
    "--version-state-tar",
    default="/home/release-test-automation/versions.tar",
    help="tar file with the version combination in.",
)
@click.option(
    "--git-version",
    default="",
    help="specify the output of: git rev-parse --verify HEAD",
)
@very_common_options(support_multi_version=True)
@common_options(
    support_multi_version=True,
    support_old=False,
    interactive=False,
    test_data_dir="/home/test_dir",
)
@download_options(default_source="ftp:stage2", double_source=True)
# fmt: off
# pylint: disable=R0913, disable=W0613
def main(
        version_state_tar,
        git_version,
        #very_common_options
        new_version, verbose, enterprise, package_dir, zip_package,
        # common_options,
        # old_version,
        test_data_dir, encryption_at_rest, alluredir, clean_alluredir, ssl, use_auto_certs,
        # no-interactive! VV not used
        starter_mode, #stress_upgrade,
        abort_on_error, publicip,
        selenium, selenium_driver_args,
        # download options:
        enterprise_magic, force, new_source, old_source,
        httpuser, httppassvoid, remote_host):
# fmt: on
    """ main """
    if len(new_source) != len(new_version):
        raise Exception("""
Cannot have different numbers of versions / sources: 
new_version:  {len_new_version} {new_version}
new_source:   {len_new_source} {new_source}
""".format(
                len_new_version=len(new_version),
                new_version=str(new_version),
                len_new_source=len(new_source),
                new_source=str(new_source),
            )
        )

    return package_test(
        verbose,
        workaround_nightly_versioning(new_version),
        package_dir,
        enterprise_magic,
        zip_package,
        new_source,
        git_version,
        httpuser,
        httppassvoid,
        test_data_dir,
        Path(version_state_tar),
        remote_host,
        force,
        starter_mode,
        publicip,
        selenium,
        selenium_driver_args,
        alluredir,
        clean_alluredir,
        ssl,
        use_auto_certs,
    )


if __name__ == "__main__":
    # pylint: disable=E1120 # fix clickiness.
    sys.exit(main())
