import time
from baseSelenium import BaseSelenium


class ViewsPage(BaseSelenium):

    def __init__(self, driver):
        super().__init__()
        self.driver = driver
        self.select_views_tab_id = "/html//a[@id='views']"
        self.create_new_views_id = "/html//a[@id='createView']"
        self.naming_new_view_id = "/html//input[@id='newName']"
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
                                    "remove all whitespaces (Ctrl+Shift+\)']"
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

    # selecting views tab
    def select_views_tab(self):
        self.select_views_tab_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.select_views_tab_id)
        self.select_views_tab_id.click()

    # creating new views tab
    def create_new_views(self):
        self.create_new_views_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.create_new_views_id)
        self.create_new_views_id.click()

    # naming new views
    def naming_new_view(self, name):
        self.naming_new_view_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.naming_new_view_id)
        self.naming_new_view_id.click()
        self.naming_new_view_id.send_keys(name)

    # creating new views tab
    def select_create_btn(self):
        self.select_create_btn_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.select_create_btn_id)
        self.select_create_btn_id.click()
        time.sleep(2)

    # selecting view setting
    def select_views_settings(self):
        self.select_views_settings_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.select_views_settings_id)
        self.select_views_settings_id.click()
        time.sleep(3)

    # sorting multiple views into descending
    def select_sorting_views(self):
        self.select_sorting_views_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.select_sorting_views_id)
        self.select_sorting_views_id.click()
        time.sleep(3)

    # searching views
    def search_views(self, search):
        self.search_views_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.search_views_id)
        self.search_views_id.click()
        self.search_views_id.clear()
        self.search_views_id.send_keys(search)
        time.sleep(3)

    # selecting first view
    def select_first_view(self):
        self.select_first_view_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.select_first_view_id)
        self.select_first_view_id.click()

    # selecting collapse all btn
    def select_collapse_btn(self):
        self.select_collapse_btn_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.select_collapse_btn_id)
        self.select_collapse_btn_id.click()
        time.sleep(3)

    # selecting expand all btn
    def select_expand_btn(self):
        self.select_expand_btn_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.select_expand_btn_id)
        self.select_expand_btn_id.click()
        time.sleep(3)

    # selecting object tabs
    def select_editor_mode_btn(self):
        self.select_editor_mode_btn_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.select_editor_mode_btn_id)
        self.select_editor_mode_btn_id.click()
        time.sleep(3)

    # switching editor mode to Code
    def switch_to_code_editor_mode(self):
        self.switch_to_code_editor_mode_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.switch_to_code_editor_mode_id)
        self.switch_to_code_editor_mode_id.click()
        time.sleep(3)

    # switching editor mode to Code compact view
    def compact_json_data(self):
        self.compact_json_data_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.compact_json_data_id)
        self.compact_json_data_id.click()
        time.sleep(3)

    # switching editor mode to Tree
    def switch_to_tree_editor_mode(self):
        self.switch_to_tree_editor_mode_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.switch_to_tree_editor_mode_id)
        self.switch_to_tree_editor_mode_id.click()
        time.sleep(3)

    # Clicking on arangosearch documentation link
    def click_arangosearch_documentation_link(self):
        self.click_arangosearch_documentation_link_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.click_arangosearch_documentation_link_id)
        self.switch_tab(self.click_arangosearch_documentation_link_id)

    # Selecting search option inside views
    def select_inside_search(self, keyword):
        self.select_inside_search_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.select_inside_search_id)
        self.select_inside_search_id.click()
        self.select_inside_search_id.clear()
        self.select_inside_search_id.send_keys(keyword)

    # traverse search results down
    def search_result_traverse_down(self):
        self.search_result_traverse_down_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.search_result_traverse_down_id)
        for x in range(8):
            self.search_result_traverse_down_id.click()
            time.sleep(1)

    # traverse search results up
    def search_result_traverse_up(self):
        self.search_result_traverse_up_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.search_result_traverse_up_id)
        for x in range(8):
            self.search_result_traverse_up_id.click()
            time.sleep(1)

    # Changing views properties
    def change_consolidation_policy(self, number):
        self.change_consolidation_policy_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.change_consolidation_policy_id)
        self.change_consolidation_policy_id.click()
        self.change_consolidation_policy_id.clear()
        self.change_consolidation_policy_id.send_keys(number)
        time.sleep(5)

    # Select Views rename btn
    def clicking_rename_views_btn(self):
        self.clicking_rename_views_btn_id = \
            BaseSelenium.locator_finder_by_id(self, self.clicking_rename_views_btn_id)
        self.clicking_rename_views_btn_id.click()

    # changing view name
    def rename_views_name(self, name):
        self.rename_views_name_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.rename_views_name_id)
        self.rename_views_name_id.click()
        self.rename_views_name_id.clear()
        self.rename_views_name_id.send_keys(name)

    # Confirm rename views
    def rename_views_name_confirm(self):
        self.rename_views_name_confirm_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.rename_views_name_confirm_id)
        self.rename_views_name_confirm_id.click()
        time.sleep(3)

    # select renamed view for deleting
    def select_renamed_view(self):
        self.select_renamed_view_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.select_renamed_view_id)
        self.select_renamed_view_id.click()

    # select delete button
    def delete_views_btn(self):
        self.delete_views_btn_id = \
            BaseSelenium.locator_finder_by_id(self, self.delete_views_btn_id)
        self.delete_views_btn_id.click()

    # Confirm deletion of the current views
    def delete_views_confirm_btn(self):
        self.delete_views_confirm_btn_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.delete_views_confirm_btn_id)
        self.delete_views_confirm_btn_id.click()

    # Final confirmation of deletion
    def final_delete_confirmation(self):
        self.final_delete_confirmation_id = \
            BaseSelenium.locator_finder_by_id(self, self.final_delete_confirmation_id)
        self.final_delete_confirmation_id.click()

    # selecting second view
    def select_second_view(self):
        self.select_second_view_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.select_second_view_id)
        self.select_second_view_id.click()
