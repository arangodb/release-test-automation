#!/usr/bin/env python3
""" analyzer page testsuite """
import semver
import traceback

from selenium_ui_test.pages.analyzers_page import AnalyzerPage
from selenium_ui_test.test_suites.base_selenium_test_suite import BaseSeleniumTestSuite
from test_suites_core.base_test_suite import testcase


class AnalyzersTestSuite(BaseSeleniumTestSuite):
    """ analyzer page testsuite """
    @testcase
    def test_analyzers(self):
        """ analyzer page test """
        # pylint: disable=too-many-statements
        print("---------Analyzers Page Test Begin--------- \n")
        analyzers = AnalyzerPage(self.webdriver, self.cfg)

        assert analyzers.current_user() == "ROOT", "current user is root?"
        assert analyzers.current_database() == "_SYSTEM", "current database is _system?"
        
        self.exception = False
        self.error = None
        package_version = analyzers.current_package_version()
        try:
            if package_version >= semver.VersionInfo.parse("3.9.0"):
                analyzers.select_analyzers_page()
                analyzers.select_help_filter_btn()

                print("Showing in-built Analyzers list \n")
                analyzers.select_built_in_analyzers_open()

                print('Checking in-built identity analyzer \n')
                analyzers.select_analyzer_to_check(2)
                print('Checking in-built text_de analyzer \n')
                analyzers.select_analyzer_to_check(3)
                print('Checking in-built text_en analyzer \n')
                analyzers.select_analyzer_to_check(4)
                print('Checking in-built text_es analyzer \n')
                analyzers.select_analyzer_to_check(5)
                print('Checking in-built text_fi analyzer \n')
                analyzers.select_analyzer_to_check(6)
                print('Checking in-built text_fr analyzer \n')
                analyzers.select_analyzer_to_check(7)
                print('Checking in-built text_it analyzer \n')
                analyzers.select_analyzer_to_check(8)
                print('Checking in-built text_nl analyzer \n')
                analyzers.select_analyzer_to_check(9)
                print('Checking in-built text_no analyzer \n')
                analyzers.select_analyzer_to_check(10)
                print('Checking in-built text_pt analyzer \n')
                analyzers.select_analyzer_to_check(11)
                print('Checking in-built text_ru analyzer \n')
                analyzers.select_analyzer_to_check(12)
                print('Checking in-built text_sv analyzer \n')
                analyzers.select_analyzer_to_check(13)
                print('Checking in-built text_zh analyzer \n')
                analyzers.select_analyzer_to_check(14)

                print("Hiding in-built Analyzers list \n")
                analyzers.select_built_in_analyzers_close()
                
                if package_version >= semver.VersionInfo.parse("3.9.99"):
                    print('Adding Identity analyzer \n')
                    analyzers.add_new_analyzer('My_Identity_Analyzer', 0)  # 128 represents required div_id

                    print('Adding Delimiter analyzer \n')
                    analyzers.add_new_analyzer('My_Delimiter_Analyzer', 1)

                    print('Adding Stem analyzer \n')
                    analyzers.add_new_analyzer('My_Stem_Analyzer', 2)

                    print('Adding Norm analyzer \n')
                    analyzers.add_new_analyzer('My_Norm_Analyzer', 3)

                    print('Adding N-Gram analyzer \n')
                    analyzers.add_new_analyzer('My_N-Gram_Analyzer', 4)

                    print('Adding Text analyzer \n')
                    analyzers.add_new_analyzer('My_Text_Analyzer', 5)

                    print('Adding AQL analyzer \n')
                    analyzers.add_new_analyzer('My_AQL_Analyzer', 6)

                    print('Adding Stopwords analyzer \n')
                    analyzers.add_new_analyzer('My_Stopwords_Analyzer', 7)

                    print('Adding Collation analyzer \n')
                    analyzers.add_new_analyzer('My_Collation_Analyzer', 8)

                    print('Adding Segmentation analyzer \n')
                    analyzers.add_new_analyzer('My_Segmentation_Alpha_Analyzer', 9)

                    print('Adding nearest-neighbor analyzer \n')
                    analyzers.add_new_analyzer('My_Nearest_Neighbor_Analyzer', 10, self.test_data_dir)

                    print('Adding classification analyzer \n')
                    analyzers.add_new_analyzer('My_Classification_Analyzer', 11, self.test_data_dir)

                    print('Adding Pipeline analyzer \n')
                    analyzers.add_new_analyzer('My_Pipeline_Analyzer', 12)

                    print('Adding GeoJSON analyzer \n')
                    analyzers.add_new_analyzer('My_GeoJSON_Analyzer', 13)

                    print('Adding GeoPoint analyzer \n')
                    analyzers.add_new_analyzer('My_GeoPoint_Analyzer', 14)

                    print('Checking analyzer expected error scenario \n')
                    analyzers.analyzer_expected_error_check()
                
                else:
                    print('Adding Identity analyzer \n')
                    analyzers.add_new_analyzer('My_Identity_Analyzer', 0)

                    print('Adding Delimiter analyzer \n')
                    analyzers.add_new_analyzer('My_Delimiter_Analyzer', 1)

                    print('Adding Stem analyzer \n')
                    analyzers.add_new_analyzer('My_Stem_Analyzer', 2)

                    print('Adding Norm analyzer \n')
                    analyzers.add_new_analyzer('My_Norm_Analyzer', 3)

                    print('Adding N-Gram analyzer \n')
                    analyzers.add_new_analyzer('My_N-Gram_Analyzer', 4)

                    print('Adding Text analyzer \n')
                    analyzers.add_new_analyzer('My_Text_Analyzer', 5)

                    print('Adding AQL analyzer \n')
                    analyzers.add_new_analyzer('My_AQL_Analyzer', 6)

                    print('Adding Stopwords analyzer \n')
                    analyzers.add_new_analyzer('My_Stopwords_Analyzer', 7)

                    print('Adding Collation analyzer \n')
                    analyzers.add_new_analyzer('My_Collation_Analyzer', 8)

                    print('Adding Segmentation analyzer \n')
                    analyzers.add_new_analyzer('My_Segmentation_Alpha_Analyzer', 9)

                    print('Adding Pipeline analyzer \n')
                    analyzers.add_new_analyzer('My_Pipeline_Analyzer', 10)

                    print('Adding GeoJSON analyzer \n')
                    analyzers.add_new_analyzer('My_GeoJSON_Analyzer', 11)

                    print('Adding GeoPoint analyzer \n')
                    analyzers.add_new_analyzer('My_GeoPoint_Analyzer', 12)

                    print('Checking analyzer expected error scenario \n')
                    analyzers.analyzer_expected_error_check()
                
                print("Checking analyzer search filter options started \n")
                analyzers.checking_search_filter_option("de")
                analyzers.checking_search_filter_option("geo", False)  # false indicating builtIn option will be disabled
                print("Checking analyzer search filter options completed \n")

            else:
                print("Analyzer UI test is not supported for the package version below 3.9.0 \n")

        except BaseException:
            print('x' * 45, "\nINFO: Error Occurred! Force Deletion Started\n", 'x' * 45)
            self.exception = True  # mark the exception status as true
            self.error = traceback.format_exc()

        finally:
            if package_version >= semver.VersionInfo.parse("3.9.0"):
                print("Analyzer deletion started.")
                analyzers.delete_analyzer('My_AQL_Analyzer')
                analyzers.delete_analyzer('My_Collation_Analyzer')
                analyzers.delete_analyzer('My_Delimiter_Analyzer')
                analyzers.delete_analyzer('My_GeoJSON_Analyzer')
                analyzers.delete_analyzer('My_GeoPoint_Analyzer')
                analyzers.delete_analyzer('My_Identity_Analyzer')
                analyzers.delete_analyzer('My_N-Gram_Analyzer')
                analyzers.delete_analyzer('My_Norm_Analyzer')
                analyzers.delete_analyzer('My_Pipeline_Analyzer')
                analyzers.delete_analyzer('My_Segmentation_Alpha_Analyzer')
                analyzers.delete_analyzer('My_Stem_Analyzer')
                analyzers.delete_analyzer('My_Stopwords_Analyzer')
                analyzers.delete_analyzer('My_Text_Analyzer')
                analyzers.delete_analyzer('My_Nearest_Neighbor_Analyzer')
                analyzers.delete_analyzer('My_Classification_Analyzer')
                del analyzers
                print("---------Analyzers Page Test Completed--------- \n")
                if self.exception:
                    raise Exception(self.error)
