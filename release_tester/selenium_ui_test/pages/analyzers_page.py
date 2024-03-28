#!/usr/bin/env python3
""" analyzer page object """
import time
import traceback
import semver
from selenium_ui_test.pages.base_page import Keys
from selenium_ui_test.pages.navbar import NavigationBarPage
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
import pyperclip


class AnalyzerPage(NavigationBarPage):
    """ analyzer page object """
    # pylint: disable=too-many-instance-attributes
    def __init__(self, webdriver, cfg):
        super().__init__(webdriver, cfg)
        self.analyzers_page = "analyzers"
        self.in_built_analyzer = "icon_arangodb_settings2"
        self.add_new_analyzer_btn = '//*[@id="analyzersContent"]/div/div/div/div/button/i'

        self.close_analyzer_btn = "//button[text()='Close' and not(ancestor::div[contains(@style,'display:none')]) " \
                                  "and not(ancestor::div[contains(@style,'display: none')])] "
        self.index = 0
        self.package_version = self.current_package_version()

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
        if self.version_is_newer_than('3.11.99'):
            print("select_help_filter_btn test skipped \n")
        else:
            self.webdriver.refresh()
            print("Selecting Analyzers help filter button \n")
            help_filter = "//a[@href='#analyzers']//i[@class='fa fa-question-circle']"
            help_sitem = self.locator_finder_by_xpath(help_filter)
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
        built_in_sitem = self.locator_finder_by_xpath(built_in)
        built_in_sitem.click()
        time.sleep(2)

    def select_built_in_analyzers_close(self):
        """Checking in-built analyzers list and description"""
        built_in = "//*[contains(text(),'Built-in')]"
        built_in_sitem = self.locator_finder_by_xpath(built_in)
        built_in_sitem.click()
        time.sleep(2)

        show_built_in_analyzers = "icon_arangodb_settings2"
        show_built_in_analyzers_sitem = self.locator_finder_by_class(show_built_in_analyzers)
        show_built_in_analyzers_sitem.click()
        time.sleep(2)


    def select_analyzer_to_check(self, analyzer_name, locators):
        """Checking in-built analyzers one by one"""
        print(f"Checking {analyzer_name} analyzer\n")

        print('Selecting analyzer from the in-built analyzers list \n')
        self.locator_finder_by_xpath(locators).click()
        time.sleep(2)

        switch_view_template_str = lambda id_name: f"//div[@id='modal-content-view-{id_name}']/child::div//div/div[2]/button"
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
        print('Switch to Code view \n')
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

        print('Closing the analyzer \n')
        close_sitem = self.locator_finder_by_xpath(self.close_analyzer_btn)
        close_sitem.click()
        time.sleep(2)
    

    def checking_analyzer_page_transition(self, keyword):
        """This methdo will check page transition error for BTS-902"""
        """
        To reproduce the issue we need to follow steps given below:
        Login to the web UI
        Click in the menu on “Analyzers”
        Click in the menu on “Collections”
        Click in the menu on “Analyzers” again
        Click the search icon from the search/filter box if it takes 
        to the collection page then it's an error.
        """

        if self.version_is_newer_than('3.11.99'):
            print("checking_analyzer_page_transition test skipped \n")
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
            print("Selecting add new analyzer button \n")
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
            print("select_help_filter_btn test skipped \n")
        else:
            print('Showing in-built Analyzers list \n')
            self.select_built_in_analyzers_open()
            
            for analyzer in built_in_analyzers:
                print(f'Checking in-built {analyzer} analyzer \n')
                xpath = f'//tr/td[text()="{analyzer}"]/following-sibling::td[2]/button'
                self.select_analyzer_to_check(analyzer, xpath)
            
            print('Hiding in-built Analyzers list \n')
            self.select_built_in_analyzers_close()

    def get_analyzer_index(self, name):
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
            "My_Nearest_Neighbor_Analyzer": 10 if self.version_is_newer_than('3.9.99') else 9,
            "My_Classification_Analyzer": 11 if self.version_is_newer_than('3.9.99') else 9,
            "My_Pipeline_Analyzer": 12 if self.version_is_newer_than('3.9.99') else 10,
            "My_GeoJSON_Analyzer": 13 if self.version_is_newer_than('3.9.99') else 11,
            "My_GeoPoint_Analyzer": 14 if self.version_is_newer_than('3.9.99') else 12,
            "My_GeoS2_Analyzer": 15 if self.version_is_newer_than('3.9.99') else 13,
            "My_Minhash_Analyzer": 16 if self.version_is_newer_than('3.9.99') else 14,
            "My_MultiDelimiter_Analyzer": 17 if self.version_is_newer_than('3.9.99') else 15,
            "My_WildCard_Analyzer": 18 if self.version_is_newer_than('3.9.99') else 16
        }
        return analyzer_lookup.get(name, -1)  # Return -1 if the analyzer name is not found


    def add_new_analyzer(self, name, ui_data_dir=None):
        """Adding analyzer type delimiter with necessary features"""
        # pylint: disable=too-many-locals disable=too-many-branches disable=too-many-statements
        index = self.get_analyzer_index(name)
        if index == -1:
            print(f"Analyzer '{name}' not found in the lookup table.")
            return
        
        self.select_analyzers_page()
        self.webdriver.refresh()

        if self.version_is_newer_than('3.11.99'):
            add_new_analyzer_btn = '//*[@id="content-react"]/div/div[1]/span/button'
        else:
            add_new_analyzer_btn = '//*[@id="analyzersContent"]/div/div/div/div/button/i'

        add_analyzer_sitem = self.locator_finder_by_xpath(add_new_analyzer_btn)
        add_analyzer_sitem.click()
        time.sleep(2)

        print(f'Creating {name} started \n')
        # common attributes for all the analyzer
        if self.version_is_newer_than('3.11.99'):
            analyzer_name = "(//input[@id='name'])[1]"
            analyzer_type = "(//*[name()='svg'][@class='css-8mmkcg'])[2]"
            frequency = '//*[@id="chakra-modal--body-7"]/div/div[2]/div/label[1]/span[1]/span'
            norm = '//*[@id="chakra-modal--body-7"]/div/div[2]/div/label[2]/span[1]/span'
            position = '//*[@id="chakra-modal--body-7"]/div/div[2]/div/label[3]/span[1]'
            local_placeholder = "(//input[@id='properties.locale'])[1]"
            case_placeholder = "(//label[normalize-space()='Case'])[1]"
        else:
            analyzer_name = '//div[label[text()="Analyzer Name"]]/input[not(@disabled)]'
            analyzer_type = '//div[label[text()="Analyzer Type"]]/select[not(@disabled)]'
            frequency = '//div[label[text()="Frequency"]]/input[not(@disabled)]'
            norm = '//div[label[text()="Norm"]]/input[not(@disabled)]'
            position = '//div[label[text()="Position"]]/input[not(@disabled)]'
            # switch_form_btn = "//*[text()='Switch to form view']"
            # switch_view_btn = '//*[@id="chakra-modal--header-2"]/div/div[3]/button' #todo 3.11
            local_placeholder = '//div[label[text()="Locale"]]//input[not(@disabled)]'
            case_placeholder = '//div[label[text()="Case"]]//select[not(@disabled)]'

        analyzer_name_sitem = self.locator_finder_by_xpath(analyzer_name)
        analyzer_name_sitem.click()
        analyzer_name_sitem.clear()
        analyzer_name_sitem.send_keys(name)
        time.sleep(2)

        print('Selecting analyzer type \n')
        if self.version_is_newer_than('3.11.99'):
            analyzer_type_sitem = self.locator_finder_by_xpath(analyzer_type)
            analyzer_type_sitem.click()
            time.sleep(2)
            # this will simulate down arrow key according to its index position
            print("Analyzer's position on the list: ", index)
            for _ in range(index):
                self.send_key_action(Keys.ARROW_DOWN)
            self.send_key_action(Keys.ENTER)
            time.sleep(1)
        else:
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
        if name == "My_Delimiter_Analyzer":
            delimiter = '//div[label[text()="Delimiter (characters to split on)"]]//input[not(@disabled)]'
            value = "_"
            delimiter_sitem = self.locator_finder_by_xpath(delimiter)
            delimiter_sitem.click()
            delimiter_sitem.clear()
            delimiter_sitem.send_keys(value)
        # for stem
        elif name == "My_Stem_Analyzer":
            value = 'en_US.utf-8'
            locale_sitem = self.locator_finder_by_xpath(local_placeholder)
            locale_sitem.click()
            locale_sitem.clear()
            locale_sitem.send_keys(value)
        # for norm
        elif name == "My_Norm_Analyzer":
            value = 'en_US.utf-8'
            locale_sitem = self.locator_finder_by_xpath(local_placeholder)
            locale_sitem.click()
            locale_sitem.clear()
            locale_sitem.send_keys(value)

            print('Selecting case for norm analyzer using index value \n')
            if self.version_is_newer_than('3.11.99'):
                case_sitem = self.locator_finder_by_xpath(case_placeholder)
                case_sitem.click()
                self.send_key_action(Keys.ARROW_DOWN)
                self.send_key_action(Keys.ENTER)
            else:
                self.locator_finder_by_select_using_xpath(case_placeholder, 0)

            print('Selecting accent for norm analyzer \n')
            if self.version_is_newer_than('3.11.99'):
                accent = '//*[@id="chakra-modal--body-7"]/div/div[3]/div/div[3]/div/div/label[2]/span/span'
            else:
                accent = '//div[label[text()="Accent"]]//input[not(@disabled)]'

            accent_sitem = self.locator_finder_by_xpath(accent)
            accent_sitem.click()
            time.sleep(2)

        # for N-Gram
        elif name == "My_N-Gram_Analyzer":
            print(f'Adding minimum n-gram length for {name} \n')
            min_length = '//div[label[text()="Minimum N-Gram Length"]]//input[not(@disabled)]'
            min_length_sitem = self.locator_finder_by_xpath(min_length)
            min_length_sitem.click()
            min_length_sitem.clear()
            min_length_sitem.send_keys('2')
            time.sleep(2)

            print(f'Adding maximum n-gram length for {name} \n')
            max_length = '//div[label[text()="Maximum N-Gram Length"]]//input[not(@disabled)]'
            max_length_sitem = self.locator_finder_by_xpath(max_length)
            max_length_sitem.click()
            max_length_sitem.clear()
            max_length_sitem.send_keys('3')
            time.sleep(2)

            print(f'Preserve original value for {name}\n')
            if self.version_is_newer_than('3.11.99'):
                preserve = "(//span[@class='chakra-switch__thumb css-7roig'])[5]"
            else:
                preserve = '//div[label[text()="Preserve Original"]]//input[not(@disabled)]'

            preserve_sitem = self.locator_finder_by_xpath(preserve)
            preserve_sitem.click()
            time.sleep(2)

            print(f'Start marker value {name}\n')
            start_marker = '//div[label[text()="Start Marker"]]//input[not(@disabled)]'
            start_marker_sitem = self.locator_finder_by_xpath(start_marker)
            start_marker_sitem.click()
            start_marker_sitem.clear()
            start_marker_sitem.send_keys('^')
            time.sleep(2)

            print(f'End marker value for {name} \n')
            end_marker = '//div[label[text()="End Marker"]]//input[not(@disabled)]'
            end_marker_sitem = self.locator_finder_by_xpath(end_marker)
            end_marker_sitem.click()
            end_marker_sitem.clear()
            end_marker_sitem.send_keys('$')
            time.sleep(2)

            print(f'Stream type selection using index value for {name}\n')
            if self.version_is_newer_than('3.11.99'):
                stream_type = "(//label[normalize-space()='Stream Type'])[1]"
                stream_type_sitem = self.locator_finder_by_xpath(stream_type)
                stream_type_sitem.click()
                self.send_key_action(Keys.ARROW_DOWN)
                self.send_key_action(Keys.ARROW_DOWN)
                self.send_key_action(Keys.ENTER)
            else:
                stream_type = '//div[label[text()="Stream Type"]]//select[not(@disabled)]'
                self.locator_finder_by_select_using_xpath(stream_type, 1)
            time.sleep(2)
        # for text
        elif name == "My_Text_Analyzer":
            value = 'en_US.utf-8'
            locale_sitem = self.locator_finder_by_xpath(local_placeholder)
            locale_sitem.click()
            locale_sitem.clear()
            locale_sitem.send_keys(value)
            time.sleep(2)

            # need to properly define the path of the stopwords
            # print('Selecting path for stopwords \n')
            # stopwords_path = '//div[label[text()="Stopwords Path"]]//input[not(@disabled)]'
            # stopwords_path_sitem = BaseSelenium.locator_finder_by_xpath(stopwords_path)
            # stopwords_path_sitem.click()
            # stopwords_path_sitem.clear()
            # stopwords_path_sitem.send_keys('/home/username/Desktop/')

            print(f'Selecting stopwords for the {name} \n')
            if self.version_is_newer_than('3.11.99'):
                print("skipped! \n")
            else:
                stopwords = '//div[label[text()="Stopwords (One per line)"]]//textarea[not(@disabled)]'
                stopwords_sitem = self.locator_finder_by_xpath(stopwords)
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

            print(f'Selecting case for the analyzer from the dropdown menu for {name} \n')
            if self.version_is_newer_than('3.11.99'):
                case = "(//label[normalize-space()='Case'])[1]"
                case_sitem = self.locator_finder_by_xpath(case)
                case_sitem.click()
                self.send_key_action(Keys.ARROW_DOWN)
                self.send_key_action(Keys.TAB)
            else:
                self.locator_finder_by_select_using_xpath(case_placeholder, 1)

            print('Selecting stem for the analyzer \n')
            if self.version_is_newer_than('3.11.99'):
                stem = '//*[@id="chakra-modal--body-7"]/div/div[3]/div/div[5]/div/div/label[2]/span/span'
            else:
                stem = '//div[label[text()="Stemming"]]//input[not(@disabled)]'
            stem_sitem = self.locator_finder_by_xpath(stem)
            stem_sitem.click()
            time.sleep(2)

            print('Selecting accent for the analyzer \n')
            if self.version_is_newer_than('3.11.99'):
                accent = '//*[@id="chakra-modal--body-7"]/div/div[3]/div/div[6]/div/div/label[2]/span/span'
            else:
                accent = '//div[label[text()="Accent"]]//input[not(@disabled)]'
            accent_sitem = self.locator_finder_by_xpath(accent)
            accent_sitem.click()
            time.sleep(2)

            print(f'Selecting minimum N-Gram length for {name} \n')
            ngram_length_min = '//div[label[text()="Minimum N-Gram Length"]]//input[not(@disabled)]'
            ngram_length_min_sitem = self.locator_finder_by_xpath(ngram_length_min)
            ngram_length_min_sitem.click()
            ngram_length_min_sitem.send_keys('2')
            time.sleep(2)

            print(f'Selecting maximum N-Gram length for {name} \n')
            ngram_length_max_length = '//div[label[text()="Maximum N-Gram Length"]]//input[not(@disabled)]'
            ngram_length_max_length_sitem = self.locator_finder_by_xpath(ngram_length_max_length)
            ngram_length_max_length_sitem.click()
            ngram_length_max_length_sitem.send_keys('3')
            time.sleep(2)

            print(f'Selecting preserve original for {name} \n')
            if self.version_is_newer_than('3.11.99'):
                preserve = '//*[@id="chakra-modal--body-7"]/div/div[3]/div/div[9]/div/div/label[2]/span/span'
            else:
                preserve = '//div[label[text()="Preserve Original"]]//input[not(@disabled)]'
            preserve_sitem = self.locator_finder_by_xpath(preserve)
            preserve_sitem.click()
            if self.version_is_newer_than('3.11.99'):
                print("skipped")
            else:
                preserve_sitem.send_keys('3')
            time.sleep(2)
        # for AQL analyzer
        elif name == "My_AQL_Analyzer":
            print(f'Selecting query string for {name} \n')
            query_string = '//div[label[text()="Query String"]]/textarea[not(@disabled)]'
            query_string_sitem = self.locator_finder_by_xpath(query_string)
            query_string_sitem.send_keys('FOR year IN 2010..2015 RETURN year')
            time.sleep(2)

            print(f'Selecting batch size for {name} \n')
            batch_size = '//div[label[text()="Batch Size"]]//input[not(@disabled)]'
            batch_size_sitem = self.locator_finder_by_xpath(batch_size)
            batch_size_sitem.click()
            if self.version_is_newer_than('3.11.99'):
                self.send_key_action(Keys.BACKSPACE)
            else:
                batch_size_sitem.clear()
                batch_size_sitem.send_keys('100')
            time.sleep(2)

            print(f'Selecting memory limit for {name} \n')
            memory_limit = '//div[label[text()="Memory Limit"]]//input[not(@disabled)]'
            memory_limit_sitem = self.locator_finder_by_xpath(memory_limit)
            memory_limit_sitem.click()
            if self.version_is_newer_than('3.11.99'):
                self.send_key_action(Keys.BACKSPACE)
            else:
                memory_limit_sitem.clear()
                memory_limit_sitem.send_keys('200')
            time.sleep(2)

            print(f'Selecting collapse position for {name} \n')
            if self.version_is_newer_than('3.11.99'):
                collapse = '//*[@id="chakra-modal--body-7"]/div/div[3]/div/div[4]/div/div/label[2]/span/span'
            else:
                collapse = '//div[label[text()="Collapse Positions"]]//input[not(@disabled)]'
            collapse_sitem = self.locator_finder_by_xpath(collapse)
            collapse_sitem.click()
            time.sleep(2)

            print(f'Selecting keep null for {name} \n')
            if self.version_is_newer_than('3.11.99'):
                print('Skipped \n')
            else:
                keep_null = '//div[label[text()="Keep Null"]]//input[not(@disabled)]'
                keep_null_sitem = self.locator_finder_by_xpath(keep_null)
                keep_null_sitem.click()
            time.sleep(2)

            print(f'Selecting Return type for {name} \n')
            if self.version_is_newer_than('3.11.99'):
                return_type = "(//label[normalize-space()='Return Type'])[1]"
                return_type_sitem = self.locator_finder_by_xpath(return_type)
                return_type_sitem.click()
                self.send_key_action(Keys.ARROW_DOWN)
                self.send_key_action(Keys.ENTER)

            else:
                return_type = '//div[label[text()="Return Type"]]//select[not(@disabled)]'
                self.locator_finder_by_select_using_xpath(return_type, 1)
            time.sleep(2)
        # for stopwords
        elif name == "My_Stopwords_Analyzer":
            print(f'Selecting stopwords for {name} \n')
            if self.version_is_newer_than('3.11.99'):
                stopwords = '//*[@id="chakra-modal--body-7"]/div/div[3]/div/div[1]/div/div[1]/div[1]/div[2]'
                stopwords_sitem = self.locator_finder_by_xpath(stopwords)
                stopwords_sitem.click()
                self.send_key_action('616e64')
                self.send_key_action(Keys.ENTER)
            else:
                stopwords = '//div[label[text()="Stopwords (One per line)"]]//textarea[not(@disabled)]'
                stopwords_sitem = self.locator_finder_by_xpath(stopwords)
                stopwords_sitem.click()
                stopwords_sitem.clear()
                stopwords_sitem.send_keys('616e64')
                stopwords_sitem.send_keys(Keys.ENTER)
                time.sleep(1)
                stopwords_sitem.send_keys('746865')
                stopwords_sitem.send_keys(Keys.ENTER)
                time.sleep(1)

            print(f'Selecting hex value for {name} \n')
            if self.version_is_newer_than('3.11.99'):
                hex_value = '//*[@id="chakra-modal--body-7"]/div/div[3]/div/div[2]/div/div/label[2]/span/span'
            else:
                hex_value = '//div[label[text()="Hex"]]//input[not(@disabled)]'
            hex_sitem = self.locator_finder_by_xpath(hex_value)
            hex_sitem.click()
            time.sleep(2)

        # Collation
        elif name == "My_Collation_Analyzer":
            print(f'Selecting locale for {name} \n')
            value = 'en_US.utf-8'
            locale_sitem = self.locator_finder_by_xpath(local_placeholder)
            locale_sitem.click()
            locale_sitem.clear()
            locale_sitem.send_keys(value)
        # Segmentation alpha 
        elif name == "My_Segmentation_Alpha_Analyzer":
            print(f'Selecting segmentation break as alpha for {name} \n')
            if self.version_is_newer_than('3.11.99'):
                alpha_break = "(//label[normalize-space()='Break'])[1]"
                alpha_break_sitem = self.locator_finder_by_xpath(alpha_break)
                alpha_break_sitem.click()
                self.send_key_action(Keys.ARROW_DOWN)
                self.send_key_action(Keys.ENTER)
            else:
                alpha_break = '//div[label[text()="Break"]]//select[not(@disabled)]'
                self.locator_finder_by_select_using_xpath(alpha_break, 1)
            time.sleep(2)

            print(f'Selecting segmentation case as lower for {name} \n')
            if self.version_is_newer_than('3.11.99'):
                case_lower = "(//label[normalize-space()='Case'])[1]"
                case_lower_sitem = self.locator_finder_by_xpath(case_lower)
                case_lower_sitem.click()
                self.send_key_action(Keys.ARROW_DOWN)
                self.send_key_action(Keys.ENTER)
            else:
                case_lower = '//div[label[text()="Case"]]//select[not(@disabled)]'
                self.locator_finder_by_select_using_xpath(case_lower, 0)
            time.sleep(2)

        # for nearest neighbor analyzer introduced on 3.10.x
        elif name == "My_Nearest_Neighbor_Analyzer":
            location = ui_data_dir / "ui_data" / "analyzer_page" / "610_model_cooking.bin"
            print(f'Selecting model location for {name} \n')
            model_location = '//div[label[text()="Model Location"]]//input[not(@disabled)]'
            model_location_sitem = self.locator_finder_by_xpath(model_location)
            model_location_sitem.send_keys(str(location.absolute()))
            time.sleep(2)

            print(f'Selecting Top K value for {name}\n')
            top_k = '//div[label[text()="Top K"]]//input[not(@disabled)]'
            top_k_sitem = self.locator_finder_by_xpath(top_k)
            top_k_sitem.send_keys('2')
            time.sleep(2)

        # for classification analyzer introduced on 3.10.x
        elif name == "My_Classification_Analyzer":
            location = ui_data_dir / "ui_data" / "analyzer_page" / "610_model_cooking.bin"
            print(f'Selecting model location for {name} \n')
            model_location = '//div[label[text()="Model Location"]]//input[not(@disabled)]'
            model_location_sitem = self.locator_finder_by_xpath(model_location)
            model_location_sitem.send_keys(str(location.absolute()))
            time.sleep(2)

            print(f'Selecting Top K value for {name}\n')
            top_k = '//div[label[text()="Top K"]]//input[not(@disabled)]'
            top_k_sitem = self.locator_finder_by_xpath(top_k)
            top_k_sitem.send_keys('2')
            time.sleep(2)

            print(f'Selecting threshold for {name} \n')
            threshold = '//div[label[text()="Threshold"]]//input[not(@disabled)]'
            threshold_sitem = self.locator_finder_by_xpath(threshold)
            threshold_sitem.send_keys('.80')

        # Pipeline
        elif name == "My_Pipeline_Analyzer":
            # ----------------------adding first pipeline analyzer as Norm analyzer--------------------------
            print(f'Selecting add analyzer button for {name} \n')
            if self.version_is_newer_than('3.11.99'):
                add_analyzer01 = '//*[@id="chakra-modal--body-7"]/div/div[3]/div/button'
            else:
                add_analyzer01 = '(//button[@class="button-warning"][not(@disabled)])[2]'
            add_analyzer01_sitem = self.locator_finder_by_xpath(add_analyzer01)
            add_analyzer01_sitem.click()
            time.sleep(1)

            print(f'Selecting first pipeline analyzer as Norm for {name} \n')
            if self.version_is_newer_than('3.11.99'):
                norm = '//*[@id="chakra-modal--body-7"]/div/div[3]/div/div/div[1]/div/div/div/div[1]/div[2]'
                norm_sitem = self.locator_finder_by_xpath(norm)
                norm_sitem.click()

                # selecting norm analyzer
                for _ in range(3):
                    self.send_key_action(Keys.ARROW_DOWN)
                self.send_key_action(Keys.ENTER)
                time.sleep(1)

                # selecting locale value
                select_locale = "(//input[@id='properties.pipeline.0.properties.locale'])[1]"
                select_locale_sitem = self.locator_finder_by_xpath(select_locale)
                select_locale_sitem.click()
                select_locale_sitem.send_keys("en_US.utf-8")
                time.sleep(1)

                # selecting case for norm analyzer
                case = '//*[@id="chakra-modal--body-7"]/div/div[3]/div/div/div[1]/div[2]/div/div[2]/div/div/div[1]/div[2]'
                case_sitem = self.locator_finder_by_xpath(case)
                case_sitem.click()
                self.send_key_action(Keys.ARROW_DOWN)
                self.send_key_action(Keys.ENTER)
                time.sleep(1)

                # selecting accent
                accent = '//*[@id="chakra-modal--body-7"]/div/div[3]/div/div/div[1]/div[2]/div/div[3]/div/div/label[2]/span/span'
                accent_sitem = self.locator_finder_by_xpath(accent)
                accent_sitem.click()
                time.sleep(1)
            else:
                norm = '(//div[label[text()="Analyzer Type"]]//select[not(@disabled)])[2]'
                self.locator_finder_by_select_using_xpath(norm, 2)  # 2 for norm from the drop-down list
                time.sleep(2)
                print(f'Selecting locale value for Norm analyzer of {name} \n')
                value = 'en_US.utf-8'
                locale_sitem = self.locator_finder_by_xpath(local_placeholder)
                locale_sitem.click()
                locale_sitem.send_keys(value)
                time.sleep(2)

                print(f'Selecting case value to upper for Norm analyzer of {name} \n')
                self.locator_finder_by_select_using_xpath(case_placeholder,1)  # 1 represents upper from the dropdown
                time.sleep(2)
                # ----------------------adding second pipeline analyzer as N-Gram analyzer--------------------------
                print(f'Selecting add analyzer button for {name} \n')
                new_analyzer = '(//button[@class="button-warning"][not(@disabled)])[3]'
                new_analyzer_sitem = self.locator_finder_by_xpath(new_analyzer)
                new_analyzer_sitem.click()
                time.sleep(2)

                print(f'Selecting second pipeline analyzer as N-Gram for {name} \n')
                ngram = '(//div[label[text()="Analyzer Type"]]//select[not(@disabled)])[3]'
                self.locator_finder_by_select_using_xpath(ngram, 3)  # 3 represents N-Gram from the dropdown
                time.sleep(2)

                print(f'Selecting N-Gram minimum length for {name} \n')
                min_length = '//div[label[text()="Minimum N-Gram Length"]]//input[not(@disabled)]'
                min_length_sitem = self.locator_finder_by_xpath(min_length)
                min_length_sitem.click()
                min_length_sitem.clear()
                min_length_sitem.send_keys(3)
                time.sleep(2)

                print(f'Selecting N-Gram maximum length for {name} \n')
                max_length = '//div[label[text()="Maximum N-Gram Length"]]//input[not(@disabled)]'
                max_length_sitem = self.locator_finder_by_xpath(max_length)
                max_length_sitem.click()
                max_length_sitem.clear()
                max_length_sitem.send_keys(3)

                print(f'Selecting Preserve original value for {name}\n')
                preserve = '//div[label[text()="Preserve Original"]]//input[not(@disabled)]'
                preserve_sitem = self.locator_finder_by_xpath(preserve)
                preserve_sitem.click()
                time.sleep(2)

                print(f'Start marker value {name}\n')
                start_marker = '//div[label[text()="Start Marker"]]//input[not(@disabled)]'
                start_marker_sitem = self.locator_finder_by_xpath(start_marker)
                start_marker_sitem.click()
                start_marker_sitem.clear()
                start_marker_sitem.send_keys('^')
                time.sleep(2)

                print(f'End marker value for {name} \n')
                end_marker = '//div[label[text()="End Marker"]]//input[not(@disabled)]'
                end_marker_sitem = self.locator_finder_by_xpath(end_marker)
                end_marker_sitem.click()
                end_marker_sitem.clear()
                end_marker_sitem.send_keys('$')
                time.sleep(2)

                print(f'Stream type selection using name value for {name}\n')
                stream_type = '//div[label[text()="Stream Type"]]//select[not(@disabled)]'
                self.locator_finder_by_select_using_xpath(stream_type, 1)
                time.sleep(2)
        # GeoJson
        elif name == "My_GeoJSON_Analyzer":
            if self.version_is_newer_than('3.11.99'):
                types = '//*[@id="field-11-label"]'
                types_sitem = self.locator_finder_by_xpath(types)
                types_sitem.click()
                self.send_key_action(Keys.ARROW_DOWN)
                self.send_key_action(Keys.ARROW_DOWN)
                self.send_key_action(Keys.ARROW_DOWN)
                self.send_key_action(Keys.ENTER)

            else:
                types = '//div[label[text()="Type"]]//select[not(@disabled)]'
                types_sitem = self.locator_finder_by_xpath(types)
                types_sitem.click()
            time.sleep(2)

            print(f'Selecting max S2 cells value for {name} \n')
            if self.version_is_newer_than('3.11.99'):
                max_s2_cells = '//*[@id="properties.options.maxCells"]'
            else:
                max_s2_cells = '//div[label[text()="Max S2 Cells"]]//input[not(@disabled)]'

            max_s2_cells_sitem = self.locator_finder_by_xpath(max_s2_cells)
            max_s2_cells_sitem.click()

            if self.version_is_newer_than('3.11.99'):
                self.send_key_action(Keys.BACKSPACE)
                self.send_key_action(Keys.BACKSPACE)
            else:
                max_s2_cells_sitem.clear()

            max_s2_cells_sitem.send_keys('20')
            time.sleep(2)

            print(f'Selecting least precise S2 levels for {name} \n')
            least_precise = '//div[label[text()="Least Precise S2 Level"]]//input[not(@disabled)]'
            least_precise_sitem = self.locator_finder_by_xpath(least_precise)
            least_precise_sitem.click()

            if self.version_is_newer_than('3.11.99'):
                self.send_key_action(Keys.BACKSPACE)
            else:
                least_precise_sitem.clear()

            least_precise_sitem.send_keys('10')
            time.sleep(2)

            print(f'Selecting most precise S2 levels for {name} \n')
            most_precise = '//div[label[text()="Most Precise S2 Level"]]//input[not(@disabled)]'
            most_precise_sitem = self.locator_finder_by_xpath(most_precise)
            most_precise_sitem.click()
            if self.version_is_newer_than('3.11.99'):
                self.send_key_action(Keys.BACKSPACE)
                self.send_key_action(Keys.BACKSPACE)

            most_precise_sitem.send_keys('30')
            time.sleep(2)
        # GeoPoint
        elif name == "My_GeoPoint_Analyzer":
            print(f'Selecting Latitude Path for {name} \n')
            latitude_paths = '//div[label[text()="Latitude Path"]]//input[not(@disabled)]'
            latitude_paths_sitem = self.locator_finder_by_xpath(latitude_paths)
            latitude_paths_sitem.click()
            latitude_paths_sitem.send_keys('40.78')
            if self.version_is_newer_than('3.11.99'):
                self.send_key_action(Keys.ENTER)
            time.sleep(2)

            print(f'Selecting Longitude Path for {name} \n')
            longitude_paths = '//div[label[text()="Longitude Path"]]//input[not(@disabled)]'
            longitude_paths_sitem = self.locator_finder_by_xpath(longitude_paths)
            longitude_paths_sitem.click()
            longitude_paths_sitem.send_keys('-73.97')
            if self.version_is_newer_than('3.11.99'):
                self.send_key_action(Keys.ENTER)
            time.sleep(2)

            print(f'Selecting max S2 cells value for {name} \n')
            max_s2_cells = '//div[label[text()="Max S2 Cells"]]//input[not(@disabled)]'
            max_s2_cells_sitem = self.locator_finder_by_xpath(max_s2_cells)
            max_s2_cells_sitem.click()
            if self.version_is_newer_than('3.11.99'):
                self.send_key_action(Keys.BACKSPACE)
                self.send_key_action(Keys.BACKSPACE)
            max_s2_cells_sitem.send_keys('20')
            time.sleep(2)

            print(f'Selecting least precise S2 levels for {name} \n')
            least_precise = '//div[label[text()="Least Precise S2 Level"]]//input[not(@disabled)]'
            least_precise_sitem = self.locator_finder_by_xpath(least_precise)
            least_precise_sitem.click()
            if self.version_is_newer_than('3.11.99'):
                self.send_key_action(Keys.BACKSPACE)
            least_precise_sitem.send_keys('4')
            time.sleep(2)

            print(f'Selecting most precise S2 levels for {name} \n')
            most_precise = '//div[label[text()="Most Precise S2 Level"]]//input[not(@disabled)]'
            most_precise_sitem = self.locator_finder_by_xpath(most_precise)
            most_precise_sitem.click()
            if self.version_is_newer_than('3.11.99'):
                self.send_key_action(Keys.BACKSPACE)
                self.send_key_action(Keys.BACKSPACE)
            most_precise_sitem.send_keys('23')
            time.sleep(2)
        # GeoS2
        elif name == 'My_GeoS2_Analyzer':
            print("Selecting type of geos2 analyzer")
            if self.version_is_newer_than('3.11.99'):
                types = "(//label[@id='field-11-label'])[1]"
            else:
                types = "(//label[normalize-space()='Type'])[1]"

            if self.version_is_older_than('3.10.99'):
                print("Type and Formate selection skipped for this version below 3.10 \n")
            else:
                type_sitem = self.locator_finder_by_xpath(types)
                type_sitem.click()
                self.send_key_action(Keys.ARROW_DOWN)
                self.send_key_action(Keys.ARROW_DOWN)

                if self.version_is_newer_than('3.11.99'):
                    self.send_key_action(Keys.ENTER)

                print("Selecting format of geos2 analyzer")
                if self.version_is_newer_than('3.11.99'):
                    formats = "(//label[normalize-space()='format'])[1]"
                else:
                    formats = "(//label[normalize-space()='Format'])[1]"

                format_sitem = self.locator_finder_by_xpath(formats)
                format_sitem.click()
                self.send_key_action(Keys.ARROW_DOWN)
                self.send_key_action(Keys.ARROW_DOWN)
                if self.version_is_newer_than('3.11.99'):
                    self.send_key_action(Keys.ENTER)

            print(f"Selecting max s2 for {name} \n")
            if self.version_is_older_than('3.10.99'):
                max_s2_cell = '//div[label[text()="Max S2 Cells"]]//input[not(@disabled)]'
            else:
                max_s2_cell = "//*[text()='Max S2 Cells']"
            
            max_s2_cell_sitem = self.locator_finder_by_xpath(max_s2_cell)
            max_s2_cell_sitem.click()
            if self.version_is_newer_than('3.11.99'):
                self.send_key_action(Keys.BACKSPACE)
                self.send_key_action(Keys.BACKSPACE)
            self.send_key_action("20")
            time.sleep(2)

            print(f'Selecting least precise for {name} \n')
            if self.version_is_older_than('3.10.99'):
                least_precise_s2_level = '//div[label[text()="Least Precise S2 Level"]]//input[not(@disabled)]'
            else:
                least_precise_s2_level = "//*[text()='Least Precise S2 Level']"
            least_precise_s2_level_sitem = self.locator_finder_by_xpath(least_precise_s2_level)
            least_precise_s2_level_sitem.click()
            if self.version_is_newer_than('3.11.99'):
                self.send_key_action(Keys.BACKSPACE)
            self.send_key_action("4")
            time.sleep(2)

            print(f'Selecting most precise S2 level for {name} \n')
            if self.version_is_older_than('3.10.99'):
                most_precise_s2_level = '//div[label[text()="Most Precise S2 Level"]]//input[not(@disabled)]'
            else:
                most_precise_s2_level = "//*[text()='Most Precise S2 Level']"
            most_precise_s2_level_sitem = self.locator_finder_by_xpath(most_precise_s2_level)
            most_precise_s2_level_sitem.click()
            if self.version_is_newer_than('3.11.99'):
                self.send_key_action(Keys.BACKSPACE)
                self.send_key_action(Keys.BACKSPACE)
            self.send_key_action("23")
            time.sleep(2)
        # Minhash
        elif name == 'My_Minhash_Analyzer':
            print("Selecting type of minhash analyzer")
            analyzer_type = '//*[@id="chakra-modal--body-7"]/div/div[3]/div/div[1]/div[1]/div[1]/div/div/div[1]/div[2]'
            analyzer_type_sitem = self.locator_finder_by_xpath(analyzer_type)
            analyzer_type_sitem.click()
            # selecting minhash for delimiter analyzer
            self.send_key_action(Keys.ARROW_DOWN)
            self.send_key_action(Keys.ENTER)
            time.sleep(2)

            print("adding minhash for delimiter analyzer")
            delimiter_value = '//*[@id="properties.analyzer.properties.delimiter"]'
            delimiter_value_sitem = self.locator_finder_by_xpath(delimiter_value)
            delimiter_value_sitem.click()
            delimiter_value_sitem.send_keys("#")
            time.sleep(1)

            numhashes = "(//input[@id='properties.numHashes'])[1]"
            numhashes_sitem = self.locator_finder_by_xpath(numhashes)
            numhashes_sitem.click()
            numhashes_sitem.send_keys("10")
            time.sleep(1)
        # MultiDelimiter
        elif name == "My_MultiDelimiter_Analyzer":
            print("Selecting type of MultiDelimiter analyzer")
            delimiters = "(//label[normalize-space()='Delimiters'])[1]"
            delimiters_sitem = self.locator_finder_by_xpath(delimiters)
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
            print("Selecting type of WildCard analyzer\n")
            ngram = "//input[@id='properties.ngramSize']"
            ngram_sitem = self.locator_finder_by_xpath(ngram)
            ngram_sitem.click()
            self.send_key_action(Keys.BACKSPACE)
            ngram_sitem.send_keys('4')
            time.sleep(2)

            print("Selecting delimiter analyzer\n")
            delimiter = '//*[@id="chakra-modal--body-7"]/div/div[3]/div[2]/div[1]/div[1]/div/div/div[1]/div[2]'
            delimiter_sitem = self.locator_finder_by_xpath(delimiter)
            delimiter_sitem.click()
            time.sleep(1)

            # selecting multi-delimiter analyzer from the drop-down menu
            for _ in range(15):
                self.send_key_action(Keys.ARROW_DOWN)

            self.send_key_action(Keys.ENTER)

            self.send_key_action(Keys.ARROW_DOWN)
            self.send_key_action(Keys.ENTER)

            print("Selecting Multi Delimiters \n")
            delimiter_properties = '//*[@id="chakra-modal--body-7"]/div/div[3]/div[2]/div[2]/div/div/div/div/div[1]/div[1]/div[2]'
            delimiter_properties_sitem = self.locator_finder_by_xpath(delimiter_properties)
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

            self.send_key_action("]")
            self.send_key_action(Keys.ENTER)

            self.send_key_action("-")
            self.send_key_action(Keys.ENTER)

            self.send_key_action("_")
            self.send_key_action(Keys.ENTER)
            time.sleep(2)
        
        #todo need to fix this one for 3.11.x
        if self.version_is_newer_than('3.11.0'):
            print("skiped switching view for code view\n")
        else:
            print(f'Switching current view to form view for {name}\n')
            switch_view_btn = '//*[@id="modal-content-add-analyzer"]/div[1]/div/div[2]/div/div[2]/button'
            code_view_sitem = self.locator_finder_by_xpath(switch_view_btn)
            code_view_sitem.click()
            time.sleep(3)

            print(f'Switching current view to code view for {name}\n')
            form_view_sitem = self.locator_finder_by_xpath(switch_view_btn)
            form_view_sitem.click()
            time.sleep(3)
            

        print(f"Selecting the create button for the {name} \n")
        print(f'Selecting the create button for the {name} \n')
        if self.version_is_newer_than('3.11.0'):
            if self.version_is_newer_than('3.11.99'):
                create = '//*[@id="chakra-modal-7"]/form/footer/div/button[2]'
            else:
                create = '//*[@id="chakra-modal-2"]/footer/button[2]'
        else:
            create = "//*[text()='Create']"

        create_btn_sitem = self.locator_finder_by_xpath(create)
        create_btn_sitem.click()
        time.sleep(2)

        # checking the creation of the analyzer using the green notification bar appears at the bottom
        try:
            print(f"Checking successful creation of the {name} \n")
            if self.version_is_newer_than('3.11.99'):
                success_message = "/html/body/div[10]/ul[5]/li/div/div/div/div"
                success_message_sitem = self.locator_finder_by_xpath(success_message).text
                print("Notification: ", success_message_sitem, "\n")
                expected_msg = f"The analyzer: {name} was successfully created"
            else:
                success_message = "noty_body"
                success_message_sitem = self.locator_finder_by_class(success_message).text
                print("Notification: ", success_message_sitem, "\n")
                expected_msg = f"Success: Created Analyzer: _system::{name}"

            assert expected_msg == success_message_sitem, f"Expected {expected_msg} but got {success_message_sitem}"
        except TimeoutException:
            print("Error occurred!! required manual inspection.\n")
        print(f"Creating {name} completed successfully \n")

        # --------------------here we are checking the properties of the created analyzer----------------------
        if self.version_is_newer_than('3.11.99'):
            try:
                analyzer = f"//*[text()='_system::{name}']"
                analyzer_sitem = self.locator_finder_by_xpath(analyzer)
                if analyzer_sitem is None:
                    print(f'This {analyzer_name} has never been created \n')
                else:
                    analyzer_sitem.click()
                    time.sleep(1)

                    # finding the ace editor using neighbor locators
                    nearest_button = "//button[@class='jsoneditor-compact']"
                    ace_locator = self.locator_finder_by_xpath(nearest_button)
                    # Set x and y offset positions of adjacent element
                    xOffset = 50
                    yOffset = 50
                    # Performs mouse move action onto the element
                    actions = ActionChains(self.webdriver).move_to_element_with_offset(ace_locator, xOffset, yOffset)
                    actions.click()
                    actions.key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL).key_down(Keys.CONTROL).send_keys(
                        "c").key_up(Keys.CONTROL)
                    actions.perform()  # Execute the sequence of actions

                    # Retrieve text content from the clipboard using Pyperclip
                    actual_properties = ''.join(str(pyperclip.paste()).split())
                    # Get expected properties based on analyzer name
                    expected_properties = ''.join(str(self.generate_expected_properties(name)).split())
                    # Assert that the copied text matches the expected text
                    try:
                        assert actual_properties == expected_properties, "Text does not match the expected text \n"
                    except AssertionError as ex:
                        print("actual_properties: ", actual_properties)
                        print("expected_properties: ", expected_properties)
                        raise AssertionError("Text does not match the expected text") from ex
                    else:
                        print("Text matches the expected text. \n")

            except TimeoutException as ex:
                print(f'Failed to parse properties from the {name} and the error is: {ex} \n')

    @staticmethod
    def generate_expected_properties(analyzer_name):
        """Define a method to generate expected text for a specific analyzer based on its name"""
        if analyzer_name == "My_Identity_Analyzer":
            return """{
                "name": "_system::My_Identity_Analyzer",
                "type": "identity",
                "properties": {},
                "features": [
                    "frequency",
                    "position",
                    "norm"
                ]
            }"""
        elif analyzer_name == "My_Delimiter_Analyzer":
            return """{
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
                }"""
        elif analyzer_name == "My_Stem_Analyzer":
            return """{
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
                }"""
        elif analyzer_name == "My_Norm_Analyzer":
            return """{
                  "name": "_system::My_Norm_Analyzer",
                  "type": "norm",
                  "properties": {
                    "locale": "en_US",
                    "case": "none",
                    "accent": false
                  },
                  "features": [
                    "frequency",
                    "position",
                    "norm"
                  ]
                }"""
        elif analyzer_name == "My_N-Gram_Analyzer":
            return """{
                  "name": "_system::My_N-Gram_Analyzer",
                  "type": "ngram",
                  "properties": {
                    "min": 22,
                    "max": 33,
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
                }"""
        elif analyzer_name == "My_Text_Analyzer":
            return """{
                  "name": "_system::My_Text_Analyzer",
                  "type": "text",
                  "properties": {
                    "locale": "en_US",
                    "case": "lower",
                    "accent": true,
                    "stemming": false,
                    "edgeNgram": {
                      "min": 2,
                      "max": 3,
                      "preserveOriginal": true
                    }
                  },
                  "features": [
                    "frequency",
                    "position",
                    "norm"
                  ]
                }"""
        elif analyzer_name == "My_AQL_Analyzer":
            return """{
                  "name": "_system::My_AQL_Analyzer",
                  "type": "aql",
                  "properties": {
                    "queryString": "FOR year IN 2010..2015 RETURN year",
                    "collapsePositions": true,
                    "keepNull": true,
                    "batchSize": 1,
                    "memoryLimit": 104857,
                    "returnType": "string"
                  },
                  "features": [
                    "frequency",
                    "position",
                    "norm"
                  ]
                }"""
        elif analyzer_name == "My_Stopwords_Analyzer":
            return """{
                  "name": "_system::My_Stopwords_Analyzer",
                  "type": "stopwords",
                  "properties": {
                    "stopwords": [
                      "616e64"
                    ],
                    "hex": true
                  },
                  "features": [
                    "frequency",
                    "position",
                    "norm"
                  ]
                }"""
        elif analyzer_name == "My_Collation_Analyzer":
            return """{
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
                }"""
        elif analyzer_name == "My_Segmentation_Alpha_Analyzer":
            return """{
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
                }"""
        elif analyzer_name == "My_Pipeline_Analyzer":
            return """{
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
                }"""
        elif analyzer_name == "My_GeoJSON_Analyzer":
            return """{
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
                }"""
        elif analyzer_name == "My_GeoPoint_Analyzer":
            return """{
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
                """
        elif analyzer_name == "My_GeoS2_Analyzer":
            return """{
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
                }"""
        elif analyzer_name == "My_Minhash_Analyzer":
            return """{
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
                }"""
        elif analyzer_name == "My_MultiDelimiter_Analyzer":
            return """{
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
                }"""
        elif analyzer_name == "My_WildCard_Analyzer":
            return """
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
                          "[",
                          "]",
                          "-",
                          "_"
                        ]
                      }
                    }
                  },
                  "features": [
                    "frequency",
                    "position",
                    "norm"
                  ]
                }"""
        elif analyzer_name == "My_Nearest_Neighbor_Analyzer":
            return """{
                "name": "_system::My_Nearest_Neighbor_Analyzer",
                "type": "nearest_neighbors",
                "properties": {
                    "model_location": "/home/fattah/Downloads/release-test-automation/test_data/ui_data/analyzer_page/610_model_cooking.bin",
                    "top_k": 2
                },
                "features": [
                    "frequency",
                    "position",
                    "norm"
                ]
                }"""

        elif analyzer_name == "My_Classification_Analyzer":
            return """{
                "name": "_system::My_Classification_Analyzer",
                "type": "classification",
                "properties": {
                    "model_location": "/home/fattah/Downloads/release-test-automation/test_data/ui_data/analyzer_page/610_model_cooking.bin",
                    "top_k": 2,
                    "threshold": 0.8
                },
                "features": [
                    "frequency",
                    "position",
                    "norm"
                ]
                }"""

    
    def creating_all_supported_analyzer(self, enterprise, model_location=None):
        """This method will create all the supported version-specific analyzers"""
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
            "My_Segmentation_Alpha_Analyzer": (0, None, False),
            "My_Pipeline_Analyzer": (0, semver.VersionInfo.parse('3.10.0'), False),
            "My_GeoJSON_Analyzer": (0, semver.VersionInfo.parse('3.10.0'), False),
            "My_GeoPoint_Analyzer": (0, semver.VersionInfo.parse('3.10.0'), False),
            "My_MultiDelimiter_Analyzer": (0, semver.VersionInfo.parse('3.11.99'), False),
            "My_WildCard_Analyzer": (0, semver.VersionInfo.parse('3.11.99'), False),
            "My_Minhash_Analyzer": (0, semver.VersionInfo.parse('3.11.99'), not (enterprise and self.version_is_newer_than('3.11.99'))),
            "My_Nearest_Neighbor_Analyzer": (1 if enterprise else 0, semver.VersionInfo.parse('3.10.0'), not enterprise),
            "My_Classification_Analyzer": (1 if enterprise else 0, semver.VersionInfo.parse('3.10.0'), not enterprise),
            "My_GeoS2_Analyzer": (0, None, not enterprise)
        }

        # Loop through each analyzer in the dictionary
        for analyzer_name, config in decode_analyzers.items():
            # Retrieve parameters, version requirement, and skip condition for the current analyzer
            num_params, version_requirement, skip_condition = config
            # Check if the analyzer should be skipped
            if skip_condition:
                print(f'Skipping {analyzer_name} creation\n')
                continue
            # Check if the current package version meets the version requirement
            if version_requirement is None or self.version_is_newer_than(str(version_requirement)):
                print(f'Adding {analyzer_name} analyzer\n')
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
            print("Something went wrong\n")

        self.select_analyzers_page()
        self.webdriver.refresh()

        try:
            print("Selecting add new analyzer button \n")
            add_analyzer = self.add_new_analyzer_btn
            add_analyzer_sitem = self.locator_finder_by_xpath(add_analyzer)
            add_analyzer_sitem.click()
            time.sleep(2)

            print(f'checking {name} started \n')
            # common attributes for all the analyzers
            analyzer_name = '//div[label[text()="Analyzer Name"]]/input[not(@disabled)]'
            analyzer_type = '//div[label[text()="Analyzer Type"]]/select[not(@disabled)]'
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
                print(f"Expected error scenario for the {name} Started \n")
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
                print(f"Expected error scenario for the {name} Started \n")
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
                print(f"Expected error scenario for the {name} Started \n")
                # filling out the name placeholder first
                aql_analyzer_sitem = self.locator_finder_by_xpath(analyzer_name)
                aql_analyzer_sitem.click()
                aql_analyzer_sitem.clear()
                aql_analyzer_sitem.send_keys(name)

                print(f"Selecting query string for {name} \n")
                query_string = '//div[label[text()="Query String"]]/textarea[not(@disabled)]'
                query_string_sitem = self.locator_finder_by_xpath(query_string)
                query_string_sitem.send_keys("FOR year IN 2010..2015 RETURN year")
                time.sleep(2)

                print(f"Selecting memory limit for {name} \n")
                memory_limit = '//div[label[text()="Memory Limit"]]//input[not(@disabled)]'
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

            print(f"Closing the {name} check \n")
            if self.version_is_newer_than('3.11.0'):
                close_btn = '//*[@id="chakra-modal-2"]/footer/button[1]'
            else:
                close_btn = '//*[@id="modal-content-add-analyzer"]/div[3]/button[1]'
            close_btn_sitem = self.locator_finder_by_xpath(close_btn)
            close_btn_sitem.click()
            time.sleep(2)

            print(f"Expected error scenario for the {name} Completed \n")
        except Exception:
            print('Info: Error occured during checking expected error!')
    
    def analyzer_expected_error_check(self):
        """This will call all the error scenario methods"""
        if self.version_is_newer_than('3.11.99'):
            print('Skipped \n')
        else:
            print('Checking negative scenario for the identity analyzers name \n')
            self.test_analyzer_expected_error('Identity_Analyzer')
            print('Checking negative scenario for the stem analyzers locale value \n')
            self.test_analyzer_expected_error('Stem_Analyzer')
            print('Checking negative scenario for the stem analyzers locale value \n')
            self.test_analyzer_expected_error('N_Gram_Analyzer')
            print('Checking negative scenario for the AQL analyzers \n')
            self.test_analyzer_expected_error('AQL_Analyzer')


    def checking_search_filter(self):
        """This method will check analyzer's search filter option"""
        if self.version_is_newer_than('3.11.99'):
            print("Skipped \n")
        else:
            print('Checking analyzer search filter options started \n')
            self.checking_search_filter_option('de')
            self.checking_search_filter_option('geo', False)  # false indicating builtIn option will be disabled
            print('Checking analyzer search filter options completed \n')

    
    def delete_analyzer(self, analyzer_name):
        """Deleting all the analyzer using their ID"""
        self.select_analyzers_page()
        self.webdriver.refresh()

        try:
            print(f'Deletion of {analyzer_name} started \n')
            if self.version_is_newer_than('3.11.99'):
                analyzer = f"//*[text()='_system::{analyzer_name}']"
                analyzer_sitem = self.locator_finder_by_xpath(analyzer)
                if analyzer_sitem is None:
                    print(f'This {analyzer_name} has never been created \n')
                else:
                    analyzer_sitem.click()
                    time.sleep(1)

                    select_delete_btn = "(//button[normalize-space()='Delete'])[1]"
                    select_delete_btn_sitem = self.locator_finder_by_xpath(select_delete_btn)
                    select_delete_btn_sitem.click()
                    time.sleep(1)

                    delete_confirm_btn = "(//button[@class='chakra-button css-flye6g'])[1]"
                    delete_confirm_btn_sitem = self.locator_finder_by_xpath(delete_confirm_btn)
                    delete_confirm_btn_sitem.click()
                    time.sleep(1)

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
                    print("This analyzer has never been created or already been deleted! \n")
                else:
                    delete_btn_sitem.click()
                    time.sleep(8)
                print(f'Deletion of {analyzer_name} completed \n')
        except TimeoutException:
            print('TimeoutException occurred! \n')
            print('Info: Analyzer has already been deleted or never created. \n')
        except Exception:
            traceback.print_exc()
            raise Exception('Critical Error occurred and need manual inspection!! \n')
    

    def deleting_all_created_analyzers(self):
        """Deleting all the created analyzers"""
        self.delete_analyzer('My_AQL_Analyzer')
        self.delete_analyzer('My_Collation_Analyzer')
        self.delete_analyzer('My_Delimiter_Analyzer')
        self.delete_analyzer('My_GeoJSON_Analyzer')
        self.delete_analyzer('My_GeoPoint_Analyzer')
        self.delete_analyzer('My_Identity_Analyzer')
        self.delete_analyzer('My_N-Gram_Analyzer')
        self.delete_analyzer('My_Norm_Analyzer')
        self.delete_analyzer('My_Pipeline_Analyzer')
        self.delete_analyzer('My_Segmentation_Alpha_Analyzer')
        self.delete_analyzer('My_Stem_Analyzer')
        self.delete_analyzer('My_Stopwords_Analyzer')
        self.delete_analyzer('My_Text_Analyzer')
        self.delete_analyzer('My_Nearest_Neighbor_Analyzer')
        self.delete_analyzer('My_Classification_Analyzer')
        self.delete_analyzer('My_GeoS2_Analyzer')
        if self.version_is_newer_than('3.11.99'):
            self.delete_analyzer('My_Minhash_Analyzer')
            self.delete_analyzer('My_MultiDelimiter_Analyzer')
            self.delete_analyzer('My_WildCard_Analyzer')
        print('All the created analyzers have been deleted \n')