#!/usr/bin/env python3

"""Release testing script"""
import platform

import click

import tools.loghelper as lh
from common_options import very_common_options, common_options
from package_installation_tests.community_package_installation_test_suite import \
    CommunityPackageInstallationTestSuite
from package_installation_tests.enterprise_package_installation_test_suite import \
    EnterprisePackageInstallationTestSuite

is_windows = platform.win32_ver()[0] != ""


# pylint: disable=R0913 disable=R0914, disable=W0703, disable=R0912, disable=R0915
def run_conflict_tests(
        old_version,
        new_version,
        verbose,
        package_dir,
        alluredir,
        clean_alluredir,
        enterprise,
        zip_package,
        interactive,
):
    """run package conflict tests"""
    # with AllureTestSuiteContext(
    #     results_dir=alluredir,
    #     clean=clean_alluredir,
    #     suite_name=f"Test package installation, upgrade, uninstallation.",
    #     auto_generate_parent_test_suite_name=False,
    # ):
    if not enterprise:
        suite = CommunityPackageInstallationTestSuite(
            old_version,
            new_version,
            verbose,
            package_dir,
            alluredir,
            clean_alluredir,
            enterprise,
            zip_package,
            interactive,
        )
    else:
        suite = EnterprisePackageInstallationTestSuite(
            old_version,
            new_version,
            verbose,
            package_dir,
            alluredir,
            clean_alluredir,
            enterprise,
            zip_package,
            interactive,
        )
    suite.run()
    if suite.there_are_failed_tests():
        raise Exception("There are failed tests")




@click.command()
# pylint: disable=R0913
@very_common_options()
@common_options(support_old=True, interactive=True)
# fmt: off
def main(
        # very_common_options
        new_version, verbose, enterprise, package_dir, zip_package,
        # common_options
        old_version, test_data_dir, encryption_at_rest, interactive,
        starter_mode, stress_upgrade, abort_on_error, publicip,
        selenium, selenium_driver_args, alluredir, clean_alluredir, ssl, use_auto_certs):
    # fmt: on
    """ main trampoline """
    lh.configure_logging(verbose)
    run_conflict_tests(
        old_version,
        new_version,
        verbose,
        package_dir,
        alluredir,
        clean_alluredir,
        enterprise,
        zip_package,
        interactive,
    )

if __name__ == "__main__":
    # pylint: disable=E1120 # fix clickiness.
    main()
