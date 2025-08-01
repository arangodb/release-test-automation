#!/usr/bin/env python3
""" analyzer page object """
import time
import traceback
from collections import namedtuple
import semver
from selenium_ui_test.pages.base_page import Keys
from selenium_ui_test.pages.navbar import NavigationBarPage
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

# pylint: disable=line-too-long disable=too-many-lines disable=too-many-branches
class AnalyzerPage(NavigationBarPage):
    """ analyzer page object """
    # pylint: disable=too-many-instance-attributes disable=too-many-public-methods
    def __init__(self, webdriver, cfg, video_start_time):
        super().__init__(webdriver, cfg, video_start_time)
        self.analyzers_page = "analyzers"
        self.in_built_analyzer = "icon_arangodb_settings2"
        self.add_new_analyzer_btn = '//*[@id="analyzersContent"]/div/div/div/div/button/i'

        self.close_analyzer_btn = "//button[text()='Close' and not(ancestor::div[contains(@style,'display:none')]) " \
                                  "and not(ancestor::div[contains(@style,'display: none')])] "
        self.index = 0
        self.package_version = self.current_package_version()
        # enabling external page locators for analyzer page
        ui_version = 'new_ui' if self.version_is_newer_than('3.11.99') else 'old_ui'
        elements_dict = dict(self.elements_data[self.analyzers_page][ui_version])
        Elements = namedtuple("Elements", list(elements_dict.keys())) # pylint: disable=C0103
        self.elements = Elements(*list(elements_dict.values()))

    def select_analyzers_page(self):
        """Selecting analyzers page"""
        self.webdriver.refresh()
        self.tprint("Selecting Analyzers page \n")
        analyzer = self.analyzers_page
        analyzer_sitem = self.locator_finder_by_id(analyzer)
        analyzer_sitem.click()
        time.sleep(2)

    def select_help_filter_btn(self):
        """Selecting help button"""
        if self.version_is_newer_than('3.11.99'):
            self.tprint("select_help_filter_btn test skipped \n")
        else:
            self.webdriver.refresh()
            self.tprint("Selecting Analyzers help filter button \n")
            help_filter = "//a[@href='#analyzers']//i[@class='fa fa-question-circle']"
            help_sitem = self.locator_finder_by_xpath(help_filter, benchmark=True)
            help_sitem.click()
            time.sleep(3)
            self.webdriver.refresh()

    def select_built_in_analyzers_open(self):
        """Checking in-built analyzers list and description"""
        show_built_in_analyzers = "icon_arangodb_settings2"
        show_built_in_analyzers_sitem = self.locator_finder_by_class(show_built_in_analyzers)
        show_built_in_analyzers_sitem.click()
        time.sleep(2)

        built_in = "//*[contains(text(),'Built-in')]"
        built_in_sitem = self.locator_finder_by_xpath(built_in, benchmark=True)
        built_in_sitem.click()
        time.sleep(2)

    def select_built_in_analyzers_close(self):
        """Checking in-built analyzers list and description"""
        built_in = "//*[contains(text(),'Built-in')]"
        built_in_sitem = self.locator_finder_by_xpath(built_in, benchmark=True)
        built_in_sitem.click()
        time.sleep(2)

        show_built_in_analyzers = "icon_arangodb_settings2"
        show_built_in_analyzers_sitem = self.locator_finder_by_class(show_built_in_analyzers)
        show_built_in_analyzers_sitem.click()
        time.sleep(2)


    def select_analyzer_to_check(self, analyzer_name, locators):
        """Checking in-built analyzers one by one"""
        self.tprint(f"Checking {analyzer_name} analyzer\n")

        self.tprint('Selecting analyzer from the in-built analyzers list \n')
        self.locator_finder_by_xpath(locators).click()
        time.sleep(2)

        def switch_view_template_str(id_name):
            return f"//div[@id='modal-content-view-{id_name}']/child::div//div/div[2]/button"
        # this will create all the built-in switch view to {code/form} locators as needed
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

        # assigning all the switch view locators for finding the element
        self.tprint('Switch to Code view \n')
        if analyzer_name == "identity":
            switch_view = switch_view_id_list[0]
        elif analyzer_name == "text_de":
            switch_view = switch_view_id_list[1]
        elif analyzer_name == "text_en":
            switch_view = switch_view_id_list[2]
        elif analyzer_name == "text_es":
            switch_view = switch_view_id_list[3]
        elif analyzer_name == "text_fi":
            switch_view = switch_view_id_list[4]
        elif analyzer_name == "text_fr":
            switch_view = switch_view_id_list[5]
        elif analyzer_name == "text_it":
            switch_view = switch_view_id_list[6]
        elif analyzer_name == "text_nl":
            switch_view = switch_view_id_list[7]
        elif analyzer_name == "text_no":
            switch_view = switch_view_id_list[8]
        elif analyzer_name == "text_pt":
            switch_view = switch_view_id_list[9]
        elif analyzer_name == "text_ru":
            switch_view = switch_view_id_list[10]
        elif analyzer_name == "text_sv":
            switch_view = switch_view_id_list[11]
        else:
            switch_view = switch_view_id_list[12]

        self.locator_finder_by_xpath(switch_view).click()
        time.sleep(2)

        self.tprint('Closing the analyzer \n')
        close_sitem = self.locator_finder_by_xpath(self.close_analyzer_btn)
        close_sitem.click()
        time.sleep(2)

    def checking_analyzer_page_transition(self, keyword):
        """This method will check page transition error for BTS-902"""
        # To reproduce the issue we need to follow steps given below:
        # Login to the web UI
        # Click in the menu on “Analyzers”
        # Click in the menu on “Collections”
        # Click in the menu on “Analyzers” again
        # Click the search icon from the search/filter box if it takes
        # to the collection page then it's an error.

        if self.version_is_newer_than('3.11.0'):
            self.tprint("checking_analyzer_page_transition test skipped \n")
        else:
            self.navbar_goto("analyzers")
            self.navbar_goto("collections")
            self.navbar_goto("analyzers")

            filter_input = "filterInput"
            filter_input_sitem = self.locator_finder_by_id(filter_input)
            filter_input_sitem.click()
            filter_input_sitem.clear()
            filter_input_sitem.send_keys(keyword)
            filter_input_sitem.send_keys(Keys.ENTER)
            time.sleep(1)

            search = '//i[@class="fa fa-search"]'
            search_sitem = self.locator_finder_by_xpath(search)
            search_sitem.click()
            time.sleep(1)

            # trying to add new analyzer to confirm that we are still in analyzer page and not in collection page
            self.tprint("Selecting add new analyzer button \n")
            add_analyzer = self.add_new_analyzer_btn
            add_analyzer_sitem = self.locator_finder_by_xpath(add_analyzer)
            add_analyzer_sitem.click()
            time.sleep(1)

            create_btn = "//*[text()='Create']"
            create_btn_sitem = self.locator_finder_by_xpath(create_btn).text
            expected_text = 'Create'
            assert create_btn_sitem == expected_text, f"Expected text {expected_text} " \
                                                                f"but got {create_btn_sitem}"

            self.webdriver.refresh()
            # going back to analyzer page for the rest of the tests
            self.navbar_goto("analyzers")

    def checking_all_built_in_analyzer(self):
        """ check the built in analyzers """
        built_in_analyzers = [
            "identity",
            "text_de",
            "text_en",
            "text_es",
            "text_fi",
            "text_fr",
            "text_it",
            "text_nl",
            "text_no",
            "text_pt",
            "text_ru",
            "text_sv",
            "text_zh"
        ]

        if self.version_is_newer_than('3.11.99'):
            self.tprint("select_help_filter_btn test skipped \n")
        else:
            self.tprint('Showing in-built Analyzers list \n')
            self.select_built_in_analyzers_open()

            for analyzer in built_in_analyzers:
                self.tprint(f'Checking in-built {analyzer} analyzer \n')
                xpath = f'//tr/td[text()="{analyzer}"]/following-sibling::td[2]/button'
                self.select_analyzer_to_check(analyzer, xpath)

            self.tprint('Hiding in-built Analyzers list \n')
            self.select_built_in_analyzers_close()

    def get_analyzer_index(self, name):
        """ get the number of the analyzer """
        analyzer_lookup = {
            "My_Identity_Analyzer": 0,
            "My_Delimiter_Analyzer": 1,
            "My_Stem_Analyzer": 2,
            "My_Norm_Analyzer": 3,
            "My_N-Gram_Analyzer": 4,
            "My_Text_Analyzer": 5,
            "My_AQL_Analyzer": 6,
            "My_Stopwords_Analyzer": 7,
            "My_Collation_Analyzer": 8,
            "My_Segmentation_Alpha_Analyzer": 9,
            "My_Nearest_Neighbor_Analyzer": 10,
            "My_Classification_Analyzer": 11,
            "My_Pipeline_Analyzer": 12,
            "My_GeoJSON_Analyzer": 13,
            "My_GeoPoint_Analyzer": 14,
            "My_GeoS2_Analyzer": 15,
            "My_Minhash_Analyzer": 16,
            "My_MultiDelimiter_Analyzer": 17,
            "My_WildCard_Analyzer": 18
        }
        return analyzer_lookup.get(name, -1)  # Return -1 if the analyzer name is not found


    def add_new_analyzer(self, name, ui_data_dir=None):
        """Adding analyzer type delimiter with necessary features"""
        # pylint: disable=too-many-locals disable=too-many-branches disable=too-many-statements disable=too-many-nested-blocks
        index = self.get_analyzer_index(name)
        if index == -1:
            self.tprint(f"Analyzer '{name}' not found in the lookup table.")
            return

        self.select_analyzers_page()
        self.webdriver.refresh()
        self.wait_for_ajax()

        add_analyzer_sitem = self.locator_finder_by_xpath(self.elements.btn_add_new_analyzer, benchmark=True)
        add_analyzer_sitem.click()
        time.sleep(2)

        self.tprint(f'Creating {name} started \n')

        time.sleep(5) # debug
        analyzer_name_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.txt_analyzer_name)
        analyzer_name_sitem.click()
        analyzer_name_sitem.clear()
        analyzer_name_sitem.send_keys(name)
        time.sleep(2)

        self.tprint('Selecting analyzer type \n')
        if self.version_is_newer_than('3.11.99'):
            analyzer_type_sitem = self.locator_finder_by_xpath(self.elements.txt_analyzer_type, benchmark=True)
            analyzer_type_sitem.click()
            time.sleep(2)
            # this will simulate down arrow key according to its index position
            self.tprint(f"Analyzer's position on the list: {index}")
            for _ in range(index):
                self.send_key_action(Keys.ARROW_DOWN)
            self.send_key_action(Keys.ENTER)
            time.sleep(1)
        else:
            self.locator_finder_by_select_using_xpath(self.elements.txt_analyzer_type, index)
            time.sleep(2)

        self.tprint(f"selecting frequency for {name} \n")
        frequency_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.switch_frequency)
        frequency_sitem.click()
        time.sleep(2)

        self.tprint(f"selecting norm for {name}\n")
        norm_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.switch_norm)
        norm_sitem.click()
        time.sleep(2)

        self.tprint(f"selecting position for {name} \n")
        position_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.switch_position)
        position_sitem.click()
        time.sleep(2)

        # ------------------ here all the different configuration would be given----------------------
        self.tprint(f"selecting value for the placeholder for {name} \n")
        # for delimiter
        if name == "My_Delimiter_Analyzer":
            delimiter_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.txt_delimiter)
            delimiter_sitem.click()
            delimiter_sitem.clear()
            value = "_"
            delimiter_sitem.send_keys(value)
        # for stem
        elif name == "My_Stem_Analyzer":
            value = 'en_US.utf-8'
            locale_sitem = self.locator_finder_by_xpath(self.elements.txt_local_placeholder)
            locale_sitem.click()
            locale_sitem.clear()
            locale_sitem.send_keys(value)
        # for norm
        elif name == "My_Norm_Analyzer":
            value = 'en_US.utf-8'
            locale_sitem = self.locator_finder_by_xpath(self.elements.txt_local_placeholder)
            locale_sitem.click()
            locale_sitem.clear()
            locale_sitem.send_keys(value)

            self.tprint('Selecting case for norm analyzer using index value \n')
            if self.version_is_newer_than('3.11.99'):
                case_sitem = self.locator_finder_by_xpath(self.elements.select_case)
                case_sitem.click()
                self.send_key_action(Keys.ARROW_DOWN)
                self.send_key_action(Keys.ARROW_DOWN)
                self.send_key_action(Keys.ARROW_DOWN)
                self.send_key_action(Keys.ENTER)
            else:
                self.locator_finder_by_select_using_xpath(self.elements.select_case, 0)

            self.tprint('Selecting accent for norm analyzer \n')
            if self.version_is_newer_than('3.11.99'):
                self.tprint("Accent properties skipped \n")
            else:
                accent_sitem = self.locator_finder_by_xpath(self.elements.txt_accent)
                accent_sitem.click()
                time.sleep(2)

        # for N-Gram
        elif name == "My_N-Gram_Analyzer":
            self.tprint(f'Adding minimum n-gram length for {name} \n')
            min_length_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.txt_min_length)
            min_length_sitem.click()
            if self.version_is_newer_than('3.11.99'):
                self.clear_textfield()
            else:
                min_length_sitem.clear()
            min_length_sitem.send_keys('3')
            time.sleep(2)

            self.tprint(f'Adding maximum n-gram length for {name} \n')
            max_length_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.txt_max_length)
            max_length_sitem.click()
            if self.version_is_newer_than('3.11.99'):
                self.clear_textfield()
            else:
                max_length_sitem.clear()
            max_length_sitem.send_keys('3')
            time.sleep(2)

            self.tprint(f'Preserve original value for {name}\n')
            preserve_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.switch_preserve)
            preserve_sitem.click()
            time.sleep(2)

            self.tprint(f'Start marker value {name}\n')
            start_marker_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.txt_start_marker)
            start_marker_sitem.click()
            start_marker_sitem.clear()
            start_marker_sitem.send_keys('^')
            time.sleep(2)

            self.tprint(f'End marker value for {name} \n')
            end_marker_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.txt_end_marker)
            end_marker_sitem.click()
            end_marker_sitem.clear()
            end_marker_sitem.send_keys('$')
            time.sleep(2)

            self.tprint(f'Stream type selection using index value for {name}\n')
            if self.version_is_newer_than('3.11.99'):
                stream_type_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.select_stream_type)
                stream_type_sitem.click()
                self.send_key_action(Keys.ARROW_DOWN)
                self.send_key_action(Keys.ARROW_DOWN)
                self.send_key_action(Keys.ENTER)
            else:
                self.locator_finder_by_select_using_xpath(self.elements.select_stream_type, 1)
            time.sleep(2)
        # for text
        elif name == "My_Text_Analyzer":
            value = 'en_US.utf-8'
            locale_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.txt_local_placeholder)
            locale_sitem.click()
            locale_sitem.clear()
            locale_sitem.send_keys(value)
            time.sleep(2)

            # need to properly define the path of the stopwords
            # self.tprint('Selecting path for stopwords \n')
            # stopwords_path = '//div[label[text()="Stopwords Path"]]//input[not(@disabled)]'
            # stopwords_path_sitem = BaseSelenium.locator_finder_by_xpath(stopwords_path)
            # stopwords_path_sitem.click()
            # stopwords_path_sitem.clear()
            # stopwords_path_sitem.send_keys('/home/username/Desktop/')

            self.tprint(f'Selecting stopwords for the {name} \n')
            if self.version_is_newer_than('3.11.99'):
                self.tprint("skipped! \n")
            else:
                stopwords_sitem = self.locator_finder_by_xpath(self.elements.txt_stop_words)
                stopwords_sitem.clear()
                stopwords_sitem.send_keys('dog')
                stopwords_sitem.send_keys(Keys.ENTER)
                stopwords_sitem.send_keys('human')
                stopwords_sitem.send_keys(Keys.ENTER)
                stopwords_sitem.send_keys('tree')
                stopwords_sitem.send_keys(Keys.ENTER)
                stopwords_sitem.send_keys('of')
                stopwords_sitem.send_keys(Keys.ENTER)
                stopwords_sitem.send_keys('the')

            self.tprint(f'Selecting case for the analyzer from the dropdown menu for {name} \n')
            if self.version_is_newer_than('3.11.99'):
                case_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.select_case)
                case_sitem.click()
                self.send_key_action(Keys.ARROW_DOWN)
                self.send_key_action(Keys.TAB)
            else:
                self.locator_finder_by_select_using_xpath(self.elements.select_case, 1)

            self.tprint('Selecting stem for the analyzer \n')
            # stemming is already toggled in this version 3.12.2 nightly, thus keep it as it is
            if self.version_is_older_than('3.11.99'):
                stem_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.switch_stem)
                stem_sitem.click()
                time.sleep(2)

            self.tprint('Selecting accent for the analyzer \n')
            accent_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.switch_accent)
            accent_sitem.click()
            time.sleep(2)

            self.tprint(f'Selecting minimum N-Gram length for {name} \n')
            ngram_length_min_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.txt_ngram_min_length)
            ngram_length_min_sitem.click()
            ngram_length_min_sitem.send_keys('3')
            time.sleep(2)

            self.tprint(f'Selecting maximum N-Gram length for {name} \n')
            ngram_length_max_length_sitem = self.locator_finder_by_xpath_or_css_selector(
                self.elements.txt_ngram_max_length)
            ngram_length_max_length_sitem.click()
            ngram_length_max_length_sitem.send_keys('8')
            time.sleep(2)

            self.tprint(f'Selecting preserve original for {name} \n')
            preserve_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.txt_preserve_original)
            preserve_sitem.click()
            if self.version_is_newer_than('3.11.99'):
                self.tprint("skipped")
            else:
                preserve_sitem.send_keys('3')
            time.sleep(2)
        # for AQL analyzer
        elif name == "My_AQL_Analyzer":
            self.tprint(f'Selecting query string for {name} \n')
            query_string_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.txt_query_string)
            query_string_sitem.send_keys('RETURN SOUNDEX(@param)')
            time.sleep(2)

            self.tprint(f'Selecting batch size for {name} \n')
            batch_size_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.txt_batch_size)
            batch_size_sitem.click()
            if self.package_version >= semver.VersionInfo.parse('3.11.99'):
                self.clear_textfield()
            else:
                batch_size_sitem.clear()

            batch_size_sitem.send_keys('10')
            time.sleep(2)

            self.tprint(f'Selecting memory limit for {name} \n')
            memory_limit_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.txt_memory_limit)
            memory_limit_sitem.click()
            if self.package_version >= semver.VersionInfo.parse('3.11.99'):
                self.clear_textfield()
            else:
                memory_limit_sitem.clear()

            memory_limit_sitem.send_keys('1048576')
            time.sleep(2)

            self.tprint(f'Selecting collapse position for {name} \n')
            collapse_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.switch_collapse)
            collapse_sitem.click()
            time.sleep(2)

            self.tprint(f'Selecting keep null for {name} \n')
            if self.version_is_newer_than('3.11.99'):
                self.tprint('Skipped \n')
            else:
                keep_null_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.switch_keep_null)
                keep_null_sitem.click()
            time.sleep(2)

            self.tprint(f'Selecting Return type for {name} \n')
            if self.version_is_newer_than('3.11.99'):
                return_type_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.select_return_type)
                return_type_sitem.click()
                self.send_key_action(Keys.ARROW_DOWN)
                self.send_key_action(Keys.ENTER)

            else:
                self.locator_finder_by_select_using_xpath(self.elements.select_return_type, 1)
            time.sleep(2)
        # for stopwords
        elif name == "My_Stopwords_Analyzer":
            self.tprint(f'Selecting stopwords for {name} \n')
            stopwords_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.txt_stop_words)
            if self.version_is_newer_than('3.11.99'):
                stopwords_sitem.click()
                self.send_key_action('616e64')
                self.send_key_action(Keys.ENTER)
                time.sleep(1)
                self.send_key_action('746865')
                self.send_key_action(Keys.ENTER)
            else:
                stopwords_sitem.click()
                stopwords_sitem.clear()
                stopwords_sitem.send_keys('616e64')
                stopwords_sitem.send_keys(Keys.ENTER)
                time.sleep(1)
                stopwords_sitem.send_keys('746865')
                stopwords_sitem.send_keys(Keys.ENTER)
                time.sleep(1)

            self.tprint(f'Selecting hex value for {name} \n')
            hex_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.txt_hex_value)
            hex_sitem.click()
            time.sleep(2)

        # Collation
        elif name == "My_Collation_Analyzer":
            self.tprint(f'Selecting locale for {name} \n')
            value = 'en_US.utf-8'
            locale_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.txt_local_placeholder)
            locale_sitem.click()
            locale_sitem.clear()
            locale_sitem.send_keys(value)
        # Segmentation alpha
        elif name == "My_Segmentation_Alpha_Analyzer":
            self.tprint(f'Selecting segmentation break as alpha for {name} \n')
            if self.version_is_newer_than('3.11.99'):
                alpha_break_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.select_alpha_break)
                alpha_break_sitem.click()
                self.send_key_action(Keys.ARROW_DOWN)
                self.send_key_action(Keys.ENTER)
            else:
                self.locator_finder_by_select_using_xpath(self.elements.select_alpha_break, 1)
            time.sleep(2)

            self.tprint(f'Selecting segmentation case as lower for {name} \n')
            if self.version_is_newer_than('3.11.99'):
                case_lower_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.select_lower_case)
                case_lower_sitem.click()
                self.send_key_action(Keys.ARROW_DOWN)
                self.send_key_action(Keys.ENTER)
            else:
                self.locator_finder_by_select_using_xpath(self.elements.select_lower_case, 0)
            time.sleep(2)

        # for nearest neighbor analyzer introduced on 3.10.x
        elif name == "My_Nearest_Neighbor_Analyzer":
            location = ui_data_dir / "ui_data" / "analyzer_page" / "610_model_cooking.bin"
            self.tprint(f'Selecting model location for {name} \n')
            model_location_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.txt_model_location)
            model_location_sitem.send_keys(str(location.absolute()))
            time.sleep(2)

            self.tprint(f'Selecting Top K value for {name}\n')
            top_k_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.txt_top_k_val)
            top_k_sitem.send_keys('2')
            time.sleep(2)

        # for classification analyzer introduced on 3.10.x
        elif name == "My_Classification_Analyzer":
            location = ui_data_dir / "ui_data" / "analyzer_page" / "610_model_cooking.bin"
            self.tprint(f'Selecting model location for {name} \n')
            model_location_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.txt_model_location)
            model_location_sitem.send_keys(str(location.absolute()))
            time.sleep(2)

            self.tprint(f'Selecting Top K value for {name}\n')
            top_k_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.txt_top_k_val)
            top_k_sitem.send_keys('2')
            time.sleep(2)

            self.tprint(f'Selecting threshold for {name} \n')
            threshold_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.txt_threshold)
            # threshold_sitem.send_keys('.80')
            threshold_sitem.clear()
            threshold_sitem.send_keys('1')

        # Pipeline
        elif name == "My_Pipeline_Analyzer":
            # ----------------------adding first pipeline analyzer as Norm analyzer--------------------------
            self.tprint(f'Selecting add analyzer button for {name} \n')
            add_analyzer01_sitem = self.locator_finder_by_xpath_or_css_selector(
                self.elements.btn_add_pipeline_analyzer)
            add_analyzer01_sitem.click()
            time.sleep(1)

            self.tprint(f'Selecting first pipeline analyzer as Norm for {name} \n')
            if self.version_is_newer_than('3.11.99'):
                norm_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.select_pipeline_analyzer_type)
                norm_sitem.click()

                # selecting norm analyzer
                for _ in range(4):
                    self.send_key_action(Keys.ARROW_DOWN)
                self.send_key_action(Keys.ENTER)
                time.sleep(1)

                # selecting locale value
                select_locale_sitem = self.locator_finder_by_xpath_or_css_selector(
                    self.elements.txt_pipeline_analyzer_locale)
                select_locale_sitem.click()
                select_locale_sitem.send_keys("en_US.utf-8")
                time.sleep(1)

                # selecting case for norm analyzer
                case_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.select_case)
                case_sitem.click()
                self.send_key_action(Keys.ARROW_DOWN)
                self.send_key_action(Keys.ENTER)
                time.sleep(1)

                # selecting accent
                accent_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.select_accent)
                accent_sitem.click()
                time.sleep(1)
            else:
                self.locator_finder_by_select_using_xpath(self.elements.select_pipeline_analyzer_type, 2)  # 2 for norm from the drop-down list
                time.sleep(2)
                self.tprint(f'Selecting locale value for Norm analyzer of {name} \n')
                value = 'en_US.utf-8'
                locale_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.txt_local_placeholder)
                locale_sitem.click()
                locale_sitem.send_keys(value)
                time.sleep(2)

                self.tprint(f'Selecting case value to upper for Norm analyzer of {name} \n')
                self.locator_finder_by_select_using_xpath(self.elements.select_case,1)  # 1 represents upper from the dropdown
                time.sleep(2)
                # ----------------------adding second pipeline analyzer as N-Gram analyzer--------------------------
                self.tprint(f'Selecting add analyzer button for {name} \n')
                new_analyzer_sitem = self.locator_finder_by_xpath(self.elements.btn_add_second_pipeline_analyzer)
                new_analyzer_sitem.click()
                time.sleep(2)

                self.tprint(f'Selecting second pipeline analyzer as N-Gram for {name} \n')
                self.locator_finder_by_select_using_xpath(self.elements.select_second_pipeline_analyzer_type, 3)  # 3 represents N-Gram from the dropdown
                time.sleep(2)

                self.tprint(f'Selecting N-Gram minimum length for {name} \n')
                min_length_sitem = self.locator_finder_by_xpath(self.elements.txt_ngram_min_length)
                min_length_sitem.click()
                min_length_sitem.clear()
                min_length_sitem.send_keys(3)
                time.sleep(2)

                self.tprint(f'Selecting N-Gram maximum length for {name} \n')
                max_length_sitem = self.locator_finder_by_xpath(self.elements.txt_ngram_max_length)
                max_length_sitem.click()
                max_length_sitem.clear()
                max_length_sitem.send_keys(3)

                self.tprint(f'Selecting Preserve original value for {name}\n')
                preserve_sitem = self.locator_finder_by_xpath(self.elements.txt_preserve_original)
                preserve_sitem.click()
                time.sleep(2)

                self.tprint(f'Start marker value {name}\n')
                start_marker_sitem = self.locator_finder_by_xpath(self.elements.txt_start_marker)
                start_marker_sitem.click()
                start_marker_sitem.clear()
                start_marker_sitem.send_keys('^')
                time.sleep(2)

                self.tprint(f'End marker value for {name} \n')
                end_marker_sitem = self.locator_finder_by_xpath(self.elements.txt_end_marker)
                end_marker_sitem.click()
                end_marker_sitem.clear()
                end_marker_sitem.send_keys('$')
                time.sleep(2)

                self.tprint(f'Stream type selection using name value for {name}\n')
                self.locator_finder_by_select_using_xpath(self.elements.select_stream_type, 1)
                time.sleep(2)
        # GeoJson
        elif name == "My_GeoJSON_Analyzer":
            types_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.select_geo_json_type)
            if self.version_is_newer_than('3.11.99'):
                types_sitem.click()
                self.send_key_action(Keys.ARROW_DOWN)
                self.send_key_action(Keys.ARROW_DOWN)
                self.send_key_action(Keys.ARROW_DOWN)
                self.send_key_action(Keys.ENTER)

            else:
                types_sitem.click()
            time.sleep(2)

            self.tprint(f'Selecting max S2 cells value for {name} \n')
            max_s2_cells_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.txt_max_s2_cells)
            max_s2_cells_sitem.click()

            if self.version_is_newer_than('3.11.99'):
                self.send_key_action(Keys.BACKSPACE)
                self.send_key_action(Keys.BACKSPACE)
            else:
                max_s2_cells_sitem.clear()

            max_s2_cells_sitem.send_keys('20')
            time.sleep(2)

            self.tprint(f'Selecting least precise S2 levels for {name} \n')
            least_precise_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.txt_least_precise_s2_level)
            least_precise_sitem.click()

            if self.version_is_newer_than('3.11.99'):
                self.send_key_action(Keys.BACKSPACE)
            else:
                least_precise_sitem.clear()

            least_precise_sitem.send_keys('10')
            time.sleep(2)

            self.tprint(f'Selecting most precise S2 levels for {name} \n')
            most_precise_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.txt_most_precise_s2_level)
            most_precise_sitem.click()
            if self.version_is_newer_than('3.11.99'):
                self.send_key_action(Keys.BACKSPACE)
                self.send_key_action(Keys.BACKSPACE)

            most_precise_sitem.send_keys('30')
            time.sleep(2)
        # GeoPoint
        elif name == "My_GeoPoint_Analyzer":
            self.tprint(f'Selecting Latitude Path for {name} \n')
            latitude_paths_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.txt_latitude)
            latitude_paths_sitem.click()
            latitude_paths_sitem.send_keys('40.78')
            if self.version_is_newer_than('3.11.99'):
                self.send_key_action(Keys.ENTER)
            time.sleep(2)

            self.tprint(f'Selecting Longitude Path for {name} \n')
            longitude_paths_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.txt_longitude)
            longitude_paths_sitem.click()
            longitude_paths_sitem.send_keys('-73.97')
            if self.version_is_newer_than('3.11.99'):
                self.send_key_action(Keys.ENTER)
            time.sleep(2)

            self.tprint(f'Selecting max S2 cells value for {name} \n')
            max_s2_cells_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.txt_geo_point_max_s2_cells)
            max_s2_cells_sitem.click()
            if self.version_is_newer_than('3.11.99'):
                self.send_key_action(Keys.BACKSPACE)
                self.send_key_action(Keys.BACKSPACE)
            max_s2_cells_sitem.send_keys('20')
            time.sleep(2)

            self.tprint(f'Selecting least precise S2 levels for {name} \n')
            least_precise_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.txt_least_precise_s2_level)
            least_precise_sitem.click()
            if self.version_is_newer_than('3.11.99'):
                self.send_key_action(Keys.BACKSPACE)
            least_precise_sitem.send_keys('4')
            time.sleep(2)

            self.tprint(f'Selecting most precise S2 levels for {name} \n')
            most_precise_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.txt_most_precise_s2_level)
            most_precise_sitem.click()
            if self.version_is_newer_than('3.11.99'):
                self.send_key_action(Keys.BACKSPACE)
                self.send_key_action(Keys.BACKSPACE)
            most_precise_sitem.send_keys('23')
            time.sleep(2)
        # GeoS2
        elif name == 'My_GeoS2_Analyzer':
            self.tprint("Selecting type of geos2 analyzer")
            if self.version_is_older_than('3.10.99'):
                self.tprint("Type and Formate selection skipped for this version below 3.10 \n")
            else:
                type_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.select_geo_s2_analyzer_type)
                type_sitem.click()
                self.send_key_action(Keys.ARROW_DOWN)
                self.send_key_action(Keys.ARROW_DOWN)

                if self.version_is_newer_than('3.11.99'):
                    self.send_key_action(Keys.ENTER)

                self.tprint("Selecting format of geos2 analyzer")

                format_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.select_geo_s2_analyzer_format)
                format_sitem.click()
                self.send_key_action(Keys.ARROW_DOWN)
                self.send_key_action(Keys.ARROW_DOWN)
                if self.version_is_newer_than('3.11.99'):
                    self.send_key_action(Keys.ENTER)

            self.tprint(f"Selecting max s2 for {name} \n")

            max_s2_cell_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.txt_geo_s2_max_s2_cells)
            max_s2_cell_sitem.click()
            if self.version_is_newer_than('3.11.99'):
                self.send_key_action(Keys.BACKSPACE)
                self.send_key_action(Keys.BACKSPACE)
            self.send_key_action("20")
            time.sleep(2)

            self.tprint(f'Selecting least precise for {name} \n')
            least_precise_s2_level_sitem = self.locator_finder_by_xpath_or_css_selector(
                self.elements.txt_geo_s2_least_precise_s2_level)
            least_precise_s2_level_sitem.click()
            if self.version_is_newer_than('3.11.99'):
                self.send_key_action(Keys.BACKSPACE)
            self.send_key_action("4")
            time.sleep(2)

            self.tprint(f'Selecting most precise S2 level for {name} \n')
            most_precise_s2_level_sitem = self.locator_finder_by_xpath_or_css_selector(
                self.elements.txt_geo_s2_most_precise_s2_level)
            most_precise_s2_level_sitem.click()
            if self.version_is_newer_than('3.11.99'):
                self.send_key_action(Keys.BACKSPACE)
                self.send_key_action(Keys.BACKSPACE)
            self.send_key_action("23")
            time.sleep(2)
        # Minhash
        elif name == 'My_Minhash_Analyzer':
            self.tprint("Selecting type of minhash analyzer")
            analyzer_type_sitem = self.locator_finder_by_xpath_or_css_selector(
                self.elements.select_minhash_analyzer_type)
            analyzer_type_sitem.click()
            # selecting minhash for delimiter analyzer
            self.send_key_action(Keys.ARROW_DOWN)
            self.send_key_action(Keys.ARROW_DOWN)
            self.send_key_action(Keys.ENTER)
            time.sleep(2)

            self.tprint("adding minhash for delimiter analyzer")
            delimiter_value_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.txt_delimiter_value)
            delimiter_value_sitem.click()
            delimiter_value_sitem.send_keys("#")
            time.sleep(1)

            numhashes_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.txt_num_of_hashes)
            numhashes_sitem.click()
            numhashes_sitem.send_keys("10")
            time.sleep(1)
        # MultiDelimiter
        elif name == "My_MultiDelimiter_Analyzer":
            self.tprint("Selecting type of MultiDelimiter analyzer")
            delimiters_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.txt_delimiters)
            delimiters_sitem.click()

            # selecting values for MultiDelimiter analyzer
            self.send_key_action(":")
            self.send_key_action(Keys.ENTER)

            self.send_key_action(";")
            self.send_key_action(Keys.ENTER)

            self.send_key_action(",")
            self.send_key_action(Keys.ENTER)

            self.send_key_action(".")
            self.send_key_action(Keys.ENTER)

            self.send_key_action("/")
            self.send_key_action(Keys.ENTER)

            self.send_key_action("ß")
            self.send_key_action(Keys.ENTER)

            self.send_key_action("Û")
            self.send_key_action(Keys.ENTER)

            self.send_key_action("⚽")
            self.send_key_action(Keys.ENTER)
            time.sleep(2)
        # WildCard
        elif name == "My_WildCard_Analyzer":
            self.tprint("Selecting type of WildCard analyzer\n")
            ngram_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.txt_ngram_size)
            ngram_sitem.click()
            self.send_key_action(Keys.BACKSPACE)
            ngram_sitem.send_keys('4')
            time.sleep(2)

            self.tprint("Selecting delimiter analyzer\n")
            delimiter_sitem = self.locator_finder_by_xpath_or_css_selector(
                self.elements.select_delimiter_analyzer_type)
            delimiter_sitem.click()
            time.sleep(1)

            # selecting multi-delimiter analyzer from the drop-down menu
            for _ in range(16):
                self.send_key_action(Keys.ARROW_DOWN)

            self.send_key_action(Keys.ENTER)

            self.send_key_action(Keys.ARROW_DOWN)
            self.send_key_action(Keys.ENTER)

            self.tprint("Selecting Multi Delimiters \n")
            delimiter_properties_sitem = self.locator_finder_by_xpath_or_css_selector(
                self.elements.txt_multi_delimiters)
            delimiter_properties_sitem.click()

            self.send_key_action(",")
            self.send_key_action(Keys.ENTER)

            self.send_key_action(".")
            self.send_key_action(Keys.ENTER)

            self.send_key_action(":")
            self.send_key_action(Keys.ENTER)

            self.send_key_action(";")
            self.send_key_action(Keys.ENTER)

            self.send_key_action("!")
            self.send_key_action(Keys.ENTER)

            self.send_key_action("?")
            self.send_key_action(Keys.ENTER)

            self.send_key_action("[")
            self.send_key_action(Keys.ENTER)

            time.sleep(2)

        #todo need to fix this one for 3.11.x
        if self.version_is_newer_than('3.11.0'):
            self.tprint("skiped switching view for code view\n")
        else:
            self.tprint(f'Switching current view to form view for {name}\n')
            switch_view_btn = '//*[@id="modal-content-add-analyzer"]/div[1]/div/div[2]/div/div[2]/button'
            code_view_sitem = self.locator_finder_by_xpath(switch_view_btn)
            code_view_sitem.click()
            time.sleep(3)

            self.tprint(f'Switching current view to code view for {name}\n')
            form_view_sitem = self.locator_finder_by_xpath(switch_view_btn)
            form_view_sitem.click()
            time.sleep(3)

        self.tprint(f"Selecting the create button for the {name} \n")
        create_btn_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.btn_create_analyzer)
        create_btn_sitem.click()
        time.sleep(2)

        # checking the creation of the analyzer using the green notification bar appears at the bottom
        try:
            self.tprint(f"Checking successful creation of the {name} \n")
            if self.version_is_newer_than('3.11.99'):
                success_message = "/html//div[@id='chakra-toast-manager-bottom']"
                success_message_sitem = self.locator_finder_by_xpath(success_message).text
                self.tprint(f"Notification: {success_message_sitem}\n")
                expected_msg = f"The analyzer: {name} was successfully created"
            else:
                success_message = "noty_body"
                success_message_sitem = self.locator_finder_by_class(success_message).text
                self.tprint(f"Notification: {success_message_sitem}\n")
                expected_msg = f"Success: Created Analyzer: _system::{name}"

            assert expected_msg == success_message_sitem, f"Expected {expected_msg} but got {success_message_sitem}"
        except TimeoutException:
            self.tprint("Error occurred!! required manual inspection.\n")
        self.tprint(f"Creating {name} completed successfully \n")

        # --------------------here we are checking the properties of the created analyzer----------------------
        if self.version_is_older_than('3.11.0'):
            # primariliy enable the test for the version below 3.11.99
            if name in ["My_Nearest_Neighbor_Analyzer", "My_Classification_Analyzer"]:
                self.tprint(f"Skipping the properties check for {name} \n") #todo: need to fix this for 3.11.x, location porperties has changed due to the dynamic selenoid depoloyment
            else:
                try:
                    self.wait_for_ajax()
                    self.tprint(f"Checking analyzer properties for {name} \n")
                    if self.version_is_newer_than('3.10.99'):
                        # Finding the analyzer to check its properties
                        if self.version_is_newer_than('3.11.99'):
                            analyzer_xpath = f"//*[text()='_system::{name}']"
                            analyzer_sitem = self.locator_finder_by_xpath(analyzer_xpath)
                        else:
                            time.sleep(3)
                            # add search capability for the analyzer to narrow down the search
                            search_analyzer = "(//input[@id='filterInput'])[1]"
                            search_analyzer_sitem = self.locator_finder_by_xpath(search_analyzer)
                            search_analyzer_sitem.click()
                            search_analyzer_sitem.clear()
                            search_analyzer_sitem.send_keys(name)
                            time.sleep(2)

                            # then click on the analyzer to view its properties
                            analyzer_xpath = f"//td[text()='_system::{name}']/following-sibling::td/button[@class='pure-button'][1]"
                            analyzer_sitem = self.locator_finder_by_xpath(analyzer_xpath)

                        if analyzer_sitem is None:
                            self.tprint(f'This {name} has never been created \n')
                        else:
                            analyzer_sitem.click()
                            time.sleep(3)

                        if self.version_is_older_than('3.11.99'):
                            self.tprint(f"Switching to code view for {name} \n")
                            switch_to_code = "(//button[normalize-space()='Switch to code view'])[1]"
                            switch_to_code_sitem = self.locator_finder_by_xpath(switch_to_code)
                            switch_to_code_sitem.click()

                        # Find all elements matching the XPath from the ace editor
                        if self.version_is_newer_than('3.11.99'):
                            ace_text_area = "//div[contains(@class, 'ace_text-layer')]//div[contains(@class, 'ace_line_group')]"
                            ace_line_groups = self.webdriver.find_elements(By.XPATH, ace_text_area)
                            # Initialize an empty list to store text
                            text_list = []
                            # Iterate over each element and extract its text
                            for element in ace_line_groups:
                                text_list.append(element.text.strip())  # Append text from each line group
                                time.sleep(3)

                            # Join the text from all elements into a single string
                            final_text = ''.join(text_list)  # Join the text without splitting
                            actual_properties = ''.join(str(final_text).split())
                        else:
                            # Find the textarea element using XPath based on its class
                            # Define the class name of the textarea element
                            class_name = "sc-EHOje"  # Replace with the actual class name

                            # Execute JavaScript code to retrieve the text content of the textarea
                            analyzer_properties = self.webdriver.execute_script(f'''
                                var className = "{class_name}";
                                var textareaElement = document.querySelector("textarea." + className);
                                return textareaElement.value;
                            ''')
                            actual_properties = ''.join(str(analyzer_properties).split())

                        # Get expected properties based on analyzer name
                        if self.version_is_newer_than("3.11.99"):
                            expected_properties = ''.join(str(self.generate_expected_properties_312(name, ui_data_dir)).split())
                        else:
                            expected_properties = ''.join(str(self.generate_expected_properties_311(name, ui_data_dir)).split())
                        # Assert that the copied text matches the expected text
                        try:
                            assert actual_properties == expected_properties, "Text does not match the expected text \n"
                            self.tprint(f"Actual porperties: {actual_properties} \nexpected properties: {expected_properties} \nfound for {name} \n")
                        except AssertionError as ex:
                            self.tprint(f"actual_properties: {actual_properties} \n")
                            self.tprint(f"expected_properties: {expected_properties} \n")
                            raise AssertionError(
                                f"Actual properties didn't matches the expected properties for {name}") from ex
                        self.tprint(f"Actual properties matches the expected properties for {name}. \n")

                except TimeoutException as ex:
                    self.tprint(f'Failed to parse properties from the {name} and the error is: {ex} \n')

                # -------------------- Running a query for each analyzer's after creation----------------------
                try:
                    self.tprint(f"Checking analyzer query for {name} \n")
                    if self.version_is_older_than('3.11.99'):
                        self.tprint(f'Running query for {name} started \n')
                        # Goto query tab
                        self.tprint("Selecting query tab \n")
                        if self.version_is_newer_than('3.11.99'):
                            self.locator_finder_by_id('queries').click()
                        else:
                            self.webdriver.refresh()
                            self.locator_finder_by_id('queries').click()
                        time.sleep(3)
                        self.tprint('Selecting query execution area \n')
                        self.select_query_execution_area()

                        self.tprint(f'Running query for {name} analyzer started\n')
                        # Get query and expected output based on analyzer name
                        if self.version_is_newer_than('3.11.99'):
                            analyzer_query = self.get_analyzer_query_312(name)
                        else:
                            analyzer_query = self.get_analyzer_query_311(name)

                        if analyzer_query is None:
                            self.tprint(f"Analyzer '{name}' not found. Skipping test.")
                            return # Skip this test and move to the next one
                        if self.version_is_newer_than('3.11.99'):
                            self.send_key_action(analyzer_query)
                        else:
                            self.clear_textfield()
                            self.send_key_action(analyzer_query)

                        self.query_execution_btn()
                        self.scroll(1)

                        # Find all elements matching the XPath from the ace editor
                        if self.version_is_older_than('3.11.99'):
                            ace_text_area = '//div[@id="outputEditor0"]//div[contains(@class, "ace_layer ace_text-layer")]'
                            ace_line_groups = self.webdriver.find_elements(By.XPATH, ace_text_area)
                            # Initialize an empty list to store text
                            text_list = []
                            # Iterate over each element and extract its text
                            for element in ace_line_groups:
                                text_list.append(element.text.strip())  # Append text from each line group
                                time.sleep(1)

                            # Join the text from all elements into a single string
                            final_text = ''.join(text_list)  # Join the text without splitting
                            query_actual_output = ''.join(str(final_text).split())
                            self.tprint(f"query_actual_output: {query_actual_output} \n")

                        if self.version_is_newer_than('3.11.99'):
                            query_expected_output = self.get_analyzer_expected_output_312(name)
                        else:
                            query_expected_output = self.get_analyzer_expected_output_311(name)

                        if query_expected_output is None:
                            self.tprint(f"Analyzer '{name}' not found. Skipping test.")
                            return # Skip this test and move to the next one
                        # Assert that the copied text matches the expected text
                        if query_actual_output != ''.join(str(query_expected_output).split()):
                            self.tprint(f"query_actual_output: {query_actual_output} \n")
                            self.tprint(f"query_expected_output: {query_expected_output} \n")
                            raise Exception(
                                f"Actual query output didn't matches the expected query output for {name}\n")
                        self.tprint(f"Actual query output matches the expected query output for {name}\n")
                except TimeoutException as ex:
                    raise Exception(f"TimeoutException occurred during running the query for '{name}' analyzer.\nError: {ex}") from ex

    @staticmethod
    def generate_analyzer_queries_312(analyzer_name):
        """ return queries for analyzers """
        return {
            "My_Identity_Analyzer": {
                "query": "RETURN TOKENS('UPPER lower dïäcríticš', 'My_Identity_Analyzer')",
                "expected_output": [["UPPER lower dïäcríticš"]]
            },
            "My_Delimiter_Analyzer": {
                "query": "RETURN TOKENS('some-delimited-words', 'My_Delimiter_Analyzer')",
                "expected_output": [["some-delimited-words"]]
            },
            "My_Stem_Analyzer": {
                "query": "RETURN TOKENS('databases', 'My_Stem_Analyzer')",
                "expected_output": [["databas"]]
            },
            "My_Norm_Analyzer": {
                "query": "RETURN TOKENS('UPPER lower dïäcríticš', 'My_Norm_Analyzer')",
                "expected_output": [["UPPER LOWER DÏÄCRÍTICŠ"]]
            },
            "My_N-Gram_Analyzer": {
                "query": "RETURN TOKENS('foobar', 'My_N-Gram_Analyzer')",
                "expected_output": [["^foo", "^foobar", "foobar$", "oob", "oba", "bar$"]]
            },
            "My_Text_Analyzer": {
                "query": "RETURN TOKENS('The quick brown fox jumps over the dogWithAVeryLongName', 'My_Text_Analyzer')",
                "expected_output": [
                    ["the", "qui", "quic", "quick", "bro", "brow", "brown", "fox", "jum", "jump", "jumps", "ove",
                     "over", "the", "dog", "dogw", "dogwi", "dogwit", "dogwith", "dogwitha", "dogwithaverylongname"]]
            },
            "My_AQL_Analyzer": {
                "query": "RETURN TOKENS('UPPER lower dïäcríticš','My_AQL_Analyzer')",
                "expected_output": [["U164"]]
            },
            "My_Stopwords_Analyzer": {
                "query": "RETURN FLATTEN(TOKENS(SPLIT('the fox and the dog and a theater', ' '), 'My_Stopwords_Analyzer'))",
                "expected_output": [["fox", "dog", "a", "theater"]]
            },
            "My_Pipeline_Analyzer": {
                "query": "RETURN TOKENS('Quick brown foX', 'My_Pipeline_Analyzer')",
                "expected_output": [["QUICK BROWN FOX"]]
            },


            # Add more analyzers and their queries and expected outputs here
        }.get(analyzer_name, {})

    def get_analyzer_query_312(self, analyzer_name):
        """get analyzer query based on the analyzer name"""
        return self.generate_analyzer_queries_312(analyzer_name).get("query")

    def get_analyzer_expected_output_312(self, analyzer_name):
        """Get analyzer query's expected output based on the analyzer name"""
        analyzer_data = self.generate_analyzer_queries_312(analyzer_name)
        if analyzer_data:
            expected_output = analyzer_data.get("expected_output")
            # Convert the expected output to a string using double quotes
            if isinstance(expected_output, list):
                return str(expected_output).replace("'", '"')
            return expected_output
        return None

    @staticmethod
    def generate_analyzer_queries_311(analyzer_name):
        """ generate queries for the analyzers """
        return {
            "My_Identity_Analyzer": {
                "query": "RETURN TOKENS('UPPER lower dïäcríticš', 'My_Identity_Analyzer')",
                "expected_output": [["UPPER lower dïäcríticš"]]
            },
            "My_Delimiter_Analyzer": {
                "query": "RETURN TOKENS('some-delimited-words', 'My_Delimiter_Analyzer')",
                "expected_output": [["some-delimited-words"]]
            },
            "My_Stem_Analyzer": {
                "query": "RETURN TOKENS('databases', 'My_Stem_Analyzer')",
                "expected_output": [["databas"]]
            },
            "My_Norm_Analyzer": {
                "query": "RETURN TOKENS('UPPER lower dïäcríticš', 'My_Norm_Analyzer')",
                "expected_output": [["upper lower dïäcríticš"]]
            },
            "My_N-Gram_Analyzer": {
                "query": "RETURN TOKENS('foobar', 'My_N-Gram_Analyzer')",
                "expected_output": [["^foo", "^foobar", "foobar$", "oob", "oba", "bar$"]]
            },
            "My_Text_Analyzer": {
                "query": "RETURN TOKENS('The quick brown fox jumps over the dogWithAVeryLongName', 'My_Text_Analyzer')",
                "expected_output": [["THE","QUI","QUIC","QUICK","BRO","BROW","BROWN","FOX","JUM","JUMP","JUMPS",
                                     "OVE","OVER","THE","DOG","DOGW","DOGWI","DOGWIT","DOGWITH",
                                     "DOGWITHA","DOGWITHAVERYLONGNAME"]]
            },
            "My_AQL_Analyzer": {
                "query": "RETURN TOKENS('UPPER lower dïäcríticš','My_AQL_Analyzer')",
                "expected_output": [[["oIAAAAAAAAAA","sIAAAAAAAA==","wIAAAAA=","0IAA"]]]
            },
            "My_Stopwords_Analyzer": {
                "query": "RETURN FLATTEN(TOKENS(SPLIT('the fox and the dog and a theater', ' '), 'My_Stopwords_Analyzer'))",
                "expected_output": [["fox", "dog", "a", "theater"]]
            },
            "My_Pipeline_Analyzer": {
                "query": "RETURN TOKENS('Quick brown foX', 'My_Pipeline_Analyzer')",
                "expected_output": [["^QUI","^QUICKBROWNFOX","QUICKBROWNFOX$","UIC","ICK","CK","KB","BR","BRO",
                                     "ROW","OWN","WN","NF","FO","FOX$"]]
            },

            # Add more analyzers and their queries and expected outputs here
        }.get(analyzer_name, {})

    def get_analyzer_query_311(self, analyzer_name):
        """get analyzer query based on the analyzer name"""
        return self.generate_analyzer_queries_311(analyzer_name).get("query")

    def get_analyzer_expected_output_311(self, analyzer_name):
        """Get analyzer query's expected output based on the analyzer name"""
        analyzer_data = self.generate_analyzer_queries_311(analyzer_name)
        if analyzer_data:
            expected_output = analyzer_data.get("expected_output")
            # Convert the expected output to a string using double quotes
            if isinstance(expected_output, list):
                return str(expected_output).replace("'", '"')
            return expected_output
        return None

    @staticmethod
    def generate_expected_properties_311(analyzer_name, ui_data_dir=None):
        """Define a method to generate expected text for a specific analyzer for == v311"""
        location = ui_data_dir / "ui_data" / "analyzer_page" / "610_model_cooking.bin"
        analyzers = { "My_Identity_Analyzer": """{
                "name": "_system::My_Identity_Analyzer",
                "type": "identity",
                "features": [
                    "frequency",
                    "position",
                    "norm"
                ],
                "properties": {}
            }""",
                      "My_Delimiter_Analyzer": """{
                  "name": "_system::My_Delimiter_Analyzer",
                  "type": "delimiter",
                  "features": [
                    "frequency",
                    "position",
                    "norm"
                  ],
                  "properties": {
                    "delimiter": "_"
                  }
                }""",
                      "My_Stem_Analyzer": """{
                  "name": "_system::My_Stem_Analyzer",
                  "type": "stem",
                  "features": [
                    "frequency",
                    "position",
                    "norm"
                  ],
                  "properties": {
                    "locale": "en"
                  }
                }""",
                      "My_Norm_Analyzer": """{
                  "name": "_system::My_Norm_Analyzer",
                  "type": "norm",
                  "features": [
                    "frequency",
                    "position",
                    "norm"
                  ],
                  "properties": {
                    "locale": "en_US",
                    "case": "lower",
                    "accent": true
                  }
                }""",
                      "My_N-Gram_Analyzer": """{
                  "name": "_system::My_N-Gram_Analyzer",
                  "type": "ngram",
                  "features": [
                    "frequency",
                    "position",
                    "norm"
                  ],
                  "properties": {
                    "min": 3,
                    "max": 3,
                    "preserveOriginal": true,
                    "streamType": "utf8",
                    "startMarker": "^",
                    "endMarker": "$"
                  }
                }""",
                      "My_Text_Analyzer": """{
                  "name": "_system::My_Text_Analyzer",
                  "type": "text",
                  "features": [
                    "frequency",
                    "position",
                    "norm"
                  ],
                  "properties": {
                    "locale": "en_US",
                    "case": "upper",
                    "stopwords":["dog","human","of","the","tree"],
                    "accent": true,
                    "stemming": true,
                    "edgeNgram": {
                      "min": 3,
                      "max": 8,
                      "preserveOriginal": true
                    }
                  }
                }""",
                      "My_AQL_Analyzer": """{
                  "name": "_system::My_AQL_Analyzer",
                  "type": "aql",
                  "features": [
                    "frequency",
                    "position",
                    "norm"
                  ],
                  "properties": {
                    "queryString": "RETURN SOUNDEX(@param)",
                    "collapsePositions": true,
                    "keepNull": true,
                    "batchSize": 10,
                    "memoryLimit": 1048576,
                    "returnType": "number"
                  }
                }""",
                      "My_Stopwords_Analyzer": """{
                  "name": "_system::My_Stopwords_Analyzer",
                  "type": "stopwords",
                  "features": [
                    "frequency",
                    "position",
                    "norm"
                  ],
                  "properties": {
                    "stopwords": [
                      "616e64",
                      "746865",
                      ""
                    ],
                    "hex": true
                  }
                }""",
                      "My_Collation_Analyzer": """{
                  "name": "_system::My_Collation_Analyzer",
                  "type": "collation",
                  "features": [
                    "frequency",
                    "position",
                    "norm"
                  ],
                  "properties": {
                    "locale": "en_US"
                  }
                }""",
                      "My_Segmentation_Alpha_Analyzer": """{
                  "name": "_system::My_Segmentation_Alpha_Analyzer",
                  "type": "segmentation",
                  "features": [
                    "frequency",
                    "position",
                    "norm"
                  ],
                  "properties": {
                    "case": "lower",
                    "break": "alpha"
                  }
                }""",
                      "My_Pipeline_Analyzer": """{
                  "name": "_system::My_Pipeline_Analyzer",
                  "type": "pipeline",
                  "features": [
                    "frequency",
                    "position",
                    "norm"
                  ],
                  "properties": {
                    "pipeline": [
                      {
                        "type": "norm",
                        "properties": {
                          "locale": "en_US",
                          "case": "upper",
                          "accent": true
                        }
                      },
                      {"type":"ngram","properties":{"min":3,"max":3,"preserveOriginal":true,
                      "streamType":"utf8","startMarker":"^","endMarker":"$"}}
                    ]
                  }
                }""",
                      "My_GeoJSON_Analyzer": """{
                  "name": "_system::My_GeoJSON_Analyzer",
                  "type": "geojson",
                  "features": [
                    "frequency",
                    "position",
                    "norm"
                  ],
                  "properties": {
                    "options": {
                      "maxCells": 20,
                      "minLevel": 10,
                      "maxLevel": 30
                    },
                    "type":"shape","legacy":false}
                }""",
                      "My_GeoPoint_Analyzer": """{
                  "name": "_system::My_GeoPoint_Analyzer",
                  "type": "geopoint",
                  "features": [
                    "frequency",
                    "position",
                    "norm"
                  ],
                  "properties": {
                    "options": {
                      "maxCells": 20,
                      "minLevel": 4,
                      "maxLevel": 23
                    },
                    "latitude": ["40","78"],
                    "longitude": ["-73","97"]
                  }
                }
                """,
                      "My_GeoS2_Analyzer": """{
                      "name": "_system::My_GeoS2_Analyzer",
                      "type": "geo_s2",
                      "features": [
                        "frequency",
                        "position",
                        "norm"
                      ],
                      "properties": {
                        "options": {
                          "maxCells": 20,
                          "minLevel": 4,
                          "maxLevel": 23
                        },
                        "type": "point",
                        "format": "s2Point"
                      }
                    }""",
                      "My_Minhash_Analyzer": """{
                  "name": "_system::My_Minhash_Analyzer",
                  "type": "minhash",
                  "features": [
                    "frequency",
                    "position",
                    "norm"
                  ],
                  "properties": {
                    "numHashes": 10,
                    "analyzer": {
                      "type": "delimiter",
                      "properties": {
                        "delimiter": "#"
                      }
                    }
                  }
                }""",
                      "My_MultiDelimiter_Analyzer": """{
                  "name": "_system::My_MultiDelimiter_Analyzer",
                  "type": "multi_delimiter",
                  "features": [
                    "frequency",
                    "position",
                    "norm"
                  ],
                  "properties": {
                    "delimiters": [
                      ":",
                      ";",
                      ",",
                      ".",
                      "/",
                      "ß",
                      "Û",
                      "⚽"
                    ]
                  }
                }""",
                      "My_WildCard_Analyzer":"""
                {
                  "name": "_system::My_WildCard_Analyzer",
                  "type": "wildcard",
                  "features": [
                    "frequency",
                    "position",
                    "norm"
                  ],
                  "properties": {
                    "ngramSize": 4,
                    "analyzer": {
                      "type": "multi_delimiter",
                      "properties": {
                        "delimiters": [
                          ",",
                          ".",
                          ":",
                          ";",
                          "!",
                          "?",
                          "["
                        ]
                      }
                    }
                  }
                }""",
                      "My_Nearest_Neighbor_Analyzer": f"""
           {{
                "name": "_system::My_Nearest_Neighbor_Analyzer",
                "type": "nearest_neighbors",
                "features": [
                "frequency",
                "position",
                "norm"
                ],
                "properties": {{
                "model_location": "{str(location.absolute())}"
                "top_k": 2
                }}
                      }}""",
                      "My_Classification_Analyzer": f"""{{
                "name": "_system::My_Classification_Analyzer",
                "type": "classification",
                "features": [
                "frequency",
                "position",
                "norm"
                ],
                "properties": {{
                "model_location": "{str(location.absolute())}",
                "top_k": 2,
                "threshold": 1  
                }}
                }}
            """,
                     }
        return analyzers[analyzer_name]

    @staticmethod
    def generate_expected_properties_312(analyzer_name, ui_data_dir=None):
        """Define a method to generate expected text for a specific analyzer"""
        location = ui_data_dir / "ui_data" / "analyzer_page" / "610_model_cooking.bin"
        analyzers = {
            "My_Identity_Analyzer":  """{
                "name": "_system::My_Identity_Analyzer",
                "type": "identity",
                "properties": {},
                "features": [
                    "frequency",
                    "position",
                    "norm"
                ]
            }""",
            "My_Delimiter_Analyzer": """{
                  "name": "_system::My_Delimiter_Analyzer",
                  "type": "delimiter",
                  "properties": {
                    "delimiter": "_"
                  },
                  "features": [
                    "frequency",
                    "position",
                    "norm"
                  ]
                }""",
            "My_Stem_Analyzer": """{
                  "name": "_system::My_Stem_Analyzer",
                  "type": "stem",
                  "properties": {
                    "locale": "en"
                  },
                  "features": [
                    "frequency",
                    "position",
                    "norm"
                  ]
                }""",
            "My_Norm_Analyzer": """{
                  "name": "_system::My_Norm_Analyzer",
                  "type": "norm",
                  "properties": {
                    "locale": "en_US",
                    "case": "upper",
                    "accent": true
                  },
                  "features": [
                    "frequency",
                    "position",
                    "norm"
                  ]
                }""",
            "My_N-Gram_Analyzer": """{
                  "name": "_system::My_N-Gram_Analyzer",
                  "type": "ngram",
                  "properties": {
                    "min": 3,
                    "max": 3,
                    "preserveOriginal": true,
                    "streamType": "utf8",
                    "startMarker": "^",
                    "endMarker": "$"
                  },
                  "features": [
                    "frequency",
                    "position",
                    "norm"
                  ]
                }""",
            "My_Text_Analyzer":  """{
                  "name": "_system::My_Text_Analyzer",
                  "type": "text",
                  "properties": {
                    "locale": "en_US",
                    "case": "lower",
                    "accent": true,
                    "stemming": false,
                    "edgeNgram": {
                      "min": 3,
                      "max": 8,
                      "preserveOriginal": true
                    }
                  },
                  "features": [
                    "frequency",
                    "position",
                    "norm"
                  ]
                }""",
            "My_AQL_Analyzer": """{
                  "name": "_system::My_AQL_Analyzer",
                  "type": "aql",
                  "properties": {
                    "queryString": "RETURN SOUNDEX(@param)",
                    "collapsePositions": true,
                    "keepNull": true,
                    "batchSize": 10,
                    "memoryLimit": 1048576,
                    "returnType": "string"
                  },
                  "features": [
                    "frequency",
                    "position",
                    "norm"
                  ]
                }""",
            "My_Stopwords_Analyzer":  """{
                  "name": "_system::My_Stopwords_Analyzer",
                  "type": "stopwords",
                  "properties": {
                    "stopwords": [
                      "616e64",
                      "746865"
                    ],
                    "hex": true
                  },
                  "features": [
                    "frequency",
                    "position",
                    "norm"
                  ]
                }""",
            "My_Collation_Analyzer": """{
                  "name": "_system::My_Collation_Analyzer",
                  "type": "collation",
                  "properties": {
                    "locale": "en_US"
                  },
                  "features": [
                    "frequency",
                    "position",
                    "norm"
                  ]
                }""",
            "My_Segmentation_Alpha_Analyzer": """{
                  "name": "_system::My_Segmentation_Alpha_Analyzer",
                  "type": "segmentation",
                  "properties": {
                    "case": "lower",
                    "break": "alpha"
                  },
                  "features": [
                    "frequency",
                    "position",
                    "norm"
                  ]
                }""",
            "My_Pipeline_Analyzer": """{
                  "name": "_system::My_Pipeline_Analyzer",
                  "type": "pipeline",
                  "properties": {
                    "pipeline": [
                      {
                        "type": "norm",
                        "properties": {
                          "locale": "en_US",
                          "case": "upper",
                          "accent": true
                        }
                      }
                    ]
                  },
                  "features": [
                    "frequency",
                    "position",
                    "norm"
                  ]
                }""",
            "My_GeoJSON_Analyzer": """{
                  "name": "_system::My_GeoJSON_Analyzer",
                  "type": "geojson",
                  "properties": {
                    "options": {
                      "maxCells": 20,
                      "minLevel": 10,
                      "maxLevel": 30
                    },
                    "type": "point",
                    "legacy": false
                  },
                  "features": [
                    "frequency",
                    "position",
                    "norm"
                  ]
                }""",
            "My_GeoPoint_Analyzer": """{
                  "name": "_system::My_GeoPoint_Analyzer",
                  "type": "geopoint",
                  "properties": {
                    "options": {
                      "maxCells": 20,
                      "minLevel": 4,
                      "maxLevel": 23
                    },
                    "latitude": [
                      "40.78"
                    ],
                    "longitude": [
                      "-73.97"
                    ]
                  },
                  "features": [
                    "frequency",
                    "position",
                    "norm"
                  ]
                }
                """,
            "My_GeoS2_Analyzer": """{
                  "name": "_system::My_GeoS2_Analyzer",
                  "type": "geo_s2",
                  "properties": {
                    "options": {
                      "maxCells": 20,
                      "minLevel": 4,
                      "maxLevel": 23
                    },
                    "type": "centroid",
                    "format": "latLngInt"
                  },
                  "features": [
                    "frequency",
                    "position",
                    "norm"
                  ]
                }""",
            "My_Minhash_Analyzer": """{
                  "name": "_system::My_Minhash_Analyzer",
                  "type": "minhash",
                  "properties": {
                    "numHashes": 10,
                    "analyzer": {
                      "type": "delimiter",
                      "properties": {
                        "delimiter": "#"
                      }
                    }
                  },
                  "features": [
                    "frequency",
                    "position",
                    "norm"
                  ]
                }""",
            "My_MultiDelimiter_Analyzer": """{
                  "name": "_system::My_MultiDelimiter_Analyzer",
                  "type": "multi_delimiter",
                  "properties": {
                    "delimiters": [
                      ":",
                      ";",
                      ",",
                      ".",
                      "/",
                      "ß",
                      "Û",
                      "⚽"
                    ]
                  },
                  "features": [
                    "frequency",
                    "position",
                    "norm"
                  ]
                }""",
            "My_WildCard_Analyzer": """
                {
                  "name": "_system::My_WildCard_Analyzer",
                  "type": "wildcard",
                  "properties": {
                    "ngramSize": 4,
                    "analyzer": {
                      "type": "multi_delimiter",
                      "properties": {
                        "delimiters": [
                          ",",
                          ".",
                          ":",
                          ";",
                          "!",
                          "?",
                          "["
                        ]
                      }
                    }
                  },
                  "features": [
                    "frequency",
                    "position",
                    "norm"
                  ]
                }""",
            "My_Nearest_Neighbor_Analyzer": f"""
                {{
                "name": "_system::My_Nearest_Neighbor_Analyzer",
                "type": "nearest_neighbors",
                "properties": {{
                "model_location": "{str(location.absolute())}",
                "top_k": 2
                }},
                "features": [
                "frequency",
                "position",
                "norm"
                ]
                }}
        """,
            "My_Classification_Analyzer": f"""{{
                "name": "_system::My_Classification_Analyzer",
                "type": "classification",
                "properties": {{
                f"model_location": "{str(location.absolute())}",
                "top_k": 2,
                "threshold": 1
                }},
                "features": [
                "frequency",
                "position",
                "norm"
                ]
            }}"""
        }
        return analyzers[analyzer_name]


    def creating_all_supported_analyzer(self, enterprise, model_location=None, analyzer_set=1):
        """This method will create all the supported version-specific analyzers"""
        if analyzer_set == 1:
            decode_analyzers = {
                "My_Identity_Analyzer": (0, None, False),
                "My_Delimiter_Analyzer": (0, None, False),
                "My_Stem_Analyzer": (0, None, False),
                "My_Norm_Analyzer": (0, None, False),
                "My_N-Gram_Analyzer": (0, None, False),
                "My_Text_Analyzer": (0, None, False),
                "My_AQL_Analyzer": (0, None, False),
                "My_Stopwords_Analyzer": (0, None, False),
                "My_Collation_Analyzer": (0, None, False),
                "My_Segmentation_Alpha_Analyzer": (0, None, False)
            }
        else:
            decode_analyzers = {
                "My_Pipeline_Analyzer": (0, semver.VersionInfo.parse('3.10.0'), False),
                "My_GeoJSON_Analyzer": (0, semver.VersionInfo.parse('3.10.0'), False),
                "My_GeoPoint_Analyzer": (0, semver.VersionInfo.parse('3.10.0'), False),
                "My_MultiDelimiter_Analyzer": (0, semver.VersionInfo.parse('3.11.99'), False),
                "My_WildCard_Analyzer": (0, semver.VersionInfo.parse('3.11.99'), False),
                "My_Minhash_Analyzer": (0, semver.VersionInfo.parse('3.11.99'),
                                        not (enterprise and self.version_is_newer_than('3.11.99'))),
                "My_Nearest_Neighbor_Analyzer": (1 if enterprise else 0, semver.VersionInfo.parse('3.10.0'),
                                                 not enterprise),
                "My_Classification_Analyzer": (1 if enterprise else 0, semver.VersionInfo.parse('3.10.0'),
                                               not enterprise),
                "My_GeoS2_Analyzer": (0, None, not enterprise)
            }

        # Loop through each analyzer in the dictionary
        for analyzer_name, config in decode_analyzers.items():
            # Retrieve parameters, version requirement, and skip condition for the current analyzer
            num_params, version_requirement, skip_condition = config
            # Check if the analyzer should be skipped
            if skip_condition:
                self.tprint(f'Skipping {analyzer_name} creation\n')
                continue
            # Check if the current package version meets the version requirement
            if version_requirement is None or self.version_is_newer_than(str(version_requirement)):
                self.tprint(f'Adding {analyzer_name} analyzer\n')
                # Create the analyzer based on the number of parameters required
                if num_params == 0:
                    self.add_new_analyzer(analyzer_name)
                elif num_params == 1:
                    self.add_new_analyzer(analyzer_name, model_location)
                else:
                    # Additional handling can be added for analyzers with more parameters if needed in the future
                    pass

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
                self.tprint(f"Searching for {expected_msg} \n")
                assert expected_msg == de_sitem, f"Expected {expected_msg} but got {de_sitem}"
                self.tprint(f"Found {expected_msg} \n")
            elif value == "geo":
                geo = "//td[@class='arango-table-td table-cell2' and text()='GeoJSON']"
                geo_sitem = self.locator_finder_by_xpath(geo).text
                expected_msg = "GeoJSON"
                self.tprint(f"Searching for {expected_msg} \n")
                assert expected_msg == geo_sitem, f"Expected {expected_msg} but got {geo_sitem}"
                self.tprint(f"Found {expected_msg} \n")
            else:
                self.tprint("You did not put any search keyword. Please check manually! \n")

            time.sleep(2)
        except Exception as ex:
            raise Exception("Error occurred!! required manual inspection.\n") from ex

    def test_analyzer_expected_error(self, name):
        # pylint: disable=too-many-locals disable=too-many-statements
        """testing analyzers negative scenarios"""
        index = self.index
        if name == "Identity_Analyzer":
            index = 0
        elif name == "Stem_Analyzer":
            index = 2
        elif name == "N_Gram_Analyzer":
            index = 4
        elif name == "AQL_Analyzer":
            index = 6
        else:
            self.tprint("Something went wrong\n")

        self.select_analyzers_page()
        self.webdriver.refresh()

        try:
            self.tprint("Selecting add new analyzer button \n")
            add_analyzer = self.add_new_analyzer_btn
            add_analyzer_sitem = self.locator_finder_by_xpath(add_analyzer)
            add_analyzer_sitem.click()
            time.sleep(2)

            self.tprint(f'checking {name} started \n')
            # common attributes for all the analyzers
            analyzer_name = '//div[label[text()="Analyzer Name"]]/input[not(@disabled)]'
            analyzer_type = '//div[label[text()="Analyzer Type"]]/select[not(@disabled)]'
            analyzer_name_error_id = "//div[@class='noty_body']"

            self.tprint("Selecting analyzer type \n")
            self.locator_finder_by_select_using_xpath(analyzer_type, index)
            time.sleep(2)

            if index == 0:
                self.tprint(f"Expected error scenario for the {name} Started \n")
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

                # method template (self, error_input, print_statement, error_message, locators_id, error_message_id)
                self.check_expected_error_messages_for_analyzer(
                    analyzer_name_error_input,
                    analyzer_name_print_statement,
                    analyzer_name_error_message,
                    analyzer_name,
                    analyzer_name_error_id,
                )

            # ------------------------------------Stem analyzer's Locale value test------------------------------------
            if index == 2:
                self.tprint(f"Expected error scenario for the {name} Started \n")
                # filling out the name placeholder first
                stem_sitem = self.locator_finder_by_xpath(analyzer_name)
                stem_sitem.click()
                stem_sitem.clear()
                stem_sitem.send_keys(name)

                analyzer_name_error_input = ["aaaaaaaaaa12"]
                analyzer_name_print_statement = [f'Checking {name} with input "aaaaaaaaaa12"']
                analyzer_name_error_message = [
                    "Failure: Got unexpected server response: Failure initializing an "
                    "arangosearch analyzer instance for name '_system::Stem_Analyzer' type "
                    "'stem'. Properties '{ \"locale\" : \"aaaaaaaaaa12\" }' was rejected by "
                    "analyzer. Please check documentation for corresponding analyzer type."
                ]

                # for stem analyzer locale placeholder
                local_placeholder = '//div[label[text()="Locale"]]//input[not(@disabled)]'
                # method template (self, error_input, print_statement, error_message, locators_id, error_message_id, div_id)
                self.check_expected_error_messages_for_analyzer(
                    analyzer_name_error_input,
                    analyzer_name_print_statement,
                    analyzer_name_error_message,
                    local_placeholder,
                    analyzer_name_error_id,
                )

            # ------------------------------------Stem analyzer's Locale value test------------------------------------
            if index == 4:
                self.tprint(f"Expected error scenario for the {name} Started \n")
                # filling out the name placeholder first
                ngram_analyzer_sitem = self.locator_finder_by_xpath(analyzer_name)
                ngram_analyzer_sitem.click()
                ngram_analyzer_sitem.clear()
                ngram_analyzer_sitem.send_keys(name)

                # fill up the max_ngram value beforehand
                max_ngram_length = '//div[label[text()="Maximum N-Gram Length"]]//input[not(@disabled)]'
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
                    "name '_system::N_Gram_Analyzer' type 'ngram'. Properties "
                    '\'{ "min" : -1, "max" : 4, "preserveOriginal" : false }\' '
                    "was rejected by analyzer. Please check documentation for "
                    "corresponding analyzer type.",
                    "Failure: Got unexpected server response: Failure initializing an "
                    "arangosearch analyzer instance for name '_system::N_Gram_Analyzer' type "
                    '\'ngram\'. Properties \'{ "min" : 99999999999999990000000, "max" : 4, '
                    '"preserveOriginal" : false }\' was rejected by analyzer. Please check '
                    "documentation for corresponding analyzer type.",
                ]

                # min _ngram_length for initiate the test
                min_ngram_length_id = '//div[label[text()="Minimum N-Gram Length"]]//input[not(@disabled)]'

                # method template (self, error_input, print_statement, error_message, locators_id, error_message_id, div_id)
                self.check_expected_error_messages_for_analyzer(
                    analyzer_name_error_input,
                    analyzer_name_print_statement,
                    analyzer_name_error_message,
                    min_ngram_length_id,
                    analyzer_name_error_id,
                )

            # ---------------------------------------------AQL analyzer's---------------------------------------------
            if index == 6:
                self.tprint(f"Expected error scenario for the {name} Started \n")
                # filling out the name placeholder first
                aql_analyzer_sitem = self.locator_finder_by_xpath(analyzer_name)
                aql_analyzer_sitem.click()
                aql_analyzer_sitem.clear()
                aql_analyzer_sitem.send_keys(name)

                self.tprint(f"Selecting query string for {name} \n")
                query_string = '//div[label[text()="Query String"]]/textarea[not(@disabled)]'
                query_string_sitem = self.locator_finder_by_xpath(query_string)
                query_string_sitem.send_keys("FOR year IN 2010..2015 RETURN year")
                time.sleep(2)

                self.tprint(f"Selecting memory limit for {name} \n")
                memory_limit = '//div[label[text()="Memory Limit"]]//input[not(@disabled)]'
                memory_limit_sitem = self.locator_finder_by_xpath(memory_limit)
                memory_limit_sitem.click()
                memory_limit_sitem.clear()
                memory_limit_sitem.send_keys("200")
                time.sleep(2)

                self.tprint(f"Selecting greater number for batch size {name} \n")

                analyzer_name_error_input = ["1001", "-1"]
                analyzer_name_print_statement = [f'Checking {name} with input "1001"', f'Checking {name} with input "-1"']
                analyzer_name_error_message = [
                    "Failure: Got unexpected server response: Failure initializing an "
                    "arangosearch analyzer instance for name '_system::AQL_Analyzer' type "
                    "'aql'. Properties '{ \"queryString\" : \"FOR year IN 2010..2015 RETURN "
                    'year", "memoryLimit" : 200, "batchSize" : 1001 }\' was rejected by '
                    "analyzer. Please check documentation for corresponding analyzer type.",
                    "Failure: Got unexpected server response: Failure initializing an "
                    "arangosearch analyzer instance for name '_system::AQL_Analyzer' type "
                    "'aql'. Properties '{ \"queryString\" : \"FOR year IN 2010..2015 RETURN "
                    'year", "memoryLimit" : 200, "batchSize" : -1 }\' was rejected by '
                    "analyzer. Please check documentation for corresponding analyzer type.",
                ]

                # for AQL analyzer batch size placeholder
                batch_size = '//div[label[text()="Batch Size"]]//input[not(@disabled)]'

                # method template (self, error_input, print_statement, error_message, locators_id, error_message_id)
                self.check_expected_error_messages_for_analyzer(
                    analyzer_name_error_input,
                    analyzer_name_print_statement,
                    analyzer_name_error_message,
                    batch_size,
                    analyzer_name_error_id,
                )

            self.tprint(f"Closing the {name} check \n")
            if self.version_is_newer_than('3.11.0'):
                close_btn = '//*[@id="chakra-modal-2"]/footer/button[1]'
            else:
                close_btn = '//*[@id="modal-content-add-analyzer"]/div[3]/button[1]'
            close_btn_sitem = self.locator_finder_by_xpath(close_btn)
            close_btn_sitem.click()
            time.sleep(2)

            self.tprint(f"Expected error scenario for the {name} Completed \n")
        except Exception:
            self.tprint('Info: Error occured during checking expected error!')

    def analyzer_expected_error_check(self):
        """This will call all the error scenario methods"""
        if self.version_is_newer_than('3.11.0'):
            self.tprint('Skipped \n')
        else:
            self.tprint('Checking negative scenario for the identity analyzers name \n')
            self.test_analyzer_expected_error('Identity_Analyzer')
            self.tprint('Checking negative scenario for the stem analyzers locale value \n')
            self.test_analyzer_expected_error('Stem_Analyzer')
            self.tprint('Checking negative scenario for the stem analyzers locale value \n')
            self.test_analyzer_expected_error('N_Gram_Analyzer')
            self.tprint('Checking negative scenario for the AQL analyzers \n')
            self.test_analyzer_expected_error('AQL_Analyzer')


    def checking_search_filter(self):
        """This method will check analyzer's search filter option"""
        if self.version_is_newer_than('3.11.0'):
            self.tprint("Skipped \n")
        else:
            self.tprint('Checking analyzer search filter options started \n')
            self.checking_search_filter_option('de')
            self.checking_search_filter_option('geo', False)  # false indicating builtIn option will be disabled
            self.tprint('Checking analyzer search filter options completed \n')

    def delete_analyzer(self, analyzer_name):
        """Deleting all the analyzer using their ID"""
        self.select_analyzers_page()
        self.webdriver.refresh()

        try:
            self.tprint(f'Deletion of {analyzer_name} started \n')
            if self.version_is_newer_than('3.11.99'):
                analyzer = f"//*[text()='_system::{analyzer_name}']"
                time.sleep(5)
                analyzer_sitem = self.locator_finder_by_xpath(analyzer)
                if analyzer_sitem is None:
                    self.tprint(f'This {analyzer_name} has never been created \n')
                else:
                    analyzer_sitem.click()
                    time.sleep(5)

                    select_delete_btn = "(//button[normalize-space()='Delete'])[1]"
                    select_delete_btn_sitem = self.locator_finder_by_xpath(select_delete_btn)
                    select_delete_btn_sitem.click()
                    time.sleep(5)

                    delete_confirm_btn = '(//button[text()="Delete"])[2]'
                    delete_confirm_btn_sitem = self.locator_finder_by_xpath(delete_confirm_btn)
                    delete_confirm_btn_sitem.click()
                    time.sleep(2)

            else:
                # search for specific analyzer according to their name
                search_filter = '//*[@id="filterInput"]'
                search_filter_sitem = self.locator_finder_by_xpath(search_filter)
                search_filter_sitem.click()
                search_filter_sitem.send_keys(analyzer_name)
                time.sleep(2)

                analyzer_delete_icon = '//*[@id="analyzersContent"]/div/div/table/tbody/tr/td[4]/button[2]/i'
                analyzer_delete_icon_sitem = self.locator_finder_by_xpath(analyzer_delete_icon)
                analyzer_delete_icon_sitem.click()
                time.sleep(2)

                # force_delete = '//*[@id="force-delete"]'
                # force_delete.sitem = self.locator_finder_by_xpath(force_delete)
                # force_delete.sitem.click()

                # delete_btn = f'//*[@id="modal-content-delete-_system::{analyzer_name}"]/div[3]/button[2]'
                delete_btn = "(//button[normalize-space()='Delete'])[1]"
                delete_btn_sitem = self.locator_finder_by_xpath(delete_btn)
                if delete_btn_sitem is None:
                    self.tprint("This analyzer has never been created or already been deleted! \n")
                else:
                    delete_btn_sitem.click()
                    time.sleep(8)
                self.tprint(f'Deletion of {analyzer_name} completed \n')
        except TimeoutException:
            self.tprint('TimeoutException occurred! \n')
            self.tprint('Info: Analyzer has already been deleted or never created. \n')
        except Exception as ex:
            traceback.print_exc()
            raise Exception('Critical Error occurred and need manual inspection!! \n') from ex

    def deleting_all_created_analyzers(self, analyzer_set=1):
        """Deleting all the created analyzers"""
        if analyzer_set == 1:
            self.delete_analyzer('My_Identity_Analyzer')
            self.delete_analyzer('My_Delimiter_Analyzer')
            self.delete_analyzer('My_Stem_Analyzer')
            self.delete_analyzer('My_Norm_Analyzer')
            self.delete_analyzer('My_N-Gram_Analyzer')
            self.delete_analyzer('My_Text_Analyzer')
            self.delete_analyzer('My_AQL_Analyzer')
            self.delete_analyzer('My_Stopwords_Analyzer')
            self.delete_analyzer('My_Collation_Analyzer')
            self.delete_analyzer('My_Segmentation_Alpha_Analyzer')
        else:
            self.delete_analyzer('My_Pipeline_Analyzer')
            self.delete_analyzer('My_GeoJSON_Analyzer')
            self.delete_analyzer('My_GeoPoint_Analyzer')
            self.delete_analyzer('My_Nearest_Neighbor_Analyzer')
            self.delete_analyzer('My_Classification_Analyzer')
            self.delete_analyzer('My_GeoS2_Analyzer')
            if self.version_is_newer_than('3.11.99'):
                self.delete_analyzer('My_Minhash_Analyzer')
                self.delete_analyzer('My_MultiDelimiter_Analyzer')
                self.delete_analyzer('My_WildCard_Analyzer')
        self.tprint('All the created analyzers have been deleted \n')
