#!/usr/bin/env python3
""" analyzer page testsuite """
import traceback
import semver

from selenium_ui_test.pages.analyzers_page import AnalyzerPage
from selenium_ui_test.test_suites.base_selenium_test_suite import BaseSeleniumTestSuite
from test_suites_core.base_test_suite import testcase


class AnalyzersBaseTestSuite(BaseSeleniumTestSuite):
    """ analyzer base testsuite class """

    def test_analyzers(self, analyzer_set=1):
        """ analyzer page test base method """
        # pylint: disable=too-many-statements
        self.tprint(f"---------Analyzers Page Test Set {analyzer_set} Begin--------- \n")
        analyzers = AnalyzerPage(self.webdriver, self.cfg, self.video_start_time)

        assert analyzers.current_user() == "ROOT", "current user is root?"
        assert analyzers.current_database() == "_SYSTEM", "current database is _system?"

        self.exception = False
        self.error = None
        package_version = analyzers.current_package_version()
        try:
            if package_version >= semver.VersionInfo.parse("3.9.0"):
                analyzers.select_analyzers_page()
                analyzers.select_help_filter_btn()

                self.tprint('Checking analyzer page transition\n')
                analyzers.checking_analyzer_page_transition('transition')

                if package_version < semver.VersionInfo.parse("3.11.0"):
                    self.tprint('Checking all built-in analyzers\n')
                    analyzers.checking_all_built_in_analyzer()

                self.tprint(f'Creating all supported analyzers in set {analyzer_set}\n')
                analyzers.creating_all_supported_analyzer(self.is_enterprise, self.ui_data_dir, analyzer_set)

                self.tprint('Checking expected negative scenarios for analyzers\n')
                analyzers.analyzer_expected_error_check()

                self.tprint("Checking analyzer's search filter options \n")
                analyzers.checking_search_filter()
            else:
                self.tprint("Analyzer test is not available version below 3.9.0 \n")

        except BaseException:
            self.tprint(f"{'x' * 45}\nINFO: Error Occurred! Force Deletion Started\n{'x' * 45}")
            self.exception = True  # mark the exception status as true
            self.error = traceback.format_exc()

        finally:
            analyzers.print_combined_performance_results()
            if package_version >= semver.VersionInfo.parse("3.9.0"):
                self.tprint("Analyzer deletion started.")
                analyzers.deleting_all_created_analyzers(analyzer_set)
                del analyzers
                self.tprint(f"---------Analyzers Page Test {analyzer_set} Completed--------- \n")
                if self.exception:
                    raise Exception(self.error)
