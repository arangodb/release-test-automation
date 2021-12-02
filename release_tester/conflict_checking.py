#!/usr/bin/env python3

"""Release testing script"""
import sys

import click

import tools.loghelper as lh
from common_options import very_common_options, common_options
from package_installation_tests.community_package_installation_test_suite import CommunityPackageInstallationTestSuite
from package_installation_tests.enterprise_package_installation_test_suite import EnterprisePackageInstallationTestSuite


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
    # disable conflict tests for Windows and MacOS
    if not sys.platform == "linux":
        return [
            {
                "testrun name": "Package installation/uninstallation tests were skipped because OS is not Linux.",
                "testscenario": "",
                "success": True,
                "messages": [],
                "progress": "",
            }
        ]
    # disable conflict tests for zip packages
    if zip_package:
        return [
            {
                "testrun name": "Package installation/uninstallation tests were skipped for zip packages.",
                "testscenario": "",
                "success": True,
                "messages": [],
                "progress": "",
            }
        ]
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
    result = {
        "testrun name": suite.suite_name,
        "testscenario": "",
        "success": True,
        "messages": [],
        "progress": "",
    }
    if suite.there_are_failed_tests():
        result["success"] = False
        for one_result in suite.test_results:
            result["messages"].append(one_result.message)
    return [result]


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
    results = run_conflict_tests(
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
    for result in results:
        if not result["success"]:
            raise Exception("There are failed tests")


if __name__ == "__main__":
    # pylint: disable=E1120 # fix clickiness.
    main()
