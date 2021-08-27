#!/usr/bin/env python
"""
aardvark views page
"""
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By as BY

from selenium_ui_test.base_selenium import BaseSelenium

# can't circumvent long lines.. nAttr nLines
# pylint: disable=C0301 disable=R0902 disable=R0915 disable=R0904

class ViewsPage(BaseSelenium):
    """Class for View Page"""

    def __init__(self, driver):
        """View page initialization"""
        super().__init__()
        self.driver = driver
        self.select_views_tab_id = "/html//a[@id='views']"
        self.create_new_views_id = "createView"
        self.naming_new_view_id = "newName"
        self.select_create_btn_id = "//div[@id='modal-dialog']//button[@class='button-success']"
        self.select_views_settings_id = "//a[@id='viewsToggle']/span[@title='Settings']"
        self.select_sorting_views_id = "//div[@id='viewsDropdown']/ul//label[@class='checkbox checkboxLabel']"
        self.search_views_id = "/html//input[@id='viewsSearchInput']"
        self.select_first_view_id = "//*[@id='firstView']/div/h5"
        self.select_collapse_btn_id = "//*[@id='propertiesEditor']/div/div[1]/button[2]"
        self.select_expand_btn_id = "//*[@id='propertiesEditor']/div/div[1]/button[1]"
        self.select_editor_mode_btn_id = "//div[@id='propertiesEditor']//div[@class='jsoneditor-modes']" \
                                         "/button[@title='Switch editor mode']"
        self.switch_to_code_editor_mode_id = "//div[@id='propertiesEditor']//div[@class='jsoneditor-anchor']" \
                                             "//div[@class='jsoneditor-contextmenu']/ul[@class='jsoneditor-menu']" \
                                             "//button[@title='Switch to code highlighter']"
        self.compact_json_data_id = "/html//div[@id='propertiesEditor']//button[@title='Compact JSON data, " \
                                    "remove all whitespaces (Ctrl+Shift+\\)']"
        self.switch_to_tree_editor_mode_id = "//div[@id='propertiesEditor']/div[@class='jsoneditor " \
                                             "jsoneditor-mode-code']//div[@class='jsoneditor-anchor']//" \
                                             "ul[@class='jsoneditor-menu']//button[@title='Switch to tree editor']"
        self.click_arangosearch_documentation_link_id = "//div[@id='viewDocumentation']//a[@href=" \
                                                        "'https://www.arangodb.com/docs/stable" \
                                                        "/arangosearch-views.html']"
        self.select_inside_search_id = "//*[@id='propertiesEditor']/div/div[1]/table" \
                                       "/tbody/tr/td[2]/div/table/tbody/tr/td[2]/input"
        self.search_result_traverse_up_id = "/html//div[@id='propertiesEditor']/div[@class='jsoneditor " \
                                            "jsoneditor-mode-tree']//table[@class='jsoneditor-search']" \
                                            "//div[@title='Search fields and values']/table//button[@title=" \
                                            "'Previous result (Shift+Enter)']"
        self.search_result_traverse_down_id = "/html//div[@id='propertiesEditor']/div[@class=" \
                                              "'jsoneditor jsoneditor-mode-tree']//table[@class=" \
                                              "'jsoneditor-search']//div[@title=" \
                                              "'Search fields and values']/table//button[@title='Next result (Enter)']"
        self.change_consolidation_policy_id = "/html//div[@id='propertiesEditor']/div[@class=" \
                                              "'jsoneditor jsoneditor-mode-tree']/div[3]/div[@class=" \
                                              "'jsoneditor-tree']//table[@class='jsoneditor-tree']" \
                                              "/tbody/tr[16]/td[3]/table[@class='jsoneditor-values']//tr/td[4]/div"
        self.clicking_rename_views_btn_id = "renameViewButton"

        self.rename_views_name_id = "/html//input[@id='editCurrentName']"
        self.rename_views_name_confirm_id = "//div[@id='modal-dialog']//button[@class='button-success']"
        self.select_renamed_view_id = "/html//div[@id='thirdView']"
        self.delete_views_btn_id = "deleteViewButton"
        self.delete_views_confirm_btn_id = "//div[@id='modal-dialog']//button[@class='button-danger']"
        self.final_delete_confirmation_id = "modal-confirm-delete"
        self.select_second_view_id = "//div[@id='secondView']//h5[@class='collectionName']"

    def select_views_tab(self):
        """selecting views tab"""
        self.navbar_goto('views')

    def create_new_views(self):
        """creating new views tab"""
        create_new_views_sitem = \
            self.locator_finder_by_id(self.create_new_views_id)
        create_new_views_sitem.click()

    def naming_new_view(self, name):
        """naming new views"""
        naming_new_view_sitem = \
            self.locator_finder_by_id(self.naming_new_view_id)
        naming_new_view_sitem.click()
        naming_new_view_sitem.send_keys(name)

    def select_create_btn(self):
        """creating new views tab"""
        select_create_btn_sitem = \
            self.locator_finder_by_xpath(self.select_create_btn_id)
        select_create_btn_sitem.click()
        time.sleep(2)

    def select_views_settings(self):
        """selecting view setting"""
        select_views_settings_sitem = \
            self.locator_finder_by_xpath(self.select_views_settings_id)
        select_views_settings_sitem.click()
        time.sleep(3)

    def select_sorting_views(self):
        """sorting multiple views into descending"""
        select_sorting_views_sitem = \
            self.locator_finder_by_xpath(self.select_sorting_views_id)
        select_sorting_views_sitem.click()
        time.sleep(3)

    def search_views(self, search):
        """searching views"""
        search_views_sitem = self.locator_finder_by_xpath(self.search_views_id)
        search_views_sitem.click()
        search_views_sitem.clear()
        search_views_sitem.send_keys(search)
        time.sleep(3)

    def select_first_view(self):
        """selecting first view"""
        select_first_view_sitem = \
            self.locator_finder_by_xpath(self.select_first_view_id)
        select_first_view_sitem.click()

    def select_collapse_btn(self):
        """selecting collapse all btn"""
        select_collapse_btn_sitem = \
            self.locator_finder_by_xpath(self.select_collapse_btn_id)
        select_collapse_btn_sitem.click()
        time.sleep(3)

    def select_expand_btn(self):
        """selecting expand all btn"""
        select_expand_btn_sitem = self.locator_finder_by_xpath(self.select_expand_btn_id)
        select_expand_btn_sitem.click()
        time.sleep(3)

    def select_editor_mode_btn(self):
        """selecting object tabs"""
        select_editor_mode_btn_sitem = \
            self.locator_finder_by_xpath(self.select_editor_mode_btn_id)
        select_editor_mode_btn_sitem.click()
        time.sleep(3)

    def switch_to_code_editor_mode(self):
        """switching editor mode to Code"""
        switch_to_code_editor_mode_sitem = \
            self.locator_finder_by_xpath(self.switch_to_code_editor_mode_id)
        switch_to_code_editor_mode_sitem.click()
        time.sleep(3)

    def compact_json_data(self):
        """switching editor mode to Code compact view"""
        self.compact_json_data_id = \
            self.locator_finder_by_xpath(self.compact_json_data_id)
        self.compact_json_data_id.click()
        time.sleep(3)

    def switch_to_tree_editor_mode(self):
        """switching editor mode to Tree"""
        switch_to_tree_editor_mode_sitem = \
            self.locator_finder_by_xpath(self.switch_to_tree_editor_mode_id)
        switch_to_tree_editor_mode_sitem.click()
        time.sleep(3)

    def click_arangosearch_documentation_link(self):
        """Clicking on arangosearch documentation link"""
        click_arangosearch_documentation_link_sitem = \
            self.locator_finder_by_xpath(self.click_arangosearch_documentation_link_id)
        title = self.switch_tab(click_arangosearch_documentation_link_sitem)
        expected_title = 'Views Reference | ArangoSearch | Indexing | Manual | ArangoDB Documentation'
        assert title in expected_title, f"Expected page title {expected_title} but got {title}"

    def select_inside_search(self, keyword):
        """Selecting search option inside views"""
        select_inside_search_sitem = self.locator_finder_by_xpath(self.select_inside_search_id)
        select_inside_search_sitem.click()
        select_inside_search_sitem.clear()
        select_inside_search_sitem.send_keys(keyword)

    def search_result_traverse_down(self):
        """traverse search results down"""
        search_result_traverse_down_sitem = \
            self.locator_finder_by_xpath(self.search_result_traverse_down_id)
        for _ in range(8):
            search_result_traverse_down_sitem.click()
            time.sleep(1)

    def search_result_traverse_up(self):
        """traverse search results up"""
        search_result_traverse_up_sitem = \
            self.locator_finder_by_xpath(self.search_result_traverse_up_id)
        for _ in range(8):
            search_result_traverse_up_sitem.click()
            time.sleep(1)

    def change_consolidation_policy(self, number):
        """Changing views properties"""
        change_consolidation_policy_sitem = \
            self.locator_finder_by_xpath(self.change_consolidation_policy_id)
        change_consolidation_policy_sitem.click()
        change_consolidation_policy_sitem.clear()
        change_consolidation_policy_sitem.send_keys(number)
        time.sleep(5)

    def clicking_rename_views_btn(self):
        """Select Views rename btn"""
        clicking_rename_views_btn_sitem = \
            self.locator_finder_by_id(self.clicking_rename_views_btn_id)
        clicking_rename_views_btn_sitem.click()

    def rename_views_name(self, name):
        """changing view name"""
        rename_views_name_sitem = \
            self.locator_finder_by_xpath(self.rename_views_name_id)
        rename_views_name_sitem.click()
        rename_views_name_sitem.clear()
        rename_views_name_sitem.send_keys(name)

    def rename_views_name_confirm(self):
        """Confirm rename views"""
        rename_views_name_confirm_sitem = \
            self.locator_finder_by_xpath(self.rename_views_name_confirm_id)
        rename_views_name_confirm_sitem.click()
        time.sleep(3)

    def select_renamed_view(self):
        """select renamed view for deleting"""
        select_renamed_view_sitem = \
            self.locator_finder_by_xpath(self.select_renamed_view_id)
        select_renamed_view_sitem.click()

    def delete_views_btn(self):
        """select delete button"""
        delete_views_btn_sitem = \
            self.locator_finder_by_id(self.delete_views_btn_id)
        delete_views_btn_sitem.click()

    def delete_views_confirm_btn(self):
        """Confirm deletion of the current views"""
        # delete_views_confirm_btn_sitem = self.locator_finder_by_xpath(self.delete_views_confirm_btn_id)
        delete_views_confirm_btn_sitem = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((BY.XPATH, self.delete_views_confirm_btn_id)))
        delete_views_confirm_btn_sitem.click()

    def final_delete_confirmation(self):
        """Final confirmation of deletion"""
        final_delete_confirmation_sitem = \
            self.locator_finder_by_id(self.final_delete_confirmation_id)
        final_delete_confirmation_sitem.click()

    def select_second_view(self):
        """selecting second view"""
        select_second_view_sitem = \
            self.locator_finder_by_xpath(self.select_second_view_id)
        select_second_view_sitem.click()
