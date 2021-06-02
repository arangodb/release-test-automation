#!/usr/bin/env python3

""" Release testing script"""
from pathlib import Path
import traceback

import sys
import click
from common_options import very_common_options, common_options
from tools.killall import kill_all_processes
from arangodb.installers import create_config_installer_set
from arangodb.starter.deployments import (
    RunnerType,
    make_runner,
    runner_strings,
    STARTER_MODES
)
import tools.loghelper as lh

# pylint: disable=R0913 disable=R0914, disable=W0703, disable=R0912, disable=R0915
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
            installers = create_config_installer_set([old_version, new_version],
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
            runner = None
            old_inst = installers[0][1]
            new_inst = installers[1][1]
            if runner_type:
                runner = make_runner(runner_type,
                                     selenium,
                                     selenium_driver_args,
                                     installers,
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
                        runner.agency_acquire_dump()
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
            except Exception:
                print("Ignoring old cleanup error!")
                pass
            try:
                print("Ignoring new cleanup error!")
                new_inst.cleanup_system()
            except Exception:
                pass
        except Exception as ex:
            print("Caught. " + str(ex))
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
            kill_all_processes()
            if runner:
                try:
                    runner.cleanup()
                except Exception:
                    print("Ignoring runner cleanup error!")
            try:
                print("Cleaning up system after error:")
                old_inst.un_install_debug_package()
                old_inst.un_install_package()
                old_inst.cleanup_system()
            except Exception:
                print("Ignoring old cleanup error!")
                pass
            try:
                print("Ignoring new cleanup error!")
                new_inst.un_install_debug_package()
                new_inst.un_install_package()
                new_inst.cleanup_system()
            except Exception:
                pass
        results.append(one_result)
    return results

@click.command()
# pylint: disable=R0913
@very_common_options
@common_options(support_old=True, interactive=True)
def main(
        #very_common_options
        new_version, verbose, enterprise, package_dir, zip_package,
        # common_options
        old_version, test_data_dir, encryption_at_rest, interactive,
        starter_mode, stress_upgrade, abort_on_error, publicip,
        selenium, selenium_driver_args):
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
