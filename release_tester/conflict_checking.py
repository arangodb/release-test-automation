#!/usr/bin/env python3

"""Release testing script"""
import sys
from pathlib import Path

import click

import tools.loghelper as lh
import distro
from common_options import very_common_options, common_options
from arangodb.installers import InstallerBaseConfig

IS_LINUX = sys.platform == "linux"

# pylint: disable=R0913 disable=R0914, disable=W0703, disable=R0912, disable=R0915
def run_conflict_tests(
        old_version,
        new_version,
        enterprise: bool,
        alluredir: Path,
        clean_alluredir: bool,
        basecfg: InstallerBaseConfig,
):
    """run package conflict tests"""
    # disable conflict tests for Windows and MacOS
    if not IS_LINUX:
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
    if basecfg.zip_package:
        return [
            {
                "testrun name": "Package installation/uninstallation tests were skipped for zip packages.",
                "testscenario": "",
                "success": True,
                "messages": [],
                "progress": "",
            }
        ]
    # disable conflict tests for deb packages for now.
    if distro.linux_distribution(full_distribution_name=False)[0] in ["debian", "ubuntu"]:
        return [
            {
                "testrun name": "Package installation/uninstallation tests are temporarily" +
                  "disabled for debian-based linux distros. Waiting for BTS-684",
                "testscenario": "",
                "success": True,
                "messages": [],
                "progress": "",
            }
        ]
    suite = None
    # pylint: disable=import-outside-toplevel
    if enterprise:
        from package_installation_tests.enterprise_package_installation_test_suite import \
            EnterprisePackageInstallationTestSuite as testSuite
    else:
        from package_installation_tests.community_package_installation_test_suite import \
            CommunityPackageInstallationTestSuite as testSuite
    suite = testSuite(
        old_version=old_version,
        new_version=new_version,
        alluredir=alluredir,
        clean_alluredir=clean_alluredir,
        basecfg=basecfg
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
# we ignore some params, since this is a test-only toplevel tool:
# pylint: disable=R0913
@very_common_options()
@common_options(support_old=True, interactive=True)
# fmt: off
# pylint: disable=unused-argument
def main(
        # very_common_options
        new_version, verbose, enterprise, package_dir, zip_package,
        # common_options
        hot_backup, old_version, test_data_dir, encryption_at_rest, interactive,
        starter_mode, stress_upgrade, abort_on_error, publicip,
        selenium, selenium_driver_args, alluredir, clean_alluredir, ssl, use_auto_certs):
    # fmt: on
    """ main trampoline """

    lh.configure_logging(verbose)
    basecfg = InstallerBaseConfig(verbose=verbose,
                                  zip_package=zip_package,
                                  hot_backup=hot_backup,
                                  package_dir=Path(package_dir),
                                  starter_mode="all",
                                  test_data_dir=None,
                                  publicip="127.0.0.1",
                                  interactive=interactive, # todo default to  false???
                                  stress_upgrade=False)

    results = run_conflict_tests(
        old_version,
        new_version,
        enterprise,
        alluredir,
        clean_alluredir,
        basecfg,
    )
    for result in results:
        if not result["success"]:
            raise Exception("There are failed tests")


if __name__ == "__main__":
    # pylint: disable=E1120 # fix clickiness.
    main()
