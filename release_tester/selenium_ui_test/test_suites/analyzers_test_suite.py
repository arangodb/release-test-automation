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
        # login = LoginPage(self.webdriver)
        # login.login('root', '')
        analyzers = AnalyzerPage(self.webdriver, self.cfg)

        assert analyzers.current_user() == "ROOT", "current user is root?"
        assert analyzers.current_database() == "_SYSTEM", "current database is _system?"
        
        self.exception = False
        self.error = None
        try:
            if analyzers.current_package_version() >= semver.VersionInfo.parse("3.9.0"):
                # analyzers.select_analyzers_page()
                # analyzers.select_help_filter_btn()

                # print("Showing in-built Analyzers list \n")
                # analyzers.select_built_in_analyzers_open()

                # print("Checking in-built identity analyzer \n")
                # analyzers.select_analyzer_to_check(analyzers.identity_analyzer, analyzers.identity_analyzer_switch_view)
                # print("Checking in-built text_de analyzer \n")
                # analyzers.select_analyzer_to_check(analyzers.text_de, analyzers.text_de_switch_view)
                # print("Checking in-built text_en analyzer \n")
                # analyzers.select_analyzer_to_check(analyzers.text_en, analyzers.text_en_switch_view)
                # print("Checking in-built text_es analyzer \n")
                # analyzers.select_analyzer_to_check(analyzers.text_es, analyzers.text_es_switch_view)
                # print("Checking in-built text_fi analyzer \n")
                # analyzers.select_analyzer_to_check(analyzers.text_fi, analyzers.text_fi_switch_view)
                # print("Checking in-built text_fr analyzer \n")
                # analyzers.select_analyzer_to_check(analyzers.text_fr, analyzers.text_fr_switch_view)
                # print("Checking in-built text_it analyzer \n")
                # analyzers.select_analyzer_to_check(analyzers.text_it, analyzers.text_it_switch_view)
                # print("Checking in-built text_nl analyzer \n")
                # analyzers.select_analyzer_to_check(analyzers.text_nl, analyzers.text_nl_switch_view)
                # print("Checking in-built text_no analyzer \n")
                # analyzers.select_analyzer_to_check(analyzers.text_no, analyzers.text_no_switch_view)
                # print("Checking in-built text_pt analyzer \n")
                # analyzers.select_analyzer_to_check(analyzers.text_pt, analyzers.text_pt_switch_view)
                # print("Checking in-built text_ru analyzer \n")
                # analyzers.select_analyzer_to_check(analyzers.text_ru, analyzers.text_ru_switch_view)
                # print("Checking in-built text_sv analyzer \n")
                # analyzers.select_analyzer_to_check(analyzers.text_sv, analyzers.text_sv_switch_view)
                # print("Checking in-built text_zh analyzer \n")
                # analyzers.select_analyzer_to_check(analyzers.text_zh, analyzers.text_zh_switch_view)

                # print("Hiding in-built Analyzers list \n")
                # analyzers.select_built_in_analyzers_close()

                print("Adding Identity analyzer \n")
                analyzers.add_new_analyzer("My_Identity_Analyzer", 0, 104)  # 104 represents the required div_id in the method

                print("Adding Delimiter analyzer \n")
                analyzers.add_new_analyzer("My_Delimiter_Analyzer", 1, 108)

                print("Adding Stem analyzer \n")
                analyzers.add_new_analyzer("My_Stem_Analyzer", 2, 112)

                print("Adding Norm analyzer \n")
                analyzers.add_new_analyzer("My_Norm_Analyzer", 3, 116)

                print("Adding N-Gram analyzer \n")
                analyzers.add_new_analyzer("My_N-Gram_Analyzer", 4, 120)

                print("Adding Text analyzer \n")
                analyzers.add_new_analyzer("My_Text_Analyzer", 5, 124)

                print("Adding AQL analyzer \n")
                analyzers.add_new_analyzer("My_AQL_Analyzer", 6, 128)

                print("Adding Stopwords analyzer \n")
                analyzers.add_new_analyzer("My_Stopwords_Analyzer", 7, 132)

                print("Adding Collation analyzer \n")
                analyzers.add_new_analyzer("My_Collation_Analyzer", 8, 136)

                print("Adding Segmentation analyzer \n")
                analyzers.add_new_analyzer("My_Segmentation_Alpha_Analyzer", 9, 140)

                print("Adding Pipeline analyzer \n")
                analyzers.add_new_analyzer("My_Pipeline_Analyzer", 12, 144)

                print("Adding GeoJSON analyzer \n")
                analyzers.add_new_analyzer("My_GeoJSON_Analyzer", 13, 148)

                print("Adding GeoJSON analyzer \n")
                analyzers.add_new_analyzer("My_GeoPoint_Analyzer", 14, 152)

                # only going to work if and only all the possible type of analyzers are done creating
                print("Checking negative scenario for the identity analyzers name \n")
                analyzers.test_analyzer_expected_error("identity_analyzer", 0, 156)
                print("Checking negative scenario for the stem analyzers locale value \n")
                analyzers.test_analyzer_expected_error("stem_analyzer", 2, 156)
                print("Checking negative scenario for the stem analyzers locale value \n")
                analyzers.test_analyzer_expected_error("n-gram_analyzer", 4, 156)
                print("Checking negative scenario for the AQL analyzers \n")
                analyzers.test_analyzer_expected_error("AQL_analyzer", 6, 156)

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
                analyzer_delete_template_str = \
                    lambda name: f'//*[@id="modal-content-delete-_system::{name}"]/div[3]/button[2]'

                delete_analyzer_id_list = [analyzer_delete_template_str('My_AQL_Analyzer'),
                                           analyzer_delete_template_str('My_Collation_Analyzer'),
                                           analyzer_delete_template_str('My_Delimiter_Analyzer'),
                                           analyzer_delete_template_str('My_GeoJSON_Analyzer'),
                                           analyzer_delete_template_str('My_GeoPoint_Analyzer'),
                                           analyzer_delete_template_str('My_Identity_Analyzer'),
                                           analyzer_delete_template_str('My_N-Gram_Analyzer'),
                                           analyzer_delete_template_str('My_Norm_Analyzer'),
                                           analyzer_delete_template_str('My_Pipeline_Analyzer'),
                                           analyzer_delete_template_str('My_Segmentation_Alpha_Analyzer'),
                                           analyzer_delete_template_str('My_Stem_Analyzer'),
                                           analyzer_delete_template_str('My_Stopwords_Analyzer'),
                                           analyzer_delete_template_str('My_Text_Analyzer')]

                # analyzers deletion start
                analyzers.delete_analyzer('My_AQL_Analyzer', delete_analyzer_id_list[0])
                analyzers.delete_analyzer('My_Collation_Analyzer', delete_analyzer_id_list[1])
                analyzers.delete_analyzer('My_Delimiter_Analyzer', delete_analyzer_id_list[2])
                analyzers.delete_analyzer('My_GeoJSON_Analyzer', delete_analyzer_id_list[3])
                analyzers.delete_analyzer('My_GeoPoint_Analyzer', delete_analyzer_id_list[4])
                analyzers.delete_analyzer('My_Identity_Analyzer', delete_analyzer_id_list[5])
                analyzers.delete_analyzer('My_N-Gram_Analyzer', delete_analyzer_id_list[6])
                analyzers.delete_analyzer('My_Norm_Analyzer', delete_analyzer_id_list[7])
                analyzers.delete_analyzer('My_Pipeline_Analyzer', delete_analyzer_id_list[8])
                analyzers.delete_analyzer('My_Segmentation_Alpha_Analyzer', delete_analyzer_id_list[9])
                analyzers.delete_analyzer('My_Stem_Analyzer', delete_analyzer_id_list[10])
                analyzers.delete_analyzer('My_Stopwords_Analyzer', delete_analyzer_id_list[11])
                analyzers.delete_analyzer('My_Text_Analyzer', delete_analyzer_id_list[12])
                del analyzers
                print("---------Analyzers Page Test Completed--------- \n")
                if self.exception:
                    raise Exception(self.error)
