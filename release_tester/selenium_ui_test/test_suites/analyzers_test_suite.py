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
        try:
            if analyzers.current_package_version() >= semver.VersionInfo.parse("3.9.0"):
                analyzers.select_analyzers_page()
                # analyzers.select_help_filter_btn()

                print("Showing in-built Analyzers list \n")
                analyzers.select_built_in_analyzers_open()

                print("Checking in-built identity analyzer \n")
                analyzers.select_analyzer_to_check(analyzers.identity_analyzer, analyzers.identity_analyzer_switch_view)
                print("Checking in-built text_de analyzer \n")
                analyzers.select_analyzer_to_check(analyzers.text_de, analyzers.text_de_switch_view)
                print("Checking in-built text_en analyzer \n")
                analyzers.select_analyzer_to_check(analyzers.text_en, analyzers.text_en_switch_view)
                print("Checking in-built text_es analyzer \n")
                analyzers.select_analyzer_to_check(analyzers.text_es, analyzers.text_es_switch_view)
                print("Checking in-built text_fi analyzer \n")
                analyzers.select_analyzer_to_check(analyzers.text_fi, analyzers.text_fi_switch_view)
                print("Checking in-built text_fr analyzer \n")
                analyzers.select_analyzer_to_check(analyzers.text_fr, analyzers.text_fr_switch_view)
                print("Checking in-built text_it analyzer \n")
                analyzers.select_analyzer_to_check(analyzers.text_it, analyzers.text_it_switch_view)
                print("Checking in-built text_nl analyzer \n")
                analyzers.select_analyzer_to_check(analyzers.text_nl, analyzers.text_nl_switch_view)
                print("Checking in-built text_no analyzer \n")
                analyzers.select_analyzer_to_check(analyzers.text_no, analyzers.text_no_switch_view)
                print("Checking in-built text_pt analyzer \n")
                analyzers.select_analyzer_to_check(analyzers.text_pt, analyzers.text_pt_switch_view)
                print("Checking in-built text_ru analyzer \n")
                analyzers.select_analyzer_to_check(analyzers.text_ru, analyzers.text_ru_switch_view)
                print("Checking in-built text_sv analyzer \n")
                analyzers.select_analyzer_to_check(analyzers.text_sv, analyzers.text_sv_switch_view)
                print("Checking in-built text_zh analyzer \n")
                analyzers.select_analyzer_to_check(analyzers.text_zh, analyzers.text_zh_switch_view)

                print("Hiding in-built Analyzers list \n")
                analyzers.select_built_in_analyzers_close()
                
                print('Adding Identity analyzer \n')
                analyzers.add_new_analyzer('My_Identity_Analyzer', 0, 128)  # 128 represents required div_id

                print('Adding Delimiter analyzer \n')
                analyzers.add_new_analyzer('My_Delimiter_Analyzer', 1, 132)

                print('Adding Stem analyzer \n')
                analyzers.add_new_analyzer('My_Stem_Analyzer', 2, 136)

                print('Adding Norm analyzer \n')
                analyzers.add_new_analyzer('My_Norm_Analyzer', 3, 140)

                print('Adding N-Gram analyzer \n')
                analyzers.add_new_analyzer('My_N-Gram_Analyzer', 4, 144)

                print('Adding Text analyzer \n')
                analyzers.add_new_analyzer('My_Text_Analyzer', 5, 148)

                print('Adding AQL analyzer \n')
                analyzers.add_new_analyzer('My_AQL_Analyzer', 6, 152)

                print('Adding Stopwords analyzer \n')
                analyzers.add_new_analyzer('My_Stopwords_Analyzer', 7, 156)

                print('Adding Collation analyzer \n')
                analyzers.add_new_analyzer('My_Collation_Analyzer', 8, 160)

                print('Adding Segmentation analyzer \n')
                analyzers.add_new_analyzer('My_Segmentation_Alpha_Analyzer', 9, 164)

                print('Adding nearest-neighbor analyzer \n')
                analyzers.add_new_analyzer('My_Nearest_Neighbor_Analyzer', 10, 168, self.test_data_dir)

                print('Adding classification analyzer \n')
                analyzers.add_new_analyzer('My_Classification_Analyzer', 11, 172, self.test_data_dir)

                print('Adding Pipeline analyzer \n')
                analyzers.add_new_analyzer('My_Pipeline_Analyzer', 12, 176)

                print('Adding GeoJSON analyzer \n')
                analyzers.add_new_analyzer('My_GeoJSON_Analyzer', 13, 180)

                print('Adding GeoPoint analyzer \n')
                analyzers.add_new_analyzer('My_GeoPoint_Analyzer', 14, 184)

                # only going to work if and only all the possible type of analyzers are done creating
                print('Checking negative scenario for the identity analyzers name \n')
                analyzers.test_analyzer_expected_error('identity_analyzer', 0, 188)
                print('Checking negative scenario for the stem analyzers locale value \n')
                analyzers.test_analyzer_expected_error('stem_analyzer', 2, 188)
                print('Checking negative scenario for the stem analyzers locale value \n')
                analyzers.test_analyzer_expected_error('n-gram_analyzer', 4, 188)
                print('Checking negative scenario for the AQL analyzers \n')
                analyzers.test_analyzer_expected_error('AQL_analyzer', 6, 188)

                print("Checking analyzer search filter options started \n")
                analyzers.checking_search_filter_option("de")
                analyzers.checking_search_filter_option("geo", False)  # false indicating builtIn option will be disabled
                print("Checking analyzer search filter options completed \n")

            else:
                print("Analyzer UI test is not supported for the package version below 3.9.0 \n")

        except BaseException:
            print('x' * 45, "\nINFO: Error Occurred! Force Deletion Started\n", 'x' * 45)
            self.exception = True  # mark the exception as true
            self.error = traceback.format_exc()

        finally:
            if analyzers.current_package_version() >= semver.VersionInfo.parse("3.9.0"):
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
