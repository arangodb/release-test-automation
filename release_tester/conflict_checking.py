#!/usr/bin/env python3

""" Release testing script"""
from pathlib import Path
import traceback

import sys
import platform
import click
from allure_commons.model2 import Status, StatusDetails

from common_options import very_common_options, common_options
from reporting.reporting_utils import RtaTestcase, AllureTestSuiteContext
from tools.killall import kill_all_processes
from arangodb.installers import create_config_installer_set
from arangodb.starter.deployments import (
    RunnerType,
    make_runner,
    runner_strings,
    STARTER_MODES,
)
import tools.loghelper as lh

is_windows = platform.win32_ver()[0] != ""

# pylint: disable=R0913 disable=R0914, disable=W0703, disable=R0912, disable=R0915
def run_conflict_tests(
    old_version,
    new_version,
    verbose,
    package_dir,
    test_data_dir,
    alluredir,
    clean_alluredir,
    enterprise,
    encryption_at_rest,
    zip_package,
    interactive,
    starter_mode,
    stress_upgrade,
    abort_on_error,
    publicip,
    selenium,
    selenium_driver_args,
    testrun_name,
    ssl,
    use_auto_certs,
):
    """execute upgrade tests"""
    lh.section("startup")
    results = []
    installers = []
    installers['community'] = create_config_installer_set(
        [old_version, new_version],
        verbose,
        False,
        encryption_at_rest,
        zip_package,
        Path(package_dir),
        Path(test_data_dir),
        "all",
        publicip,
        interactive,
        stress_upgrade,
    )
    installers['enterprise'] = create_config_installer_set(
        [old_version, new_version],
        verbose,
        True,
        encryption_at_rest,
        zip_package,
        Path(package_dir),
        Path(test_data_dir),
        "all",
        publicip,
        interactive,
        stress_upgrade,
    )
    old_inst_e = installers['enterprise'][0][1]
    new_inst_e = installers['enterprise'][1][1]
    old_inst_c = installers['community'][0][1]
    new_inst_c = installers['community'][1][1]
    
    with AllureTestSuiteContext(
            alluredir,
            clean_alluredir,
            enterprise,
            zip_package,
            new_version,
            encryption_at_rest,
            old_version,
            None,
            runner_strings[runner_type],
            None,
            new_inst.installer_type,
            ssl,
        ):

        # here install old, debug symbols, check conflicts.

            if self.cfg.debug_package_is_installed:
                print("removing *old* debug package in advance")
                self.old_installer.un_install_debug_package()
            self.cfg.debug_package_is_installed = self.new_installer.install_debug_package()
            if self.cfg.debug_package_is_installed:
                self.new_installer.gdb_test()
                self.cfg.debug_package_is_installed = inst.install_debug_package()
                if self.cfg.debug_package_is_installed:
                    self.progress(True, "testing debug symbols")
                    inst.gdb_test()
        if self.cfg.debug_package_is_installed:
            print("uninstalling debug package")
            inst.un_install_debug_package()

        
    return results


@click.command()
# pylint: disable=R0913
@very_common_options()
@common_options(support_old=True, interactive=True)
# fmt: off
def main(
        #very_common_options
        new_version, verbose, enterprise, package_dir, zip_package,
        # common_options
        old_version, test_data_dir, encryption_at_rest, interactive,
        starter_mode, stress_upgrade, abort_on_error, publicip,
        selenium, selenium_driver_args, alluredir, clean_alluredir, ssl, use_auto_certs):
    # fmt: on
    """ main trampoline """
    lh.configure_logging(verbose)
    results = run_conflict_tests(
        old_version,
        new_version,
        verbose,
        package_dir,
        test_data_dir,
        alluredir,
        clean_alluredir,
        enterprise,
        encryption_at_rest,
        zip_package,
        interactive,
        starter_mode,
        stress_upgrade,
        abort_on_error,
        publicip,
        selenium,
        selenium_driver_args,
        "",
        ssl,
        use_auto_certs,
    )
    print("V" * 80)
    status = True
    for one_result in results:
        print(one_result)
        status = status and one_result["success"]
    if not status:
        print("exiting with failure")
        sys.exit(1)


if __name__ == "__main__":
    # pylint: disable=E1120 # fix clickiness.
    main()
