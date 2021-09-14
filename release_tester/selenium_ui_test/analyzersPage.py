import time

from baseSelenium import BaseSelenium
from selenium.webdriver.common.keys import Keys


class AnalyzerPage(BaseSelenium):

    def __init__(self, driver):
        super().__init__()
        self.driver = driver
        self.analyzers_page = 'analyzers'  # list of in-built analyzers
        self.in_built_analyzer = "inbuilt-analyzers"
        self.add_new_analyzer_btn = '//*[@id="analyzersContent"]/div/div/div/div[1]/div/button/i'
        self.identity_analyzer = '//*[@id="analyzersContent"]/div/div/table/tbody/tr[1]/td[4]/button/i'
        self.identity_analyzer_switch_view = '/html/body/div[14]/div/div[1]/div/div[2]/button'
        self.close_identity_btn = '/html/body/div[14]/div/div[3]/button'

        self.text_de = '//*[@id="analyzersContent"]/div/div/table/tbody/tr[2]/td[4]/button/i'
        self.text_de_switch_view = '/html/body/div[16]/div/div[1]/div/div[2]/button'
        self.close_text_de_btn = '/html/body/div[16]/div/div[3]/button'

        self.text_en = '//*[@id="analyzersContent"]/div/div/table/tbody/tr[3]/td[4]/button/i'
        self.text_en_switch_view = '/html/body/div[18]/div/div[1]/div/div[2]/button'
        self.close_text_en_btn = '/html/body/div[18]/div/div[3]/button'

        self.text_es = '//*[@id="analyzersContent"]/div/div/table/tbody/tr[4]/td[4]/button/i'
        self.text_es_switch_view = '/html/body/div[20]/div/div[1]/div/div[2]/button'
        self.close_text_es_btn = '/html/body/div[20]/div/div[3]/button'

        self.text_fi = '//*[@id="analyzersContent"]/div/div/table/tbody/tr[5]/td[4]/button/i'
        self.text_fi_switch_view = '/html/body/div[22]/div/div[1]/div/div[2]/button'
        self.close_text_fi_btn = '/html/body/div[22]/div/div[3]/button'

        self.text_fr = '//*[@id="analyzersContent"]/div/div/table/tbody/tr[6]/td[4]/button/i'
        self.text_fr_switch_view = '/html/body/div[24]/div/div[1]/div/div[2]/button'
        self.close_text_fr_btn = '/html/body/div[24]/div/div[3]/button'

        self.text_it = '//*[@id="analyzersContent"]/div/div/table/tbody/tr[7]/td[4]/button/i'
        self.text_it_switch_view = '/html/body/div[26]/div/div[1]/div/div[2]/button'
        self.close_text_it_btn = '/html/body/div[26]/div/div[3]/button'

        self.text_nl = '//*[@id="analyzersContent"]/div/div/table/tbody/tr[8]/td[4]/button/i'
        self.text_nl_switch_view = '/html/body/div[28]/div/div[1]/div/div[2]/button'
        self.close_text_nl_btn = '/html/body/div[28]/div/div[3]/button'

        self.text_no = '//*[@id="analyzersContent"]/div/div/table/tbody/tr[9]/td[4]/button/i'
        self.text_no_switch_view = '/html/body/div[30]/div/div[1]/div/div[2]/button'
        self.close_text_no_btn = '/html/body/div[30]/div/div[3]/button'

        self.text_pt = '//*[@id="analyzersContent"]/div/div/table/tbody/tr[10]/td[4]/button/i'
        self.text_pt_switch_view = '/html/body/div[32]/div/div[1]/div/div[2]/button'
        self.close_text_pt_btn = '/html/body/div[32]/div/div[3]/button'

        self.text_ru = '//*[@id="analyzersContent"]/div/div/table/tbody/tr[11]/td[4]/button/i'
        self.text_ru_switch_view = '/html/body/div[34]/div/div[1]/div/div[2]/button'
        self.close_text_ru_btn = '/html/body/div[34]/div/div[3]/button'

        self.text_sv = '//*[@id="analyzersContent"]/div/div/table/tbody/tr[12]/td[4]/button/i'
        self.text_sv_switch_view = '/html/body/div[36]/div/div[1]/div/div[2]/button'
        self.close_text_sv_btn = '/html/body/div[36]/div/div[3]/button'

        self.text_zh = '//*[@id="analyzersContent"]/div/div/table/tbody/tr[13]/td[4]/button/i'
        self.text_zh_switch_view = '/html/body/div[38]/div/div[1]/div/div[2]/button'
        self.close_text_zh_btn = '/html/body/div[38]/div/div[3]/button'

    def select_analyzers_page(self):
        """Selecting analyzers page"""
        print("Selecting Analyzers page \n")
        analyzer = self.analyzers_page
        analyzer_sitem = BaseSelenium.locator_finder_by_id(self, analyzer)
        analyzer_sitem.click()
        time.sleep(2)

    def select_help_filter_btn(self):
        """Selecting help button"""
        print("Selecting Analyzers help filter button \n")
        help_filter = '//*[@id="analyzersContent"]/div/div/div/div[2]/a/i'
        help_sitem = BaseSelenium.locator_finder_by_xpath(self, help_filter)
        help_sitem.click()
        time.sleep(3)

        print("Closing Analyzers help filter1 \n")
        help_filter_close = '//*[@id="modal-content-3"]/div[3]/button'
        help_close_sitem = BaseSelenium.locator_finder_by_xpath(self, help_filter_close)
        help_close_sitem.click()
        time.sleep(2)

    def select_built_in_analyzers(self):
        """Checking in-built analyzers list and description"""
        show_built_in_analyzers = self.in_built_analyzer
        show_built_in_analyzers_sitem = BaseSelenium.locator_finder_by_id(self, show_built_in_analyzers)
        show_built_in_analyzers_sitem.click()
        time.sleep(2)

    def select_analyzer_to_check(self, analyzer_name, analyzer_view, close_btn):
        """Checking in-built analyzers one by one"""
        print('Selecting analyzer from the in-built analyzers list \n')
        analyzer_name = analyzer_name
        identity_sitem = BaseSelenium.locator_finder_by_xpath(self, analyzer_name)
        identity_sitem.click()
        time.sleep(2)

        print('Switch to Code view \n')
        switch_to_code_view = analyzer_view
        code_view_sitem = BaseSelenium.locator_finder_by_xpath(self, switch_to_code_view)
        code_view_sitem.click()
        time.sleep(2)

        print('Switch to form view \n')
        switch_to_form_view = analyzer_view
        form_view_sitem = BaseSelenium.locator_finder_by_xpath(self, switch_to_form_view)
        form_view_sitem.click()
        time.sleep(2)

        print('Closing the analyzer \n')
        close_button = close_btn
        close_sitem = BaseSelenium.locator_finder_by_xpath(self, close_button)
        close_sitem.click()
        time.sleep(2)

    def add_new_analyzer(self, name, index):
        """Adding analyzer type delimiter with necessary features"""
        print('Selecting add new analyzer button \n')
        self.select_analyzers_page()
        add_analyzer = self.add_new_analyzer_btn
        add_analyzer_sitem = BaseSelenium.locator_finder_by_xpath(self, add_analyzer)
        add_analyzer_sitem.click()
        time.sleep(2)

        # assigning variables to none for future use
        analyzer_name = analyzer_type = frequency = norm = position = switch_view_btn = create = None

        if index == 0:
            print('Creating Identity analyzer started \n')
            analyzer_name = '/html/body/div[12]/div/div[2]/div/div[1]/fieldset/div/div[1]/input'
            analyzer_type = '/html/body/div[12]/div/div[2]/div/div[1]/fieldset/div/div[2]/select'
            frequency = '/html/body/div[12]/div/div[2]/div/div[3]/fieldset/div/div[1]/input'
            norm = '/html/body/div[12]/div/div[2]/div/div[3]/fieldset/div/div[2]/input'
            position = '/html/body/div[12]/div/div[2]/div/div[3]/fieldset/div/div[3]/input'
            switch_view_btn = '/html/body/div[12]/div/div[1]/div/div[2]/div/div[2]/button'
            create = '/html/body/div[12]/div/div[3]/button[2]'

        elif index == 1:
            print('Creating Delimiter analyzer started \n')
            analyzer_name = '/html/body/div[16]/div/div[2]/div/div[1]/fieldset/div/div[1]/input'
            analyzer_type = '/html/body/div[16]/div/div[2]/div/div[1]/fieldset/div/div[2]/select'
            frequency = '/html/body/div[16]/div/div[2]/div/div[3]/fieldset/div/div[1]/input'
            norm = '/html/body/div[16]/div/div[2]/div/div[3]/fieldset/div/div[2]/input'
            position = '/html/body/div[16]/div/div[2]/div/div[3]/fieldset/div/div[3]/input'
            switch_view_btn = '/html/body/div[16]/div/div[1]/div/div[2]/div/div[2]/button'
            create = '/html/body/div[16]/div/div[3]/button[2]'

        elif index == 2:
            print('Creating Stem analyzer started \n')
            analyzer_name = '/html/body/div[20]/div/div[2]/div/div[1]/fieldset/div/div[1]/input'
            analyzer_type = '/html/body/div[20]/div/div[2]/div/div[1]/fieldset/div/div[2]/select'
            frequency = '/html/body/div[20]/div/div[2]/div/div[3]/fieldset/div/div[1]/input'
            norm = '/html/body/div[20]/div/div[2]/div/div[3]/fieldset/div/div[2]/input'
            position = '/html/body/div[20]/div/div[2]/div/div[3]/fieldset/div/div[3]/input'
            switch_view_btn = '/html/body/div[20]/div/div[1]/div/div[2]/div/div[2]/button'
            create = '/html/body/div[20]/div/div[3]/button[2]'

        elif index == 3:
            print('Creating Norm analyzer started \n')
            analyzer_name = '/html/body/div[24]/div/div[2]/div/div[1]/fieldset/div/div[1]/input'
            analyzer_type = '/html/body/div[24]/div/div[2]/div/div[1]/fieldset/div/div[2]/select'
            frequency = '/html/body/div[24]/div/div[2]/div/div[3]/fieldset/div/div[1]/input'
            norm = '/html/body/div[24]/div/div[2]/div/div[3]/fieldset/div/div[2]/input'
            position = '/html/body/div[24]/div/div[2]/div/div[3]/fieldset/div/div[3]/input'
            switch_view_btn = '/html/body/div[24]/div/div[1]/div/div[2]/div/div[2]/button'
            create = '/html/body/div[24]/div/div[3]/button[2]'

        elif index == 4:
            print('Creating N-Gram analyzer started \n')
            analyzer_name = '/html/body/div[28]/div/div[2]/div/div[1]/fieldset/div/div[1]/input'
            analyzer_type = '/html/body/div[28]/div/div[2]/div/div[1]/fieldset/div/div[2]/select'
            frequency = '/html/body/div[28]/div/div[2]/div/div[3]/fieldset/div/div[1]/input'
            norm = '/html/body/div[28]/div/div[2]/div/div[3]/fieldset/div/div[2]/input'
            position = '/html/body/div[28]/div/div[2]/div/div[3]/fieldset/div/div[3]/input'
            switch_view_btn = '/html/body/div[28]/div/div[1]/div/div[2]/div/div[2]/button'
            create = '/html/body/div[28]/div/div[3]/button[2]'

        elif index == 5:
            print('Creating Text analyzer started \n')
            analyzer_name = '/html/body/div[32]/div/div[2]/div/div[1]/fieldset/div/div[1]/input'
            analyzer_type = '/html/body/div[32]/div/div[2]/div/div[1]/fieldset/div/div[2]/select'
            frequency = '/html/body/div[32]/div/div[2]/div/div[3]/fieldset/div/div[1]/input'
            norm = '/html/body/div[32]/div/div[2]/div/div[3]/fieldset/div/div[2]/input'
            position = '/html/body/div[32]/div/div[2]/div/div[3]/fieldset/div/div[3]/input'
            switch_view_btn = '/html/body/div[32]/div/div[1]/div/div[2]/div/div[2]/button'
            create = '/html/body/div[32]/div/div[3]/button[2]'

        analyzer_name_sitem = BaseSelenium.locator_finder_by_xpath(self, analyzer_name)
        analyzer_name_sitem.click()
        analyzer_name_sitem.clear()
        analyzer_name_sitem.send_keys(name)
        time.sleep(2)

        print('Selecting analyzer type \n')
        BaseSelenium.locator_finder_by_select_using_xpath(self, analyzer_type, index)
        time.sleep(2)

        print('selecting frequency \n')
        frequency_sitem = BaseSelenium.locator_finder_by_xpath(self, frequency)
        frequency_sitem.click()
        time.sleep(2)

        print('selecting norm \n')
        norm_sitem = BaseSelenium.locator_finder_by_xpath(self, norm)
        norm_sitem.click()
        time.sleep(2)

        print('selecting position \n')
        position_sitem = BaseSelenium.locator_finder_by_xpath(self, position)
        position_sitem.click()
        time.sleep(2)

        # ------------------ here all the different configuration would be given----------------------
        print('selecting value for the placeholder \n')
        # for delimiter
        if index == 1:
            delimiter = '/html/body/div[16]/div/div[2]/div/div[4]/fieldset/div/div/input'
            value = '_'
            delimiter_sitem = BaseSelenium.locator_finder_by_xpath(self, delimiter)
            delimiter_sitem.click()
            delimiter_sitem.clear()
            delimiter_sitem.send_keys(value)
        # for stem
        elif index == 2:
            locale = '/html/body/div[20]/div/div[2]/div/div[4]/fieldset/div/div/input'
            value = 'en_US.utf-8'
            locale_sitem = BaseSelenium.locator_finder_by_xpath(self, locale)
            locale_sitem.click()
            locale_sitem.clear()
            locale_sitem.send_keys(value)
        # for norm
        elif index == 3:
            locale = '/html/body/div[24]/div/div[2]/div/div[4]/fieldset/div/div[1]/input'
            value = 'en_US.utf-8'
            locale_sitem = BaseSelenium.locator_finder_by_xpath(self, locale)
            locale_sitem.click()
            locale_sitem.clear()
            locale_sitem.send_keys(value)
        # for N-Gram
        elif index == 4:
            pass
        # for text
        elif index == 5:
            locale = '/html/body/div[32]/div/div[2]/div/div[4]/fieldset/div/div[1]/div/div[1]/input'
            value = 'en_US.utf-8'
            locale_sitem = BaseSelenium.locator_finder_by_xpath(self, locale)
            locale_sitem.click()
            locale_sitem.clear()
            locale_sitem.send_keys(value)
            time.sleep(2)

        # ---------------extra feature for norm analyzer-------------------
        if index == 3:
            print('Selecting case for norm analyzer using index value \n')
            case = '/html/body/div[24]/div/div[2]/div/div[4]/fieldset/div/div[2]/select'
            BaseSelenium.locator_finder_by_select_using_xpath(self, case, 0)

            print('Selecting accent for norm analyzer \n')
            accent = '/html/body/div[24]/div/div[2]/div/div[4]/fieldset/div/div[3]/input'
            accent_sitem = BaseSelenium.locator_finder_by_xpath(self, accent)
            accent_sitem.click()
            time.sleep(2)

        if index == 4:
            print('Adding minimum n-gram length \n')
            min_length = '/html/body/div[28]/div/div[2]/div/div[4]/fieldset/div/div[1]/div/div[1]/input'
            min_length_sitem = BaseSelenium.locator_finder_by_xpath(self, min_length)
            min_length_sitem.click()
            min_length_sitem.clear()
            min_length_sitem.send_keys('2')
            time.sleep(2)

            print('Adding minimum n-gram length \n')
            max_length = '/html/body/div[28]/div/div[2]/div/div[4]/fieldset/div/div[1]/div/div[1]/input'
            max_length_sitem = BaseSelenium.locator_finder_by_xpath(self, max_length)
            max_length_sitem.click()
            max_length_sitem.clear()
            max_length_sitem.send_keys('3')
            time.sleep(2)

            print('Preserve original value \n')
            preserve = '/html/body/div[28]/div/div[2]/div/div[4]/fieldset/div/div[1]/div/div[3]/input'
            preserve_sitem = BaseSelenium.locator_finder_by_xpath(self, preserve)
            preserve_sitem.click()
            time.sleep(2)

            print('Start marker value \n')
            start_marker = '/html/body/div[28]/div/div[2]/div/div[4]/fieldset/div/div[2]/input'
            start_marker_sitem = BaseSelenium.locator_finder_by_xpath(self, start_marker)
            start_marker_sitem.click()
            start_marker_sitem.clear()
            start_marker_sitem.send_keys('^')
            time.sleep(2)

            print('End marker value \n')
            end_marker = '/html/body/div[28]/div/div[2]/div/div[4]/fieldset/div/div[3]/input'
            end_marker_sitem = BaseSelenium.locator_finder_by_xpath(self, end_marker)
            end_marker_sitem.click()
            end_marker_sitem.clear()
            end_marker_sitem.send_keys('$')
            time.sleep(2)

            print('Stream type selection using index value \n')
            stream_type = '/html/body/div[28]/div/div[2]/div/div[4]/fieldset/div/div[4]/select'
            BaseSelenium.locator_finder_by_select_using_xpath(self, stream_type, 1)
            time.sleep(2)
        # for text analyzer
        if index == 5:
            # print('Selecting path for stopwords \n')
            # stopwords_path = '/html/body/div[32]/div/div[2]/div/div[4]/fieldset/div/div[2]/div/div[1]/input'
            # stopwords_path_sitem = BaseSelenium.locator_finder_by_xpath(self, stopwords_path)
            # stopwords_path_sitem.click()
            # stopwords_path_sitem.clear()
            # stopwords_path_sitem.send_keys('/home/username/Desktop/')

            print('Selecting stopwords for the analyzer \n')
            stopwords = '/html/body/div[32]/div/div[2]/div/div[4]/fieldset/div/div[1]/div/div[2]/textarea'
            stopwords_sitem = BaseSelenium.locator_finder_by_xpath(self, stopwords)
            stopwords_sitem.clear()
            stopwords_sitem.send_keys('the')
            stopwords_sitem.send_keys(Keys.ENTER)
            stopwords_sitem.send_keys('of')
            stopwords_sitem.send_keys(Keys.ENTER)
            stopwords_sitem.send_keys('a')

            print('Selecting case for the analyzer from the dropdown menu \n')
            case = '/html/body/div[32]/div/div[2]/div/div[4]/fieldset/div/div[2]/div/div[2]/select'
            BaseSelenium.locator_finder_by_select_using_xpath(self, case, 1)

            print('Selecting stem for the analyzer \n')
            stem = '/html/body/div[32]/div/div[2]/div/div[4]/fieldset/div/div[2]/div/div[3]/input'
            stem_sitem = BaseSelenium.locator_finder_by_xpath(self, stem)
            stem_sitem.click()
            time.sleep(2)

            print('Selecting accent for the analyzer \n')
            accent = '/html/body/div[32]/div/div[2]/div/div[4]/fieldset/div/div[2]/div/div[4]/input'
            accent_sitem = BaseSelenium.locator_finder_by_xpath(self, accent)
            accent_sitem.click()
            time.sleep(2)

        # after initialize basic configuration this method will finalize the creation
        switch_view = switch_view_btn

        print('Switching current view to form view \n')
        code_view = switch_view
        code_view_sitem = BaseSelenium.locator_finder_by_xpath(self, code_view)
        code_view_sitem.click()
        time.sleep(3)

        print('Switching current view to code view \n')
        form_view = switch_view
        form_view_sitem = BaseSelenium.locator_finder_by_xpath(self, form_view)
        form_view_sitem.click()
        time.sleep(3)

        print('Creating the analyzer \n')
        create_btn = create
        create_btn_sitem = BaseSelenium.locator_finder_by_xpath(self, create_btn)
        create_btn_sitem.click()
        time.sleep(4)

        print('Creating analyzer completed \n')
