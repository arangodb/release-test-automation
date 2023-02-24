#!/usr/bin/env python3
""" analyzer page object """
import time
import traceback
import semver
from selenium_ui_test.pages.base_page import Keys
from selenium_ui_test.pages.navbar import NavigationBarPage
from selenium.common.exceptions import TimeoutException


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
        self.webdriver.refresh()
        print("Selecting Analyzers help filter button \n")
        help_filter = "//a[@href='#analyzers']//i[@class='fa fa-question-circle']"
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
    

    def checking_all_built_in_analyzer(self):
        print('Showing in-built Analyzers list \n')
        self.select_built_in_analyzers_open()

        print('Checking in-built identity analyzer \n')
        self.select_analyzer_to_check("identity", '//tr/td[text()="identity"]/following-sibling::td[2]/button')
        print('Checking in-built text_de analyzer \n')
        self.select_analyzer_to_check("text_de", '//tr/td[text()="text_de"]/following-sibling::td[2]/button')
        print('Checking in-built text_en analyzer \n')
        self.select_analyzer_to_check('text_en', '//tr/td[text()="text_en"]/following-sibling::td[2]/button')
        print('Checking in-built text_es analyzer \n')
        self.select_analyzer_to_check('text_es', '//tr/td[text()="text_es"]/following-sibling::td[2]/button')
        print('Checking in-built text_fi analyzer \n')
        self.select_analyzer_to_check('text_fi', '//tr/td[text()="text_fi"]/following-sibling::td[2]/button')
        print('Checking in-built text_fr analyzer \n')
        self.select_analyzer_to_check('text_fr', '//tr/td[text()="text_fr"]/following-sibling::td[2]/button')
        print('Checking in-built text_it analyzer \n')
        self.select_analyzer_to_check('text_it', '//tr/td[text()="text_it"]/following-sibling::td[2]/button')
        print('Checking in-built text_nl analyzer \n')
        self.select_analyzer_to_check('text_nl', '//tr/td[text()="text_nl"]/following-sibling::td[2]/button')
        print('Checking in-built text_no analyzer \n')
        self.select_analyzer_to_check('text_no', '//tr/td[text()="text_no"]/following-sibling::td[2]/button')
        print('Checking in-built text_pt analyzer \n')
        self.select_analyzer_to_check('text_pt', '//tr/td[text()="text_pt"]/following-sibling::td[2]/button')
        print('Checking in-built text_ru analyzer \n')
        self.select_analyzer_to_check('text_ru', '//tr/td[text()="text_ru"]/following-sibling::td[2]/button')
        print('Checking in-built text_sv analyzer \n')
        self.select_analyzer_to_check('text_sv', '//tr/td[text()="text_sv"]/following-sibling::td[2]/button')
        print('Checking in-built text_zh analyzer \n')
        self.select_analyzer_to_check('text_zh', '//tr/td[text()="text_zh"]/following-sibling::td[2]/button')

        print('Hiding in-built Analyzers list \n')
        self.select_built_in_analyzers_close()


    def add_new_analyzer(self, name, test_data_dir=None):
        """Adding analyzer type delimiter with necessary features"""
        # pylint: disable=too-many-locals disable=too-many-branches disable=too-many-statements
        index = self.index
        if name == "My_Identity_Analyzer":
            index = 0
        elif name == "My_Delimiter_Analyzer":
            index = 1
        elif name == "My_Stem_Analyzer":
            index = 2
        elif name == "My_Norm_Analyzer":
            index = 3
        elif name == "NGram_Analyzer":
            index = 4
        elif name == "My_Text_Analyzer":
            index = 5
        elif name == "My_AQL_Analyzer":
            index = 6
        elif name == "My_Stopwords_Analyzer":
            index = 7
        elif name == "My_Collation_Analyzer":
            index = 8
        elif name == "My_Segmentation_Alpha_Analyzer":
            index = 9
        elif name == "My_Nearest_Neighbor_Analyzer":
            if self.package_version >= semver.VersionInfo.parse('3.10.0'):
                index = 10
        elif name == "My_Classification_Analyzer":
            if self.package_version >= semver.VersionInfo.parse('3.10.0'):
                index = 11
        elif name == "My_Pipeline_Analyzer":
            if self.package_version >= semver.VersionInfo.parse('3.10.0'):
                index = 12
            else:
                index = 10
        elif name == "My_GeoJSON_Analyzer":
            if self.package_version >= semver.VersionInfo.parse('3.10.0'):
                index = 13
            else:
                index = 11
        elif name== "My_GeoPoint_Analyzer":
                if self.package_version >= semver.VersionInfo.parse('3.10.0'):
                    index = 14
                else:
                    index = 12
        else:
            print("Something went wrong\n")

        self.select_analyzers_page()
        self.webdriver.refresh()

        print("Selecting add new analyzer button \n")
        add_analyzer = self.add_new_analyzer_btn
        add_analyzer_sitem = self.locator_finder_by_xpath(add_analyzer)
        add_analyzer_sitem.click()
        time.sleep(2)

        print(f"Creating {name} started \n")
        # common attributes for all the analyzers
        print(f'Creating {name} started \n')
        # common attributes for all the analyzer
        analyzer_name = '//div[label[text()="Analyzer Name"]]/input[not(@disabled)]'
        analyzer_type = '//div[label[text()="Analyzer Type"]]/select[not(@disabled)]'
        frequency = '//div[label[text()="Frequency"]]/input[not(@disabled)]'
        norm = '//div[label[text()="Norm"]]/input[not(@disabled)]'
        position = '//div[label[text()="Position"]]/input[not(@disabled)]'
        switch_view_btn = '//*[@id="modal-content-add-analyzer"]/div[1]/div/div[2]/div/div[2]/button'
        switch_form_btn = '//*[@id="modal-content-add-analyzer"]/div[1]/div/div[2]/div/div[2]/button'
        create = '//*[@id="modal-content-add-analyzer"]/div[3]/button[2]'
        local_placeholder = '//div[label[text()="Locale"]]//input[not(@disabled)]'
        case_placeholder = '//div[label[text()="Case"]]//select[not(@disabled)]'

        analyzer_name_sitem = self.locator_finder_by_xpath(analyzer_name)
        analyzer_name_sitem.click()
        analyzer_name_sitem.clear()
        analyzer_name_sitem.send_keys(name)
        time.sleep(2)

        print('Selecting analyzer type \n')
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
            self.locator_finder_by_select_using_xpath(case_placeholder, 0)

            print('Selecting accent for norm analyzer \n')
            accent = '//div[label[text()="Accent"]]//input[not(@disabled)]'
            accent_sitem = self.locator_finder_by_xpath(accent)
            accent_sitem.click()
            time.sleep(2)

        # for N-Gram
        elif name == "NGram_Analyzer":
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

            print(f"Selecting case for the analyzer from the dropdown menu for {name} \n")
            self.locator_finder_by_select_using_xpath(case_placeholder, 1)

            print('Selecting stem for the analyzer \n')
            stem = '//div[label[text()="Stemming"]]//input[not(@disabled)]'
            stem_sitem = self.locator_finder_by_xpath(stem)
            stem_sitem.click()
            time.sleep(2)

            print('Selecting accent for the analyzer \n')
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
            preserve = '//div[label[text()="Preserve Original"]]//input[not(@disabled)]'
            preserve_sitem = self.locator_finder_by_xpath(preserve)
            preserve_sitem.click()
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
            batch_size_sitem.clear()
            batch_size_sitem.send_keys('100')
            time.sleep(2)

            print(f'Selecting memory limit for {name} \n')
            memory_limit = '//div[label[text()="Memory Limit"]]//input[not(@disabled)]'
            memory_limit_sitem = self.locator_finder_by_xpath(memory_limit)
            memory_limit_sitem.click()
            memory_limit_sitem.clear()
            memory_limit_sitem.send_keys('200')
            time.sleep(2)

            print(f'Selecting collapse position for {name} \n')
            collapse = '//div[label[text()="Collapse Positions"]]//input[not(@disabled)]'
            collapse_sitem = self.locator_finder_by_xpath(collapse)
            collapse_sitem.click()
            time.sleep(2)

            print(f'Selecting keep null for {name} \n')
            keep_null = '//div[label[text()="Keep Null"]]//input[not(@disabled)]'
            keep_null_sitem = self.locator_finder_by_xpath(keep_null)
            keep_null_sitem.click()
            time.sleep(2)

            print(f'Selecting Return type for {name} \n')
            return_type = '//div[label[text()="Return Type"]]//select[not(@disabled)]'
            self.locator_finder_by_select_using_xpath(return_type, 1)
            time.sleep(2)
        # for stopwords
        elif name == "My_Stopwords_Analyzer":
            print(f'Selecting stopwords for {name} \n')
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
            alpha_break = '//div[label[text()="Break"]]//select[not(@disabled)]'
            self.locator_finder_by_select_using_xpath(alpha_break, 1)
            time.sleep(2)

            print(f'Selecting segmentation case as lower for {name} \n')
            case_lower = '//div[label[text()="Case"]]//select[not(@disabled)]'
            self.locator_finder_by_select_using_xpath(case_lower, 0)
            time.sleep(2)

        # for nearest neighbor analyzer introduced on 3.10.x
        elif name == "My_Nearest_Neighbor_Analyzer":
            location = test_data_dir / "makedata_suites" / "610_model_cooking.bin"
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
            location = test_data_dir / "makedata_suites" / "610_model_cooking.bin"
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
            add_analyzer01 = '(//button[@class="button-warning"][not(@disabled)])[2]'
            add_analyzer01_sitem = self.locator_finder_by_xpath(add_analyzer01)
            add_analyzer01_sitem.click()
            time.sleep(1)

            print(f'Selecting first pipeline analyzer as Norm for {name} \n')
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
            self.locator_finder_by_select_using_xpath(case_placeholder, 1)
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

            print(f'Stream type selection using index value for {name}\n')
            stream_type = '//div[label[text()="Stream Type"]]//select[not(@disabled)]'
            self.locator_finder_by_select_using_xpath(stream_type, 1)
            time.sleep(2)
        # GeoJson
        elif name == "My_GeoJSON_Analyzer":
            print(f'Selecting type for {name} \n')
            types = '//div[label[text()="Type"]]//select[not(@disabled)]'
            types_sitem = self.locator_finder_by_xpath(types)
            types_sitem.click()
            time.sleep(2)

            print(f'Selecting max S2 cells value for {name} \n')
            max_s2_cells = '//div[label[text()="Max S2 Cells"]]//input[not(@disabled)]'
            max_s2_cells_sitem = self.locator_finder_by_xpath(max_s2_cells)
            max_s2_cells_sitem.click()
            max_s2_cells_sitem.clear()
            max_s2_cells_sitem.send_keys('20')
            time.sleep(2)

            print(f'Selecting least precise S2 levels for {name} \n')
            least_precise = '//div[label[text()="Least Precise S2 Level"]]//input[not(@disabled)]'
            least_precise_sitem = self.locator_finder_by_xpath(least_precise)
            least_precise_sitem.click()
            least_precise_sitem.clear()
            least_precise_sitem.send_keys('10')
            time.sleep(2)

            print(f'Selecting most precise S2 levels for {name} \n')
            most_precise = '//div[label[text()="Most Precise S2 Level"]]//input[not(@disabled)]'
            most_precise_sitem = self.locator_finder_by_xpath(most_precise)
            most_precise_sitem.click()
            most_precise_sitem.send_keys('30')
            time.sleep(2)
        # GeoPoint
        elif name == "My_GeoPoint_Analyzer":
            print(f'Selecting Latitude Path for {name} \n')
            latitude_paths = '//div[label[text()="Latitude Path"]]//input[not(@disabled)]'
            latitude_paths_sitem = self.locator_finder_by_xpath(latitude_paths)
            latitude_paths_sitem.click()
            latitude_paths_sitem.send_keys('40.78')
            time.sleep(2)

            print(f'Selecting Longitude Path for {name} \n')
            longitude_paths = '//div[label[text()="Longitude Path"]]//input[not(@disabled)]'
            longitude_paths_sitem = self.locator_finder_by_xpath(longitude_paths)
            longitude_paths_sitem.click()
            longitude_paths_sitem.send_keys('-73.97')
            time.sleep(2)

            print(f'Selecting max S2 cells value for {name} \n')
            max_s2_cells = '//div[label[text()="Max S2 Cells"]]//input[not(@disabled)]'
            max_s2_cells_sitem = self.locator_finder_by_xpath(max_s2_cells)
            max_s2_cells_sitem.click()
            max_s2_cells_sitem.send_keys('20')
            time.sleep(2)

            print(f'Selecting least precise S2 levels for {name} \n')
            least_precise = '//div[label[text()="Least Precise S2 Level"]]//input[not(@disabled)]'
            least_precise_sitem = self.locator_finder_by_xpath(least_precise)
            least_precise_sitem.click()
            least_precise_sitem.send_keys('4')
            time.sleep(2)

            print(f'Selecting most precise S2 levels for {name} \n')
            most_precise = '//div[label[text()="Most Precise S2 Level"]]//input[not(@disabled)]'
            most_precise_sitem = self.locator_finder_by_xpath(most_precise)
            most_precise_sitem.click()
            most_precise_sitem.send_keys('23')
            time.sleep(2)
        
        print(f'Switching current view to form view for {name}\n')
        code_view_sitem = self.locator_finder_by_xpath(switch_view_btn)
        code_view_sitem.click()
        time.sleep(3)

        print(f'Switching current view to code view for {name}\n')
        form_view_sitem = self.locator_finder_by_xpath(switch_form_btn)
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

    
    def creating_all_supported_analyzer(self, enterprise, model_location=None):
        """This method will create all the supported version specific analyzers"""
        print('Adding Identity analyzer \n')
        self.add_new_analyzer('My_Identity_Analyzer')

        print('Adding Delimiter analyzer \n')
        self.add_new_analyzer('My_Delimiter_Analyzer')

        print('Adding Stem analyzer \n')
        self.add_new_analyzer('My_Stem_Analyzer')

        print('Adding Norm analyzer \n')
        self.add_new_analyzer('My_Norm_Analyzer')

        print('Adding N-Gram analyzer \n')
        self.add_new_analyzer('My_N-Gram_Analyzer')

        print('Adding Text analyzer \n')
        self.add_new_analyzer('My_Text_Analyzer')

        print('Adding AQL analyzer \n')
        self.add_new_analyzer('My_AQL_Analyzer')

        print('Adding Stopwords analyzer \n')
        self.add_new_analyzer('My_Stopwords_Analyzer')

        print('Adding Collation analyzer \n')
        self.add_new_analyzer('My_Collation_Analyzer')

        print('Adding Segmentation analyzer \n')
        self.add_new_analyzer('My_Segmentation_Alpha_Analyzer')

        if self.package_version >= semver.VersionInfo.parse('3.10.0'): 
            if enterprise:
                print('Adding nearest-neighbor analyzer \n')
                self.add_new_analyzer('My_Nearest_Neighbor_Analyzer', model_location)

                print('Adding classification analyzer \n')
                self.add_new_analyzer('My_Classification_Analyzer', model_location)

            print('Adding Pipeline analyzer \n')
            self.add_new_analyzer('My_Pipeline_Analyzer')

            print('Adding GeoJSON analyzer \n')
            self.add_new_analyzer('My_GeoJSON_Analyzer')

            print('Adding GeoPoint analyzer \n')
            self.add_new_analyzer('My_GeoPoint_Analyzer')

        else:
            print('Adding Pipeline analyzer \n')
            self.add_new_analyzer('My_Pipeline_Analyzer')

            print('Adding GeoJSON analyzer \n')
            self.add_new_analyzer('My_GeoJSON_Analyzer')

            print('Adding GeoPoint analyzer \n')
            self.add_new_analyzer('My_GeoPoint_Analyzer')

    
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
            close_btn = '//*[@id="modal-content-add-analyzer"]/div[3]/button[1]'
            close_btn_sitem = self.locator_finder_by_xpath(close_btn)
            close_btn_sitem.click()
            time.sleep(2)

            print(f"Expected error scenario for the {name} Completed \n")
        except Exception:
            print('Info: Error occured during checking expected error!')
    
    def analyzer_expected_error_check(self):
        """This will call all the error scenario methods"""
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

            delete_btn = f'//*[@id="modal-content-delete-_system::{analyzer_name}"]/div[3]/button[2]'
            delete_btn_sitem = self.locator_finder_by_xpath(delete_btn)
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
