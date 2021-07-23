#!/usr/bin/python3
""" fetch nightly packages, process upgrade """
from pathlib import Path

import os
import resource
import sys

import shutil
import time

import click
from common_options import very_common_options, common_options, download_options

from beautifultable import BeautifulTable, ALIGN_LEFT

import tools.loghelper as lh
from acquire_packages import AcquirePackages
from upgrade import run_upgrade
from cleanup import run_cleanup

# pylint: disable=R0913 disable=R0914 disable=R0912, disable=R0915
def upgrade_package_test(verbose,
                         new_version, old_version,
                         package_dir,
                         enterprise_magic,
                         zip_package,
                         new_dlstage, old_dlstage,
                         git_version,
                         httpusername, httppassvoid,
                         test_data_dir, version_state_dir,
                         remote_host, force,
                         starter_mode, stress_upgrade,
                         publicip, selenium, selenium_driver_args,
                         alluredir, clean_alluredir):
    """ process fetch & tests """
    old_version_state = None
    new_version_state = None
    old_version_content = None
    new_version_content = None

    lh.configure_logging(verbose)

    os.chdir(test_data_dir)
    resource.setrlimit(
        resource.RLIMIT_CORE,
        (resource.RLIM_INFINITY, resource.RLIM_INFINITY))

    results = []
    # do the actual work:
    execution_plan = [
        (True, True, 'EE', 'Enterprise\nEnc@REST'),
        (True, False, 'EP', 'Enterprise'),
        (False, False, 'C', 'Community')
    ]

    for enterprise, encryption_at_rest, directory_suffix, testrun_name in execution_plan:
        run_cleanup(zip_package, testrun_name)

    print("Cleanup done")

    for enterprise, encryption_at_rest, directory_suffix, testrun_name in execution_plan:
        dl_old = None
        dl_new = None
        fresh_old_content = None
        fresh_new_content = None
        if old_dlstage != "local":
            dl_old = AcquirePackages(old_version, verbose, package_dir, enterprise,
                                     enterprise_magic, zip_package, old_dlstage,
                                     httpusername, httppassvoid, remote_host)
            old_version_state = version_state_dir / Path(dl_old.cfg.version + "_sourceInfo.log")
            if old_version_state.exists():
                old_version_content = old_version_state.read_text()
            fresh_old_content = dl_old.get_version_info(old_dlstage, git_version)

        if new_dlstage != "local":
            dl_new = AcquirePackages(new_version, verbose, package_dir, enterprise,
                                     enterprise_magic, zip_package, new_dlstage,
                                     httpusername, httppassvoid, remote_host)

            new_version_state = version_state_dir / Path(dl_new.cfg.version + "_sourceInfo.log")
            if new_version_state.exists():
                new_version_content = new_version_state.read_text()
            fresh_new_content = dl_new.get_version_info(new_dlstage, git_version)

        if new_dlstage != "local" and old_dlstage != "local":
            old_changed = old_version_content != fresh_old_content
            new_changed = new_version_content != fresh_new_content

            if not new_changed and not old_changed and not force:
                print("we already tested this version. bye.")
                return 0

        if dl_old:
            dl_old.get_packages(old_changed, old_dlstage)
            old_version = dl_old.cfg.version
        if dl_new:
            dl_new.get_packages(new_changed, new_dlstage)
            new_version = dl_new.cfg.version

        test_dir = Path(test_data_dir) / directory_suffix
        if test_dir.exists():
            shutil.rmtree(test_dir)
        test_dir.mkdir()
        while not test_dir.exists():
            time.sleep(1)
        results.append(
            run_upgrade(old_version,
                        new_version,
                        verbose,
                        package_dir,
                        test_dir,
                        enterprise, encryption_at_rest,
                        zip_package, False,
                        starter_mode, stress_upgrade, False,
                        publicip, selenium, selenium_driver_args,
                        testrun_name, alluredir, clean_alluredir))

    print('V' * 80)
    status = True
    table = BeautifulTable(maxwidth=140)
    for one_suite_result in results:
        if len(one_suite_result) > 0:
            for one_result in one_suite_result:
                if one_result['success']:
                    table.rows.append([
                        one_result['testrun name'],
                        one_result['testscenario'],
                        # one_result['success'],
                        one_result['message']
                    ])
                else:
                    table.rows.append([
                        one_result['testrun name'],
                        one_result['testscenario'],
                        # one_result['success'],
                        one_result['message'] +
                        '\n' + 'H' * 40 + '\n' +
                        one_result['progress']
                    ])
                status = status and one_result['success']
    table.columns.header = [
        'Testrun',
        'Test Scenario',
        # 'success', we also have this in message.
        'Message + Progress']
    table.columns.alignment['Message + Progress'] = ALIGN_LEFT

    tablestr = str(table)
    print(tablestr)
    Path('testfailures.txt').write_text(tablestr)
    if not status:
        print('exiting with failure')
        sys.exit(1)

    if not force:
        old_version_state.write_text(fresh_old_content)
        new_version_state.write_text(fresh_new_content)
    return 0

@click.command()
@click.option('--version-state-dir',
              default='/home/versions',
              help='directory to remember the tested version combination in.')
@click.option('--git-version',
              default='',
              help='specify the output of: git rev-parse --verify HEAD')
@very_common_options
@common_options(support_old=True, interactive=False, test_data_dir='/home/test_dir')
@download_options(default_source="ftp:stage2", double_source=True)
# pylint: disable=R0913, disable=W0613
def main(
        version_state_dir,
        git_version,
        #very_common_options
        new_version, verbose, enterprise, package_dir, zip_package,
        # common_options
        old_version, test_data_dir, encryption_at_rest, alluredir, clean_alluredir,
        # no-interactive!
        starter_mode, stress_upgrade, abort_on_error, publicip,
        selenium, selenium_driver_args,
        # download options:
        enterprise_magic, force, new_source, old_source,
        httpuser, httppassvoid, remote_host):
    """ main """
    return upgrade_package_test(verbose,
                                new_version, old_version,
                                package_dir, enterprise_magic,
                                zip_package,
                                new_source, old_source,
                                git_version,
                                httpuser, httppassvoid,
                                test_data_dir,
                                version_state_dir,
                                remote_host, force,
                                starter_mode, stress_upgrade,
                                publicip, selenium, selenium_driver_args,
                                alluredir, clean_alluredir)

if __name__ == "__main__":
# pylint: disable=E1120 # fix clickiness.
    sys.exit(main())
