from selenium_ui_test.test_suites.base_test_suite import BaseTestSuite, testcase
from selenium_ui_test.pages.analyzersPage import AnalyzerPage


class AnalyzersTestSuite(BaseTestSuite):
    @testcase
    def test_analyzers(self):
        print("---------Analyzers Page Test Begin--------- \n")
        # login = LoginPage(self.webdriver)
        # login.login('root', '')
        analyzers = AnalyzerPage(self.webdriver)
        analyzers.select_analyzers_page()
        analyzers.select_help_filter_btn()

        print('Showing in-built Analyzers list \n')
        analyzers.select_built_in_analyzers_open()

        print('Checking in-built identity analyzer \n')
        analyzers.select_analyzer_to_check(analyzers.identity_analyzer, analyzers.identity_analyzer_switch_view,
                                           analyzers.close_identity_btn)
        print('Checking in-built text_de analyzer \n')
        analyzers.select_analyzer_to_check(analyzers.text_de, analyzers.text_de_switch_view,
                                           analyzers.close_text_de_btn)
        print('Checking in-built text_en analyzer \n')
        analyzers.select_analyzer_to_check(analyzers.text_en, analyzers.text_en_switch_view,
                                           analyzers.close_text_en_btn)
        print('Checking in-built text_es analyzer \n')
        analyzers.select_analyzer_to_check(analyzers.text_es, analyzers.text_es_switch_view,
                                           analyzers.close_text_es_btn)
        print('Checking in-built text_fi analyzer \n')
        analyzers.select_analyzer_to_check(analyzers.text_fi, analyzers.text_fi_switch_view,
                                           analyzers.close_text_fi_btn)
        print('Checking in-built text_fr analyzer \n')
        analyzers.select_analyzer_to_check(analyzers.text_fr, analyzers.text_fr_switch_view,
                                           analyzers.close_text_fr_btn)
        print('Checking in-built text_it analyzer \n')
        analyzers.select_analyzer_to_check(analyzers.text_it, analyzers.text_it_switch_view,
                                           analyzers.close_text_it_btn)
        print('Checking in-built text_nl analyzer \n')
        analyzers.select_analyzer_to_check(analyzers.text_nl, analyzers.text_nl_switch_view,
                                           analyzers.close_text_nl_btn)
        print('Checking in-built text_no analyzer \n')
        analyzers.select_analyzer_to_check(analyzers.text_no, analyzers.text_no_switch_view,
                                           analyzers.close_text_no_btn)
        print('Checking in-built text_pt analyzer \n')
        analyzers.select_analyzer_to_check(analyzers.text_pt, analyzers.text_pt_switch_view,
                                           analyzers.close_text_pt_btn)
        print('Checking in-built text_ru analyzer \n')
        analyzers.select_analyzer_to_check(analyzers.text_ru, analyzers.text_ru_switch_view,
                                           analyzers.close_text_ru_btn)
        print('Checking in-built text_sv analyzer \n')
        analyzers.select_analyzer_to_check(analyzers.text_sv, analyzers.text_sv_switch_view,
                                           analyzers.close_text_sv_btn)
        print('Checking in-built text_zh analyzer \n')
        analyzers.select_analyzer_to_check(analyzers.text_zh, analyzers.text_zh_switch_view,
                                           analyzers.close_text_zh_btn)

        print('Hiding in-built Analyzers list \n')
        analyzers.select_built_in_analyzers_close()

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

        # login.logout_button()
        # del login
        del analyzers
        print("---------Analyzers Page Test Completed--------- \n")