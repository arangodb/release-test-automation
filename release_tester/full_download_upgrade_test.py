#!/usr/bin/python3
""" fetch nightly packages, process upgrade """
from pathlib import Path

import os
import sys
import click
from acquire_packages import AcquirePackages
from upgrade import run_upgrade
import resource

# pylint: disable=R0913 disable=R0914
def upgrade_package_test(verbose,
                         new_version, old_version,
                         package_dir,
                         enterprise_magic,
                         zip_package,
                         dlstage, git_version,
                         httpusername, httppassvoid,
                         test_data_dir, version_state_dir,
                         remote_host, force,
                         starter_mode, stress_upgrade,
                         publicip, selenium, selenium_driver_args):
    """ process fetch & tests """
    old_version_state = None
    new_version_state = None
    old_version_content = None
    new_version_content = None

    os.chdir(test_data_dir)
    resource.setrlimit(
        resource.RLIMIT_CORE,
        (resource.RLIM_INFINITY, resource.RLIM_INFINITY))

    for enterprise, encryption_at_rest in [(True, True),
                                           (True, False),
                                           (False, False)]:
        dl_old = AcquirePackages(old_version, verbose, package_dir, enterprise,
                                 enterprise_magic, zip_package, dlstage,
                                 httpusername, httppassvoid, remote_host)
        dl_new = AcquirePackages(new_version, verbose, package_dir, enterprise,
                                 enterprise_magic, zip_package, dlstage,
                                 httpusername, httppassvoid, remote_host)
        old_version_state = version_state_dir / Path(dl_old.cfg.version + "_sourceInfo.log")
        new_version_state = version_state_dir / Path(dl_new.cfg.version + "_sourceInfo.log")
        if old_version_state.exists():
            old_version_content = old_version_state.read_text()
        if new_version_state.exists():
            new_version_content = new_version_state.read_text()

        fresh_old_content = dl_old.get_version_info(dlstage, git_version)
        fresh_new_content = dl_new.get_version_info(dlstage, git_version)
        old_changed = old_version_content != fresh_old_content
        new_changed = new_version_content != fresh_new_content
        if new_changed and old_changed and not force:
            print("we already tested this version. bye.")
            return 0

        dl_old.get_packages(old_changed, dlstage)
        dl_new.get_packages(new_changed, dlstage)
        run_upgrade(dl_old.cfg.version,
                    dl_new.cfg.version,
                    verbose,
                    package_dir, test_data_dir,
                    enterprise, encryption_at_rest,
                    zip_package, False,
                    starter_mode, stress_upgrade,
                    publicip, selenium, selenium_driver_args)

    if not force:
        old_version_state.write_text(fresh_old_content)
        new_version_state.write_text(fresh_new_content)
    return 0

@click.command()
@click.option('--verbose/--no-verbose',
              is_flag=True,
              default=True,
              help='switch starter to verbose logging mode.')
@click.option('--new-version', help='ArangoDB version number.', default="3.8.0-nightly")
@click.option('--old-version', help='old ArangoDB version number.', default="3.7.7-nightly")
@click.option('--enterprise-magic',
              default='',
              help='Enterprise or community?')
@click.option('--zip/--no-zip', 'zip_package',
              is_flag=True,
              default=True,
              help='switch to zip or tar.gz package instead of default OS package')
@click.option('--package-dir',
              default='/home/package_cache/',
              help='directory to store the packages to.')
@click.option('--source',
              default='ftp:stage2',
              help='where to download the package from '
              '[[ftp|http]:stage1|[ftp|http]:stage2|public]')
@click.option('--httpuser',
              default="",
              help='user for external http download')
@click.option('--httppassvoid',
              default="",
              help='passvoid for external http download')
@click.option('--test-data-dir',
              default='/home/test_dir',
              help='directory create databases etc. in.')
@click.option('--version-state-dir',
              default='/home/versions',
              help='directory to remember the tested version combination in.')
@click.option('--git-version',
              default='',
              help='specify the output of: git rev-parse --verify HEAD')
@click.option('--remote-host',
              default="",
              help='remote host to acquire packages from')
@click.option('--force/--no-force',
              is_flag=True,
              default=False,
              help='whether to overwrite existing target files or not.')
@click.option('--starter-mode',
              default='all',
              help='which starter environments to start - ' +
              '[all|LF|AFO|CL|DC|none].')
@click.option('--stress-upgrade',
              is_flag=True,
              default=False,
              help='launch arangobench before starting the upgrade')
@click.option('--publicip',
              default='127.0.0.1',
              help='IP for the click to browser hints.')
@click.option('--selenium',
              default='Chrome',
              help='if non-interactive chose the selenium target')
@click.option('--selenium-driver-args',
              default=['headless'],
              multiple=True,
              help='options to the selenium web driver')
# pylint: disable=R0913
def main(verbose,
         new_version, old_version,
         package_dir, enterprise_magic,
         zip_package, source,
         httpuser, httppassvoid,
         test_data_dir, git_version,
         version_state_dir, remote_host,
         force, starter_mode, stress_upgrade,
         publicip, selenium, selenium_driver_args):
    """ main """
    return upgrade_package_test(verbose,
                                new_version, old_version,
                                package_dir, enterprise_magic,
                                zip_package, source, git_version,
                                httpuser, httppassvoid,
                                test_data_dir,
                                version_state_dir,
                                remote_host, force,
                                starter_mode, stress_upgrade,
                                publicip, selenium, selenium_driver_args)

if __name__ == "__main__":
# pylint: disable=E1120 # fix clickiness.
    sys.exit(main())
