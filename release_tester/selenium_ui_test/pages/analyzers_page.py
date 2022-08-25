#!/usr/bin/env python3
""" analyzer page object """
import time
import traceback
from selenium_ui_test.pages.base_page import Keys
from selenium_ui_test.pages.navbar import NavigationBarPage
from selenium.common.exceptions import TimeoutException


class AnalyzerPage(NavigationBarPage):
    """ analyzer page object """
    # pylint: disable=too-many-instance-attributes
    def __init__(self, webdriver, cfg):
        super().__init__(webdriver, cfg)
        self.analyzers_page = "analyzers"  # list of in-built analyzers
        self.in_built_analyzer = "icon_arangodb_settings2"
        self.add_new_analyzer_btn = '//*[@id="analyzersContent"]/div/div/div/div/button/i'

        self.close_analyzer_btn = (
            "//button[text()='Close' and not(ancestor::div[contains(@style,'display:none')]) "
            "and not(ancestor::div[contains(@style,'display: none')])] "
        )

        built_in_analyzer_template_str = \
            lambda leaflet: f'//*[@id="analyzersContent"]/div/div/table/tbody/tr[{leaflet}]/td[4]/button/i'

        built_in_analyzer_id_list = [built_in_analyzer_template_str(10),
                                     built_in_analyzer_template_str(25),
                                     built_in_analyzer_template_str(26),
                                     built_in_analyzer_template_str(27),
                                     built_in_analyzer_template_str(28),
                                     built_in_analyzer_template_str(29),
                                     built_in_analyzer_template_str(30),
                                     built_in_analyzer_template_str(31),
                                     built_in_analyzer_template_str(32),
                                     built_in_analyzer_template_str(33),
                                     built_in_analyzer_template_str(34),
                                     built_in_analyzer_template_str(35),
                                     built_in_analyzer_template_str(36)]

        switch_view_template_str = \
            lambda leaflet: f'//*[@id="modal-content-view-{leaflet}"]/div[1]/div/div[2]/button'

        switch_view_id_list = [switch_view_template_str('identity'),
                               switch_view_template_str('text_de'),
                               switch_view_template_str('text_en'),
                               switch_view_template_str('text_es'),
                               switch_view_template_str('text_fi'),
                               switch_view_template_str('text_fr'),
                               switch_view_template_str('text_it'),
                               switch_view_template_str('text_nl'),
                               switch_view_template_str('text_no'),
                               switch_view_template_str('text_pt'),
                               switch_view_template_str('text_ru'),
                               switch_view_template_str('text_sv'),
                               switch_view_template_str('text_zh')]


        self.identity_analyzer = built_in_analyzer_id_list[0]
        self.identity_analyzer_switch_view = switch_view_id_list[0]

        self.text_de = built_in_analyzer_id_list[1]
        self.text_de_switch_view = switch_view_id_list[1]

        self.text_en = built_in_analyzer_id_list[2]
        self.text_en_switch_view = switch_view_id_list[2]

        self.text_es = built_in_analyzer_id_list[3]
        self.text_es_switch_view = switch_view_id_list[3]

        self.text_fi = built_in_analyzer_id_list[4]
        self.text_fi_switch_view = switch_view_id_list[4]

        self.text_fr = built_in_analyzer_id_list[5]
        self.text_fr_switch_view = switch_view_id_list[5]
        self.text_it = built_in_analyzer_id_list[6]
        self.text_it_switch_view = switch_view_id_list[6]

        self.text_nl = built_in_analyzer_id_list[7]
        self.text_nl_switch_view = switch_view_id_list[7]

        self.text_no = built_in_analyzer_id_list[8]
        self.text_no_switch_view = switch_view_id_list[8]

        self.text_pt = built_in_analyzer_id_list[9]
        self.text_pt_switch_view = switch_view_id_list[9]

        self.text_ru = built_in_analyzer_id_list[10]
        self.text_ru_switch_view = switch_view_id_list[10]

        self.text_sv = built_in_analyzer_id_list[11]
        self.text_sv_switch_view = switch_view_id_list[11]

        self.text_zh = built_in_analyzer_id_list[12]
        self.text_zh_switch_view = switch_view_id_list[12]

    def select_analyzers_page(self):
        """Selecting analyzers page"""
        self.webdriver.refresh()
        print("Selecting Analyzers page \n")
        analyzer = self.analyzers_page
        analyzer_sitem = self.locator_finder_by_id(analyzer)
        analyzer_sitem.click()
        time.sleep(2)

    def select_help_filter_btn(self):
        """Selecting help button"""
        self.webdriver.refresh()
        print("Selecting Analyzers help filter button \n")
        help_filter = "/html/body/div[2]/div/div[2]/div[2]/div[1]/div[2]/ul/li[1]/a/i"
        help_sitem = self.locator_finder_by_xpath(help_filter)
        help_sitem.click()
        time.sleep(3)

        print("Closing Analyzers help filter \n")
        help_filter_close = "/html/body/div[10]/div/div[3]/button"
        help_close_sitem = self.locator_finder_by_xpath(help_filter_close)
        help_close_sitem.click()
        time.sleep(2)

    def select_built_in_analyzers_open(self):
        """Checking in-built analyzers list and description"""
        show_built_in_analyzers = self.in_built_analyzer
        show_built_in_analyzers_sitem = self.locator_finder_by_class(show_built_in_analyzers)
        show_built_in_analyzers_sitem.click()
        time.sleep(2)

        built_in = "//*[contains(text(),'Built-in')]"
        built_in_sitem = self.locator_finder_by_xpath(built_in)
        built_in_sitem.click()
        time.sleep(2)

    def select_built_in_analyzers_close(self):
        """Checking in-built analyzers list and description"""
        built_in = "//*[contains(text(),'Built-in')]"
        built_in_sitem = self.locator_finder_by_xpath(built_in)
        built_in_sitem.click()
        time.sleep(2)

        show_built_in_analyzers = self.in_built_analyzer
        show_built_in_analyzers_sitem = self.locator_finder_by_class(show_built_in_analyzers)
        show_built_in_analyzers_sitem.click()
        time.sleep(2)

    def select_analyzer_to_check(self, analyzer_name, analyzer_view):
        """Checking in-built analyzers one by one"""
        print("Selecting analyzer from the in-built analyzers list \n")
        identity_sitem = self.locator_finder_by_xpath(analyzer_name)
        identity_sitem.click()
        time.sleep(2)

        print("Switch to Code view \n")
        switch_to_code_view = analyzer_view
        code_view_sitem = self.locator_finder_by_xpath(switch_to_code_view)
        code_view_sitem.click()
        time.sleep(2)

        print("Switch to form view \n")
        switch_to_form_view = analyzer_view
        form_view_sitem = self.locator_finder_by_xpath(switch_to_form_view)
        form_view_sitem.click()
        time.sleep(2)

        print("Closing the analyzer \n")
        close_sitem = self.locator_finder_by_xpath(self.close_analyzer_btn)
        close_sitem.click()
        time.sleep(2)

    def add_new_analyzer(self, name, index, div_id):
        """Adding analyzer type delimiter with necessary features"""
        # pylint: disable=too-many-locals disable=too-many-branches disable=too-many-statements
        self.select_analyzers_page()
        self.webdriver.refresh()

        print("Selecting add new analyzer button \n")
        add_analyzer = self.add_new_analyzer_btn
        add_analyzer_sitem = self.locator_finder_by_xpath(add_analyzer)
        add_analyzer_sitem.click()
        time.sleep(2)

        print(f"Creating {name} started \n")
        # common attributes for all the analyzers
        analyzer_name = f"/html/body/div[{div_id}]/div/div[2]/div/div[1]/fieldset/div/div[1]/input"
        analyzer_type = f"/html/body/div[{div_id}]/div/div[2]/div/div[1]/fieldset/div/div[2]/select"
        frequency = f"/html/body/div[{div_id}]/div/div[2]/div/div[3]/fieldset/div/div[1]/input"
        norm = f"/html/body/div[{div_id}]/div/div[2]/div/div[3]/fieldset/div/div[2]/input"
        position = f"/html/body/div[{div_id}]/div/div[2]/div/div[3]/fieldset/div/div[3]/input"
        switch_view_btn = f"/html/body/div[{div_id}]/div/div[1]/div/div[2]/div/div[2]/button"
        create = f"/html/body/div[{div_id}]/div/div[3]/button[2]"

        analyzer_name_sitem = self.locator_finder_by_xpath(analyzer_name)
        analyzer_name_sitem.click()
        analyzer_name_sitem.clear()
        analyzer_name_sitem.send_keys(name)
        time.sleep(2)

        print("Selecting analyzer type \n")
        self.locator_finder_by_select_using_xpath(analyzer_type, index)
        time.sleep(2)

        print(f"selecting frequency for {name} \n")
        frequency_sitem = self.locator_finder_by_xpath(frequency)
        frequency_sitem.click()
        time.sleep(2)

        print(f"selecting norm for {name}\n")
        norm_sitem = self.locator_finder_by_xpath(norm)
        norm_sitem.click()
        time.sleep(2)

        print(f"selecting position for {name} \n")
        position_sitem = self.locator_finder_by_xpath(position)
        position_sitem.click()
        time.sleep(2)

        # ------------------ here all the different configuration would be given----------------------
        print(f"selecting value for the placeholder for {name} \n")
        # for delimiter
        if index == 1:
            delimiter = "/html/body/div[108]/div/div[2]/div/div[4]/fieldset/div/div/input"
            value = "_"
            delimiter_sitem = self.locator_finder_by_xpath(delimiter)
            delimiter_sitem.click()
            delimiter_sitem.clear()
            delimiter_sitem.send_keys(value)
        # for stem
        elif index == 2:
            locale = "/html/body/div[112]/div/div[2]/div/div[4]/fieldset/div/div/input"
            value = "en_US.utf-8"
            locale_sitem = self.locator_finder_by_xpath(locale)
            locale_sitem.click()
            locale_sitem.clear()
            locale_sitem.send_keys(value)
        # for norm
        elif index == 3:
            locale = "/html/body/div[116]/div/div[2]/div/div[4]/fieldset/div/div[1]/input"
            value = "en_US.utf-8"
            locale_sitem = self.locator_finder_by_xpath(locale)
            locale_sitem.click()
            locale_sitem.clear()
            locale_sitem.send_keys(value)

            print("Selecting case for norm analyzer using index value \n")
            case = "/html/body/div[116]/div/div[2]/div/div[4]/fieldset/div/div[2]/select"
            self.locator_finder_by_select_using_xpath(case, 0)

            print("Selecting accent for norm analyzer \n")
            accent = "/html/body/div[116]/div/div[2]/div/div[4]/fieldset/div/div[3]/input"
            accent_sitem = self.locator_finder_by_xpath(accent)
            accent_sitem.click()
            time.sleep(2)

        # for N-Gram
        elif index == 4:
            print(f"Adding minimum n-gram length for {name} \n")
            min_length = "/html/body/div[120]/div/div[2]/div/div[4]/fieldset/div/div[1]/div/div[1]/input"
            min_length_sitem = self.locator_finder_by_xpath(min_length)
            min_length_sitem.click()
            min_length_sitem.clear()
            min_length_sitem.send_keys("2")
            time.sleep(2)

            print(f"Adding maximum n-gram length for {name} \n")
            max_length = "/html/body/div[120]/div/div[2]/div/div[4]/fieldset/div/div[1]/div/div[1]/input"
            max_length_sitem = self.locator_finder_by_xpath(max_length)
            max_length_sitem.click()
            max_length_sitem.clear()
            max_length_sitem.send_keys("3")
            time.sleep(2)

            print(f"Preserve original value for {name}\n")
            preserve = "/html/body/div[120]/div/div[2]/div/div[4]/fieldset/div/div[1]/div/div[3]/input"
            preserve_sitem = self.locator_finder_by_xpath(preserve)
            preserve_sitem.click()
            time.sleep(2)

            print(f"Start marker value {name}\n")
            start_marker = "/html/body/div[120]/div/div[2]/div/div[4]/fieldset/div/div[2]/input"
            start_marker_sitem = self.locator_finder_by_xpath(start_marker)
            start_marker_sitem.click()
            start_marker_sitem.clear()
            start_marker_sitem.send_keys("^")
            time.sleep(2)

            print(f"End marker value for {name} \n")
            end_marker = "/html/body/div[120]/div/div[2]/div/div[4]/fieldset/div/div[3]/input"
            end_marker_sitem = self.locator_finder_by_xpath(end_marker)
            end_marker_sitem.click()
            end_marker_sitem.clear()
            end_marker_sitem.send_keys("$")
            time.sleep(2)

            print(f"Stream type selection using index value for {name}\n")
            stream_type = "/html/body/div[120]/div/div[2]/div/div[4]/fieldset/div/div[4]/select"
            self.locator_finder_by_select_using_xpath(stream_type, 1)
            time.sleep(2)
        # for text
        elif index == 5:
            locale = "/html/body/div[124]/div/div[2]/div/div[4]/fieldset/div/div[1]/div/div[1]/input"
            value = "en_US.utf-8"
            locale_sitem = self.locator_finder_by_xpath(locale)
            locale_sitem.click()
            locale_sitem.clear()
            locale_sitem.send_keys(value)
            time.sleep(2)

            # need to properly define the path of the stopwords
            # print('Selecting path for stopwords \n')
            # stopwords_path = '/html/body/div[32]/div/div[2]/div/div[4]/fieldset/div/div[2]/div/div[1]/input'
            # stopwords_path_sitem = self.locator_finder_by_xpath(stopwords_path)
            # stopwords_path_sitem.click()
            # stopwords_path_sitem.clear()
            # stopwords_path_sitem.send_keys('/home/username/Desktop/')

            print(f"Selecting stopwords for the {name} \n")
            stopwords = "/html/body/div[124]/div/div[2]/div/div[4]/fieldset/div/div[1]/div/div[2]/textarea"
            stopwords_sitem = self.locator_finder_by_xpath(stopwords)
            stopwords_sitem.clear()
            stopwords_sitem.send_keys("dog")
            stopwords_sitem.send_keys(Keys.ENTER)
            stopwords_sitem.send_keys("human")
            stopwords_sitem.send_keys(Keys.ENTER)
            stopwords_sitem.send_keys("tree")
            stopwords_sitem.send_keys(Keys.ENTER)
            stopwords_sitem.send_keys("of")
            stopwords_sitem.send_keys(Keys.ENTER)
            stopwords_sitem.send_keys("the")

            print(f"Selecting case for the analyzer from the dropdown menu for {name} \n")
            case = "/html/body/div[124]/div/div[2]/div/div[4]/fieldset/div/div[2]/div/div[2]/select"
            self.locator_finder_by_select_using_xpath(case, 1)

            print("Selecting stem for the analyzer \n")
            stem = "/html/body/div[124]/div/div[2]/div/div[4]/fieldset/div/div[2]/div/div[3]/input"
            stem_sitem = self.locator_finder_by_xpath(stem)
            stem_sitem.click()
            time.sleep(2)

            print("Selecting accent for the analyzer \n")
            accent = "/html/body/div[124]/div/div[2]/div/div[4]/fieldset/div/div[2]/div/div[4]/input"
            accent_sitem = self.locator_finder_by_xpath(accent)
            accent_sitem.click()
            time.sleep(2)

            print(f"Selecting minimum N-Gram length for {name} \n")
            ngram_length_min = "/html/body/div[124]/div/div[2]/div/div[4]/fieldset/div/div[4]/fieldset/div/div[1]/input"
            ngram_length_min_sitem = self.locator_finder_by_xpath(ngram_length_min)
            ngram_length_min_sitem.click()
            ngram_length_min_sitem.send_keys("2")
            time.sleep(2)

            print(f"Selecting maximum N-Gram length for {name} \n")
            ngram_length_max_length = (
                "/html/body/div[124]/div/div[2]/div/div[4]/fieldset/div/div[4]/fieldset/div/div[2]/input"
            )
            ngram_length_max_length_sitem = self.locator_finder_by_xpath(ngram_length_max_length)
            ngram_length_max_length_sitem.click()
            ngram_length_max_length_sitem.send_keys("3")
            time.sleep(2)

            print(f"Selecting preserve original for {name} \n")
            ngram_length = "/html/body/div[124]/div/div[2]/div/div[4]/fieldset/div/div[4]/fieldset/div/div[3]/input"
            ngram_length_sitem = self.locator_finder_by_xpath(ngram_length)
            ngram_length_sitem.click()
            ngram_length_sitem.send_keys("3")
            time.sleep(2)
        # for AQL analyzer
        elif index == 6:
            print(f"Selecting query string for {name} \n")
            query_string = "/html/body/div[128]/div/div[2]/div/div[4]/fieldset/div/div[1]/textarea"
            query_string_sitem = self.locator_finder_by_xpath(query_string)
            query_string_sitem.send_keys("FOR year IN 2010..2015 RETURN year")
            time.sleep(2)

            print(f"Selecting batch size for {name} \n")
            batch_size = "/html/body/div[128]/div/div[2]/div/div[4]/fieldset/div/div[2]/div/div[1]/input"
            batch_size_sitem = self.locator_finder_by_xpath(batch_size)
            batch_size_sitem.click()
            batch_size_sitem.clear()
            batch_size_sitem.send_keys("100")
            time.sleep(2)

            print(f"Selecting memory limit for {name} \n")
            memory_limit = "/html/body/div[128]/div/div[2]/div/div[4]/fieldset/div/div[2]/div/div[2]/input"
            memory_limit_sitem = self.locator_finder_by_xpath(memory_limit)
            memory_limit_sitem.click()
            memory_limit_sitem.clear()
            memory_limit_sitem.send_keys("200")
            time.sleep(2)

            print(f"Selecting collapse position for {name} \n")
            collapse = "/html/body/div[128]/div/div[2]/div/div[4]/fieldset/div/div[3]/div/div[1]/input"
            collapse_sitem = self.locator_finder_by_xpath(collapse)
            collapse_sitem.click()
            time.sleep(2)

            print(f"Selecting keep null for {name} \n")
            keep_null = "/html/body/div[128]/div/div[2]/div/div[4]/fieldset/div/div[3]/div/div[2]/input"
            keep_null_sitem = self.locator_finder_by_xpath(keep_null)
            keep_null_sitem.click()
            time.sleep(2)

            print(f"Selecting Return type for {name} \n")
            return_type = "/html/body/div[128]/div/div[2]/div/div[4]/fieldset/div/div[3]/div/div[3]/select"
            self.locator_finder_by_select_using_xpath(return_type, 1)
            time.sleep(2)
        # for stopwords
        elif index == 7:
            print(f"Selecting stopwords for {name} \n")
            stop = "/html/body/div[132]/div/div[2]/div/div[4]/fieldset/div/div[1]/textarea"
            stop_sitem = self.locator_finder_by_xpath(stop)
            stop_sitem.click()
            stop_sitem.clear()
            stop_sitem.send_keys("616e64")
            stop_sitem.send_keys(Keys.ENTER)
            time.sleep(1)
            stop_sitem.send_keys("746865")
            stop_sitem.send_keys(Keys.ENTER)
            time.sleep(1)

            print(f"Selecting hex value for {name} \n")
            hex_value = "/html/body/div[132]/div/div[2]/div/div[4]/fieldset/div/div[2]/input"
            hex_sitem = self.locator_finder_by_xpath(hex_value)
            hex_sitem.click()
            time.sleep(2)

        # Collation
        elif index == 8:
            print(f"Selecting locale for {name} \n")
            locale = "/html/body/div[136]/div/div[2]/div/div[4]/fieldset/div/div/input"
            value = "en_US.utf-8"
            locale_sitem = self.locator_finder_by_xpath(locale)
            locale_sitem.click()
            locale_sitem.clear()
            locale_sitem.send_keys(value)
        # Segmentation alpha
        elif index == 9:
            print(f"Selecting segmentation break as alpha for {name} \n")
            alpha_break = "/html/body/div[140]/div/div[2]/div/div[4]/fieldset/div/div[1]/select"
            self.locator_finder_by_select_using_xpath(alpha_break, 1)
            time.sleep(2)

            print(f"Selecting segmentation case as lower for {name} \n")
            case_lower = "/html/body/div[140]/div/div[2]/div/div[4]/fieldset/div/div[2]/select"
            self.locator_finder_by_select_using_xpath(case_lower, 0)
            time.sleep(2)

        # Pipeline
        elif index == 12:
            # ----------------------adding first pipeline analyzer as Norm analyzer--------------------------
            print(f"Selecting add analyzer button for {name} \n")
            add_analyzer01 = '/html/body/div[144]/div/div[2]/div/div[4]/fieldset/div/div[1]/button'
            add_analyzer01_sitem = self.locator_finder_by_xpath(add_analyzer01)
            add_analyzer01_sitem.click()
            time.sleep(1)

            print(f"Selecting first pipeline analyzer as Norm for {name} \n")
            norm = (
                "/html/body/div[144]/div/div[2]/div/div[4]/fieldset/div/div[2]/table/tbody/tr/td[2]"
                "/div/div[1]/label/select"
            )
            self.locator_finder_by_select_using_xpath(norm, 2)  # 2 for norm from the drop down list
            time.sleep(2)

            print(f"Selecting locale value for Norm analyzer of {name} \n")
            locale = (
                "/html/body/div[144]/div/div[2]/div/div[4]/fieldset/div"
                "/div[2]/table/tbody/tr/td[2]/div/div[3]/div/div[1]/input"
            )
            value = "en_US.utf-8"
            locale_sitem = self.locator_finder_by_xpath(locale)
            locale_sitem.click()
            locale_sitem.send_keys(value)
            time.sleep(2)

            print(f"Selecting case value to upper for Norm analyzer of {name} \n")
            case = (
                "/html/body/div[144]/div/div[2]/div/div[4]/fieldset/div"
                "/div[2]/table/tbody/tr/td[2]/div/div[3]/div/div[2]/select"
            )
            self.locator_finder_by_select_using_xpath(case, 1)  # 1 represents upper from the dropdown
            time.sleep(2)

            # ----------------------adding second pipeline analyzer as N-Gram analyzer--------------------------
            print(f"Selecting add analyzer button for {name} \n")
            new_analyzer = "/html/body/div[144]/div/div[2]/div/div[4]/fieldset/div/div[3]/button"
            new_analyzer_sitem = self.locator_finder_by_xpath(new_analyzer)
            new_analyzer_sitem.click()
            time.sleep(2)

            print(f"Selecting second pipeline analyzer as N-Gram for {name} \n")
            ngram = (
                "/html/body/div[144]/div/div[2]/div/div[4]/fieldset/div"
                "/div[2]/table/tbody/tr[2]/td[2]/div/div[1]/label/select"
            )
            self.locator_finder_by_select_using_xpath(ngram, 3)  # 3 represents N-Gram from the dropdown
            time.sleep(2)

            print(f"Selecting N-Gram minimum length for {name} \n")
            minimum_length = (
                "/html/body/div[144]/div/div[2]/div/div[4]/fieldset"
                "/div/div[2]/table/tbody/tr[2]/td[2]/div/div[3]/div/div[1]/div/div[1]/input"
            )
            minimum_length_sitem = self.locator_finder_by_xpath(minimum_length)
            minimum_length_sitem.click()
            minimum_length_sitem.clear()
            minimum_length_sitem.send_keys(3)
            time.sleep(2)

            print(f"Selecting N-Gram maximum length for {name} \n")
            maximum_length = (
                "/html/body/div[144]/div/div[2]/div/div[4]/fieldset"
                "/div/div[2]/table/tbody/tr[2]/td[2]/div/div[3]/div/div[1]/div/div[2]/input"
            )
            maximum_length_sitem = self.locator_finder_by_xpath(maximum_length)
            maximum_length_sitem.click()
            maximum_length_sitem.clear()
            maximum_length_sitem.send_keys(3)

            print(f"Selecting Preserve original value for {name}\n")
            preserve = (
                "/html/body/div[144]/div/div[2]/div/div[4]/fieldset"
                "/div/div[2]/table/tbody/tr[2]/td[2]/div/div[3]/div/div[1]/div/div[3]/input"
            )
            preserve_sitem = self.locator_finder_by_xpath(preserve)
            preserve_sitem.click()
            time.sleep(2)

            print(f"Start marker value {name}\n")
            start_marker = (
                "/html/body/div[144]/div/div[2]/div/div[4]"
                "/fieldset/div/div[2]/table/tbody/tr[2]/td[2]/div/div[3]/div/div[2]/input"
            )
            start_marker_sitem = self.locator_finder_by_xpath(start_marker)
            start_marker_sitem.click()
            start_marker_sitem.clear()
            start_marker_sitem.send_keys("^")
            time.sleep(2)

            print(f"End marker value for {name} \n")
            end_marker = (
                "/html/body/div[144]/div/div[2]/div/div[4]/fieldset"
                "/div/div[2]/table/tbody/tr[2]/td[2]/div/div[3]/div/div[3]/input"
            )
            end_marker_sitem = self.locator_finder_by_xpath(end_marker)
            end_marker_sitem.click()
            end_marker_sitem.clear()
            end_marker_sitem.send_keys("$")
            time.sleep(2)

            print(f"Stream type selection using index value for {name}\n")
            # stream_type = "/html/body/div[144]/div/div[2]/div/div[4]/fieldset/div/div[4]/select" # todo works on 3.9 or less

            stream_type = '/html/body/div[144]/div/div[2]/div/div[4]/fieldset/div/div[2]/table/tbody/tr[2]/td[2]/div/div[3]/div/div[4]/select'

            self.locator_finder_by_select_using_xpath(stream_type, 1)
            time.sleep(2)
        # GeoJson
        elif index == 13:
            print(f"Selecting type for {name} \n")
            types = "/html/body/div[148]/div/div[2]/div/div[4]/fieldset/div/div[1]/select"
            types_sitem = self.locator_finder_by_xpath(types)
            types_sitem.click()
            time.sleep(2)

            print(f"Selecting max S2 cells value for {name} \n")
            max_s2_cells = "/html/body/div[148]/div/div[2]/div/div[4]/fieldset/div/div[2]/fieldset/div/div[1]/input"
            max_s2_cells_sitem = self.locator_finder_by_xpath(max_s2_cells)
            max_s2_cells_sitem.click()
            max_s2_cells_sitem.clear()
            max_s2_cells_sitem.send_keys("20")
            time.sleep(2)

            print(f"Selecting least precise S2 levels for {name} \n")
            least_precise = "/html/body/div[148]/div/div[2]/div/div[4]/fieldset/div/div[2]/fieldset/div/div[2]/input"
            least_precise_sitem = self.locator_finder_by_xpath(least_precise)
            least_precise_sitem.click()
            least_precise_sitem.clear()
            least_precise_sitem.send_keys("10")
            time.sleep(2)

            print(f"Selecting most precise S2 levels for {name} \n")
            most_precise = "/html/body/div[148]/div/div[2]/div/div[4]/fieldset/div/div[2]/fieldset/div/div[3]/input"
            most_precise_sitem = self.locator_finder_by_xpath(most_precise)
            most_precise_sitem.click()
            most_precise_sitem.send_keys("30")
            time.sleep(2)
            # GeoJson
        elif index == 14:
            print(f"Selecting Latitude Path for {name} \n")
            latitude_paths = "/html/body/div[152]/div/div[2]/div/div[4]/fieldset/div/div[1]/input"
            latitude_paths_sitem = self.locator_finder_by_xpath(latitude_paths)
            latitude_paths_sitem.click()
            latitude_paths_sitem.send_keys("40.78")
            time.sleep(2)

            print(f"Selecting Longitude Path for {name} \n")
            longitude_paths = "/html/body/div[152]/div/div[2]/div/div[4]/fieldset/div/div[2]/input"
            longitude_paths_sitem = self.locator_finder_by_xpath(longitude_paths)
            longitude_paths_sitem.click()
            longitude_paths_sitem.send_keys("-73.97")
            time.sleep(2)

            print(f"Selecting max S2 cells value for {name} \n")
            max_s2_cells = "/html/body/div[152]/div/div[2]/div/div[4]/fieldset/div/div[3]/fieldset/div/div[1]/input"
            max_s2_cells_sitem = self.locator_finder_by_xpath(max_s2_cells)
            max_s2_cells_sitem.click()
            max_s2_cells_sitem.send_keys("20")
            time.sleep(2)

            print(f"Selecting least precise S2 levels for {name} \n")
            least_precise = "/html/body/div[152]/div/div[2]/div/div[4]/fieldset/div/div[3]/fieldset/div/div[2]/input"
            least_precise_sitem = self.locator_finder_by_xpath(least_precise)
            least_precise_sitem.click()
            least_precise_sitem.send_keys("4")
            time.sleep(2)

            print(f"Selecting most precise S2 levels for {name} \n")
            most_precise = "/html/body/div[152]/div/div[2]/div/div[4]/fieldset/div/div[3]/fieldset/div/div[3]/input"
            most_precise_sitem = self.locator_finder_by_xpath(most_precise)
            most_precise_sitem.click()
            most_precise_sitem.send_keys("23")
            time.sleep(2)

        # finalizing analyzer creation
        switch_view = switch_view_btn

        print(f"Switching current view to form view for {name}\n")
        code_view = switch_view
        code_view_sitem = self.locator_finder_by_xpath(code_view)
        code_view_sitem.click()
        time.sleep(3)

        print(f"Switching current view to code view for {name}\n")
        form_view = switch_view
        form_view_sitem = self.locator_finder_by_xpath(form_view)
        form_view_sitem.click()
        time.sleep(3)

        print(f"Selecting the create button for the {name} \n")
        create_btn = create
        create_btn_sitem = self.locator_finder_by_xpath(create_btn)
        create_btn_sitem.click()
        time.sleep(2)

        # checking the creation of the analyzer using the green notification bar appears at the bottom
        try:
            print(f"Checking successful creation of the {name} \n")
            success_message = "noty_body"
            success_message_sitem = self.locator_finder_by_class(success_message).text
            print("Notification: ", success_message_sitem, "\n")
            expected_msg = f"Success: Created Analyzer: _system::{name}"
            assert expected_msg == success_message_sitem, f"Expected {expected_msg} but got {success_message_sitem}"
        except TimeoutException:
            print("Error occurred!! required manual inspection.\n")
        print(f"Creating {name} completed successfully \n")

    def checking_search_filter_option(self, value, builtin=True):
        """checking the filter option on Analyzer tab"""
        self.select_analyzers_page()
        # select the built in analyzer list for checking filter option if builtIn tik enabled
        self.webdriver.refresh()
        if builtin:
            self.select_built_in_analyzers_open()
        # select filter placeholder for input search term
        filter_input = "filterInput"
        filter_input_sitem = self.locator_finder_by_id(filter_input)
        filter_input_sitem.click()
        filter_input_sitem.clear()
        filter_input_sitem.send_keys(value)
        filter_input_sitem.send_keys(Keys.ENTER)
        time.sleep(3)

        # checking search results if built analyzer tab are open
        try:
            if value == "de":
                de_id = "//*[@class='arango-table-td table-cell1' and text()='text_de']"
                de_sitem = self.locator_finder_by_xpath(de_id).text
                expected_msg = "text_de"
                print(f"Searching for {expected_msg} \n")
                assert expected_msg == de_sitem, f"Expected {expected_msg} but got {de_sitem}"
                print(f"Found {expected_msg} \n")
            elif value == "geo":
                geo = "//td[@class='arango-table-td table-cell2' and text()='GeoJSON']"
                geo_sitem = self.locator_finder_by_xpath(geo).text
                expected_msg = "GeoJSON"
                print(f"Searching for {expected_msg} \n")
                assert expected_msg == geo_sitem, f"Expected {expected_msg} but got {geo_sitem}"
                print(f"Found {expected_msg} \n")
            else:
                print("You did not put any search keyword. Please check manually! \n")

            time.sleep(2)
        except Exception as ex:
            raise Exception("Error occurred!! required manual inspection.\n") from ex

    def test_analyzer_expected_error(self, name, index, div_id):
        # pylint: disable=too-many-locals disable=too-many-statements
        """testing analyzers negative scenarios"""
        self.select_analyzers_page()
        self.webdriver.refresh()

        try:
            print("Selecting add new analyzer button \n")
            add_analyzer = self.add_new_analyzer_btn
            add_analyzer_sitem = self.locator_finder_by_xpath(add_analyzer)
            add_analyzer_sitem.click()
            time.sleep(2)

            print(f"checking {name} started \n")
            # common attributes for all the analyzers
            analyzer_type = f"/html/body/div[{div_id}]/div/div[2]/div/div[1]/fieldset/div/div[2]/select"
            analyzer_name_error_id = "//div[@class='noty_body']"

            print("Selecting analyzer type \n")
            self.locator_finder_by_select_using_xpath(analyzer_type, index)
            time.sleep(2)

            if index == 0:
                print(f"Expected error scenario for the {name} Started \n")
                analyzer_name_error_input = ["", "@", "1", "שלום"]
                analyzer_name_print_statement = [
                    f'Checking blank {name} with " "',
                    f'Checking {name} with symbol " @ "',
                    f'Checking numeric value for {name} " 1 "',
                    'Checking Non-ASCII Hebrew Characters "שלום"',
                ]
                analyzer_name_error_message = [
                    "Failure: Got unexpected server response: invalid characters in analyzer name ''",
                    "Failure: Got unexpected server response: invalid characters in analyzer name '@'",
                    "Failure: Got unexpected server response: invalid characters in analyzer name '1'",
                    "Failure: Got unexpected server response: invalid characters in analyzer name 'שלום'",
                ]

                # for identity analyzer name placeholder
                analyzer_name_id = f"/html/body/div[{div_id}]/div/div[2]/div/div[1]/fieldset/div/div[1]/input"

                # method template (self, error_input, print_statement, error_message, locators_id, error_message_id)
                self.check_expected_error_messages_for_analyzer(
                    analyzer_name_error_input,
                    analyzer_name_print_statement,
                    analyzer_name_error_message,
                    analyzer_name_id,
                    analyzer_name_error_id,
                    div_id,
                )

            # ------------------------------------Stem analyzer's Locale value test------------------------------------
            if index == 2:
                print(f"Expected error scenario for the {name} Started \n")

                # filling out the name placeholder first
                stem_analyzer = "/html/body/div[156]/div/div[2]/div/div[1]/fieldset/div/div[1]/input"
                stem_analyzer_sitem = self.locator_finder_by_xpath(stem_analyzer)
                stem_analyzer_sitem.click()
                stem_analyzer_sitem.clear()
                stem_analyzer_sitem.send_keys(name)
                analyzer_name_error_input = ["aaaaaaaaaa12"]
                analyzer_name_print_statement = [f'Checking {name} with input "aaaaaaaaaa12"']
                analyzer_name_error_message = [
                    "Failure: Got unexpected server response: Failure initializing an "
                    "arangosearch analyzer instance for name '_system::stem_analyzer' type "
                    "'stem'. Properties '{ \"locale\" : \"aaaaaaaaaa12\" }' was rejected by "
                    "analyzer. Please check documentation for corresponding analyzer type."
                ]

                # for stem analyzer locale placeholder
                analyzer_locale_id = f"/html/body/div[{div_id}]/div/div[2]/div/div[4]/fieldset/div/div/input"

                # method template (self, error_input, print_statement, error_message, locators_id, error_message_id, div_id)
                self.check_expected_error_messages_for_analyzer(
                    analyzer_name_error_input,
                    analyzer_name_print_statement,
                    analyzer_name_error_message,
                    analyzer_locale_id,
                    analyzer_name_error_id,
                    div_id,
                )

            # ------------------------------------Stem analyzer's Locale value test------------------------------------
            if index == 4:
                print(f"Expected error scenario for the {name} Started \n")

                # filling out the name placeholder first
                ngram_analyzer = f"/html/body/div[{div_id}]/div/div[2]/div/div[1]/fieldset/div/div[1]/input"
                ngram_analyzer_sitem = self.locator_finder_by_xpath(ngram_analyzer)
                ngram_analyzer_sitem.click()
                ngram_analyzer_sitem.clear()
                ngram_analyzer_sitem.send_keys(name)

                # fill up the max_ngram value beforehand
                max_ngram_length = f"/html/body/div[{div_id}]/div/div[2]/div/div[4]/fieldset/div/div[1]/div/div[2]/input"
                max_ngram_length_sitem = self.locator_finder_by_xpath(max_ngram_length)
                max_ngram_length_sitem.click()
                max_ngram_length_sitem.clear()
                max_ngram_length_sitem.send_keys("4")

                analyzer_name_error_input = ["-1", "100000000000000000000000"]
                analyzer_name_print_statement = [
                    f'Checking {name} with input "-1"',
                    f'Checking {name} with input "100000000000000000000000"',
                ]
                analyzer_name_error_message = [
                    "Failure: Got unexpected server response: Failure initializing "
                    "an arangosearch analyzer instance for "
                    "name '_system::n-gram_analyzer' type 'ngram'. Properties "
                    '\'{ "min" : -1, "max" : 4, "preserveOriginal" : false }\' '
                    "was rejected by analyzer. Please check documentation for "
                    "corresponding analyzer type.",
                    "Failure: Got unexpected server response: Failure initializing an "
                    "arangosearch analyzer instance for name '_system::n-gram_analyzer' type "
                    '\'ngram\'. Properties \'{ "min" : 99999999999999990000000, "max" : 4, '
                    '"preserveOriginal" : false }\' was rejected by analyzer. Please check '
                    "documentation for corresponding analyzer type.",
                ]

                # for stem analyzer locale placeholder
                min_ngram_length_id = f"/html/body/div[{div_id}]/div/div[2]/div/div[4]/fieldset/div/div[1]/div/div[1]/input"

                # method template (self, error_input, print_statement, error_message, locators_id, error_message_id, div_id)
                self.check_expected_error_messages_for_analyzer(
                    analyzer_name_error_input,
                    analyzer_name_print_statement,
                    analyzer_name_error_message,
                    min_ngram_length_id,
                    analyzer_name_error_id,
                    div_id,
                )

            # ---------------------------------------------AQL analyzer's---------------------------------------------
            if index == 6:
                print(f"Expected error scenario for the {name} Started \n")
                # filling out the name placeholder first
                aql_analyzer = f"/html/body/div[{div_id}]/div/div[2]/div/div[1]/fieldset/div/div[1]/input"
                aql_analyzer_sitem = self.locator_finder_by_xpath(aql_analyzer)
                aql_analyzer_sitem.click()
                aql_analyzer_sitem.clear()
                aql_analyzer_sitem.send_keys(name)

                print(f"Selecting query string for {name} \n")
                query_string = f"/html/body/div[{div_id}]/div/div[2]/div/div[4]/fieldset/div/div[1]/textarea"
                query_string_sitem = self.locator_finder_by_xpath(query_string)
                query_string_sitem.send_keys("FOR year IN 2010..2015 RETURN year")
                time.sleep(2)

                print(f"Selecting memory limit for {name} \n")
                memory_limit = f"/html/body/div[{div_id}]/div/div[2]/div/div[4]/fieldset/div/div[2]/div/div[2]/input"
                memory_limit_sitem = self.locator_finder_by_xpath(memory_limit)
                memory_limit_sitem.click()
                memory_limit_sitem.clear()
                memory_limit_sitem.send_keys("200")
                time.sleep(2)

                print(f"Selecting greater number for batch size {name} \n")

                analyzer_name_error_input = ["1001", "-1"]
                analyzer_name_print_statement = [f'Checking {name} with input "1001"', f'Checking {name} with input "-1"']
                analyzer_name_error_message = [
                    "Failure: Got unexpected server response: Failure initializing an "
                    "arangosearch analyzer instance for name '_system::AQL_analyzer' type "
                    "'aql'. Properties '{ \"queryString\" : \"FOR year IN 2010..2015 RETURN "
                    'year", "memoryLimit" : 200, "batchSize" : 1001 }\' was rejected by '
                    "analyzer. Please check documentation for corresponding analyzer type.",
                    "Failure: Got unexpected server response: Failure initializing an "
                    "arangosearch analyzer instance for name '_system::AQL_analyzer' type "
                    "'aql'. Properties '{ \"queryString\" : \"FOR year IN 2010..2015 RETURN "
                    'year", "memoryLimit" : 200, "batchSize" : -1 }\' was rejected by '
                    "analyzer. Please check documentation for corresponding analyzer type.",
                ]

                # for AQL analyzer batch size placeholder
                batch_size_id = f"/html/body/div[{div_id}]/div/div[2]/div/div[4]/fieldset/div/div[2]/div/div[1]/input"

                # method template (self, error_input, print_statement, error_message, locators_id, error_message_id)
                self.check_expected_error_messages_for_analyzer(
                    analyzer_name_error_input,
                    analyzer_name_print_statement,
                    analyzer_name_error_message,
                    batch_size_id,
                    analyzer_name_error_id,
                    div_id,
                )

            print(f"Closing the {name} check \n")
            close_btn = '//*[@id="modal-content-add-analyzer"]/div[3]/button[1]'
            close_btn_sitem = self.locator_finder_by_xpath(close_btn)
            close_btn_sitem.click()
            time.sleep(2)

            print(f"Expected error scenario for the {name} Completed \n")
        except Exception:
            print('Info: Error occured during checking expected error!')


    def delete_analyzer(self, analyzer_name, locator):
        """Deleting all the analyzer using their ID"""
        self.select_analyzers_page()
        self.webdriver.refresh()

        try:
            print(f'Deletion of {analyzer_name} started \n')
            analyzer_delete_icon = '//*[@id="analyzersContent"]/div/div/table/tbody/tr[1]/td[4]/button[2]/i'

            analyzer_delete_icon_sitem = self.locator_finder_by_xpath(analyzer_delete_icon)
            analyzer_delete_icon_sitem.click()
            time.sleep(2)

            # force_delete = '//*[@id="force-delete"]'
            # force_delete.sitem = self.locator_finder_by_xpath(self, force_delete)
            # force_delete.sitem.click()

            # delete_btn = f'//*[@id="modal-content-delete-0"]/div[3]/button[2]'
            delete_btn_sitem = self.locator_finder_by_xpath(locator)
            delete_btn_sitem.click()
            time.sleep(2)
            print(f'Deletion of {analyzer_name} completed \n')
        except TimeoutException:
            print('TimeoutException occurred! \n')
            print('Info: Analyzer has already been deleted or never created. \n')
        except Exception:
            # traceback.print_exc()
            raise Exception('Critical Error occurred and need manual inspection!! \n')
