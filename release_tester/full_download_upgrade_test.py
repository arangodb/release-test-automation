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
from acquire_packages import AcquirePackages
from reporting.reporting_utils import AllureTestSuiteContext
from upgrade import run_upgrade
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
    new_version,
    old_version,
    package_dir,
    enterprise_magic,
    zip_package,
    new_dlstage,
    old_dlstage,
    git_version,
    httpusername,
    httppassvoid,
    test_data_dir,
    version_state_dir,
    remote_host,
    force,
    starter_mode,
    stress_upgrade,
    publicip,
    selenium,
    selenium_driver_args,
    alluredir,
    clean_alluredir,
    ssl,
    use_auto_certs,
):
    """process fetch & tests"""
    old_version_state = None
    new_version_state = None
    old_version_content = None
    new_version_content = None

    set_r_limits()

    lh.configure_logging(verbose)
    list_all_processes()
    os.chdir(test_data_dir)

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

        # Configure Chrome to accept self-signed SSL certs and certs signed by unknown CA.
        # FIXME: Add custom CA to Chrome to properly validate server cert.
        if ssl:
            selenium_driver_args += ("ignore-certificate-errors",)

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
                old_version[j],
                testrun_name,
            ) as suite_context:
                dl_old = None
                dl_new = None
                fresh_old_content = None
                fresh_new_content = None
                if old_dlstage[j] != "local":
                    dl_old = AcquirePackages(
                        old_version[j],
                        verbose,
                        package_dir,
                        enterprise,
                        enterprise_magic,
                        zip_package,
                        old_dlstage[j],
                        httpusername,
                        httppassvoid,
                        remote_host,
                    )
                    if old_version[j].find("-nightly") >= 0:
                        old_version_state = version_state_dir / Path(dl_old.cfg.version + "_sourceInfo.log")
                        if old_version_state.exists():
                            old_version_content = old_version_state.read_text()
                        fresh_old_content = dl_old.get_version_info(old_dlstage[j], git_version)

                if new_dlstage[j] != "local":
                    dl_new = AcquirePackages(
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
                    )
                    if new_version[j].find("-nightly") >= 0:
                        new_version_state = version_state_dir / Path(dl_new.cfg.version + "_sourceInfo.log")
                        if new_version_state.exists():
                            new_version_content = new_version_state.read_text()
                        fresh_new_content = dl_new.get_version_info(new_dlstage[j], git_version)

                if new_dlstage[j] != "local" and old_dlstage[j] != "local":
                    old_changed = old_version_content != fresh_old_content
                    new_changed = new_version_content != fresh_new_content

                    if not new_changed and not old_changed and not force:
                        print("we already tested this version. bye.")
                        return 0
                old = old_version[j]
                new = new_version[j]
                if dl_old:
                    dl_old.get_packages(old_changed, old_dlstage[j])
                    old = dl_old.cfg.version
                if dl_new:
                    dl_new.get_packages(new_changed, new_dlstage[j])
                    new = dl_new.cfg.version

                test_dir = Path(test_data_dir) / directory_suffix
                if test_dir.exists():
                    shutil.rmtree(test_dir)
                    if "REQUESTS_CA_BUNDLE" in os.environ:
                        del os.environ["REQUESTS_CA_BUNDLE"]
                test_dir.mkdir()
                while not test_dir.exists():
                    time.sleep(1)
                results.append(
                    run_upgrade(
                        old,
                        new,
                        verbose,
                        package_dir,
                        test_dir,
                        enterprise,
                        encryption_at_rest,
                        zip_package,
                        False, # interactive
                        starter_mode,
                        stress_upgrade,
                        False, # abort on error
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
        old_version_state.write_text(fresh_old_content)
        new_version_state.write_text(fresh_new_content)
    return 0


@click.command()
@click.option(
    "--version-state-dir",
    default="/home/versions",
    help="directory to remember the tested version combination in.",
)
@click.option(
    "--git-version",
    default="",
    help="specify the output of: git rev-parse --verify HEAD",
)
@very_common_options(support_multi_version=True)
@common_options(
    support_multi_version=True,
    support_old=True,
    interactive=False,
    test_data_dir="/home/test_dir",
)
@download_options(default_source="ftp:stage2", double_source=True)
# fmt: off
# pylint: disable=R0913, disable=W0613
def main(
        version_state_dir,
        git_version,
        #very_common_options
        new_version, verbose, enterprise, package_dir, zip_package,
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
    if ((len(new_source) != len(new_version)) or
        (len(old_source) != len(old_version)) or
        (len(old_source) != len(new_source))):
        raise Exception("""
Cannot have different numbers of versions / sources: 
old_version:  {len_old_version} {old_version}
old_source:   {len_old_source} {old_source}
new_version:  {len_new_version} {new_version}
new_source:   {len_new_source} {new_source}
""".format(
                len_old_version=len(old_version),
                old_version=str(old_version),
                len_old_source=len(old_source),
                old_source=str(old_source),
                len_new_version=len(new_version),
                new_version=str(new_version),
                len_new_source=len(new_source),
                new_source=str(new_source),
            )
        )

    return upgrade_package_test(
        verbose,
        workaround_nightly_versioning(new_version),
        workaround_nightly_versioning(old_version),
        package_dir,
        enterprise_magic,
        zip_package,
        new_source,
        old_source,
        git_version,
        httpuser,
        httppassvoid,
        test_data_dir,
        version_state_dir,
        remote_host,
        force,
        starter_mode,
        stress_upgrade,
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
