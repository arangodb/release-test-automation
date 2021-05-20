#!/usr/bin/env python3

""" Release testing script"""
from pathlib import Path
import traceback

import sys
import click

from tools.killall import kill_all_processes
from arangodb.installers import make_installer, InstallerConfig
from arangodb.starter.deployments import (
    RunnerType,
    make_runner,
    runner_strings,
    STARTER_MODES
)
import tools.loghelper as lh

# pylint: disable=R0913 disable=R0914
def run_upgrade(old_version, new_version, verbose,
                package_dir, test_data_dir,
                enterprise, encryption_at_rest,
                zip_package, interactive,
                starter_mode, stress_upgrade, abort_on_error,
                publicip, selenium, selenium_driver_args,
                testrun_name):
    """ execute upgrade tests """
    lh.section("configuration")
    print("old version: " + str(old_version))
    print("version: " + str(new_version))
    print("using enterpise: " + str(enterprise))
    print("using encryption at rest: " + str(encryption_at_rest))
    print("using zip: " + str(zip_package))
    print("package directory: " + str(package_dir))
    print("starter mode: " + str(starter_mode))
    print("public ip: " + str(publicip))
    print("interactive: " + str(interactive))
    print("verbose: " + str(verbose))

    lh.section("startup")

    results = []
    for runner_type in STARTER_MODES[starter_mode]:
        if not enterprise and runner_type == RunnerType.DC2DC:
            continue
        one_result = {
            'testrun name': testrun_name,
            'testscenario': runner_strings[runner_type],
            'success': True,
            'message': 'success',
            'progress': 'success',
        }
        try:
            kill_all_processes()
            install_config_old = InstallerConfig(old_version,
                                                 verbose,
                                                 enterprise,
                                                 encryption_at_rest,
                                                 zip_package,
                                                 Path(package_dir),
                                                 Path(test_data_dir),
                                                 'all',
                                                 publicip,
                                                 interactive,
                                                 stress_upgrade)
            old_inst = make_installer(install_config_old)
            install_config_new = InstallerConfig(new_version,
                                                 verbose,
                                                 enterprise,
                                                 encryption_at_rest,
                                                 zip_package,
                                                 Path(package_dir),
                                                 Path(test_data_dir),
                                                 'all',
                                                 publicip,
                                                 interactive,
                                                 stress_upgrade)
            new_inst = make_installer(install_config_new)

            runner = None
            if runner_type:
                runner = make_runner(runner_type,
                                     selenium,
                                     selenium_driver_args,
                                     install_config_old,
                                     old_inst,
                                     install_config_new,
                                     new_inst,
                                     testrun_name)
                if runner:
                    try:
                        runner.run()
                    except Exception as ex:
                        one_result = {
                            'testrun name': testrun_name,
                            'testscenario': runner_strings[runner_type],
                            'success': False,
                            'message': str(ex),
                            'progress': runner.get_progress()
                            }
                        results.append(one_result)
                        runner.take_screenshot()
                        runner.search_for_warnings()
                        runner.zip_test_dir()
                        if abort_on_error:
                            raise ex
                        traceback.print_exc()
                        kill_all_processes()
                        lh.section("uninstall on error")
                        old_inst.un_install_debug_package()
                        old_inst.un_install_package()
                        old_inst.cleanup_system()
                        continue

            lh.section("uninstall")
            new_inst.un_install_package()
            lh.section("check system")
            new_inst.check_uninstall_cleanup()
            lh.section("remove residuals")
            try:
                old_inst.cleanup_system()
            except :
                print("Ignoring old cleanup error!")
                pass
            try:
                print("Ignoring new cleanup error!")
                new_inst.cleanup_system()
            except:
                pass
        except Exception as ex:
            print("Caught.")
            one_result = {
                'testrun name': testrun_name,
                'testscenario': runner_strings[runner_type],
                'success': False,
                'message': str(ex),
                'progress': "aborted outside of testcodes"
            }
            if abort_on_error:
                print("re-throwing.")
                raise ex
            traceback.print_exc()
            if runner:
                try:
                    runner.cleanup()
                except:
                    print("Ignoring runner cleanup error!")
            try:
                print("Cleaning up system after error:")
                old_inst.cleanup_system()
            except :
                print("Ignoring old cleanup error!")
                pass
            try:
                print("Ignoring new cleanup error!")
                new_inst.cleanup_system()
            except:
                pass
        results.append(one_result)
    return results

@click.command()
@click.option('--old-version', help='old ArangoDB version number.', default="3.7.0-nightly")
@click.option('--new-version', help='ArangoDB version number.', default="3.8.0-nightly")
@click.option('--verbose/--no-verbose',
              is_flag=True,
              default=False,
              help='switch starter to verbose logging mode.')
@click.option('--package-dir',
              default='/tmp/',
              help='directory to load the packages from.')
@click.option('--test-data-dir',
              default='/tmp/',
              help='directory create databases etc. in.')
@click.option('--enterprise/--no-enterprise',
              is_flag=True,
              default=False,
              help='Enterprise or community?')
@click.option('--encryption-at-rest/--no-encryption-at-rest',
              is_flag=True,
              default=False,
              help='turn on encryption at rest for Enterprise packages')
@click.option('--zip/--no-zip', "zip_package",
              is_flag=True,
              default=False,
              help='switch to zip or tar.gz package instead of default OS package')
@click.option('--interactive/--no-interactive',
              is_flag=True,
              default=sys.stdout.isatty(),
              help='wait for the user to hit Enter?')
@click.option('--starter-mode',
              default='all',
              type=click.Choice(STARTER_MODES.keys()),
              help='which starter deployments modes to use')
@click.option('--stress-upgrade',
              is_flag=True,
              default=False,
              help='launch arangobench before starting the upgrade')
@click.option('--abort-on-error',
              is_flag=True,
              default=True,
              help='if we should abort on first error')
@click.option('--publicip',
              default='127.0.0.1',
              help='IP for the click to browser hints.')
@click.option('--selenium',
              default='none',
              help='if non-interactive chose the selenium target')
@click.option('--selenium-driver-args',
              default=[],
              multiple=True,
              help='options to the selenium web driver')
# pylint: disable=R0913
def main(old_version, new_version, verbose,
         package_dir, test_data_dir,
         enterprise, encryption_at_rest,
         zip_package, interactive,
         starter_mode, stress_upgrade, abort_on_error,
         publicip, selenium, selenium_driver_args):
    """ main trampoline """
    lh.configure_logging(verbose)
    results = run_upgrade(old_version, new_version, verbose,
                          package_dir, test_data_dir,
                          enterprise, encryption_at_rest,
                          zip_package, interactive,
                          starter_mode, stress_upgrade, abort_on_error,
                          publicip, selenium, selenium_driver_args, "")
    print('V' * 80)
    status = True
    for one_result in results:
        print(one_result)
        status = status and one_result['success']
    if not status:
        print('exiting with failure')
        sys.exit(1)

if __name__ == "__main__":
# pylint: disable=E1120 # fix clickiness.
    main()
