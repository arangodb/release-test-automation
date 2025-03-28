#!/usr/bin/python3
"""page object for views editing"""
import time
import traceback
import semver

from selenium_ui_test.pages.navbar import NavigationBarPage
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException, TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

# can't circumvent long lines.. nAttr nLines
# pylint: disable=line-too-long disable=too-many-instance-attributes disable=too-many-statements disable=too-many-public-methods
# pylint: disable=too-many-lines disable=too-many-locals


class ViewsPage(NavigationBarPage):
    """Class for View Page"""

    # views id after creation
    select_improved_arangosearch_view_01 = "//h5[contains(text(),'improved_arangosearch_view_01')]"
    select_improved_arangosearch_view_02 = "//h5[contains(text(),'improved_arangosearch_view_02')]"
    select_modified_views_name = "//h5[contains(text(),'modified_views_name')]"

    search_first_view = '//*[@id="firstView"]/div/h5'
    search_second_view = '//*[@id="secondView"]/div/h5'

    select_renamed_view_id = "/html//div[@id='thirdView']"
    select_second_view_id = "//div[@id='secondView']//h5[@class='collectionName']"

    def __init__(self, driver, cfg, video_start_time):
        """View page initialization"""
        super().__init__(driver, cfg, video_start_time)
        self.current_version = self.current_package_version()
        self.testing_version = semver.VersionInfo.parse("3.9.100")
        self.select_views_tab_id = "views"
        self.create_new_view = 'createView'
        self.naming_new_view_id = '//input[@id="name"]'
        self.select_create_btn_id = "//div[@id='modal-dialog']//button[@class='button-success']"
        self.select_views_settings_id = "//a[@id='viewsToggle']/span[@title='Settings']"
        self.select_sorting_views_id = '//*[@id="viewsDropdown"]/ul/li[2]/a/label/i'

        self.search_views_id = "/html//input[@id='viewsSearchInput']"
        self.select_first_view_id = "//*[@id='firstView']/div/h5"
        self.select_collapse_btn_id = "//*[@id='propertiesEditor']/div/div[1]/button[2]"
        self.select_expand_btn_id = "//*[@id='propertiesEditor']/div/div[1]/button[1]"
        self.select_editor_mode_btn_id = (
            "//div[@id='propertiesEditor']//div[@class='jsoneditor-modes']/button[@title='Switch editor mode']"
        )
        self.switch_to_code_editor_mode_id = "//*[text()='Code']"
        self.compact_json_data_id = "jsoneditor-compact"
        self.switch_to_tree_editor_mode_id = "//*[text()='Tree']"
        self.select_inside_search_id = '//tbody//tr//td//input'
        self.search_result_traverse_up_id = "jsoneditor-previous"
        self.search_result_traverse_down_id = "jsoneditor-next"
        self.clicking_rename_views_btn_id = "renameViewButton"

        self.rename_views_name_id = "/html//input[@id='editCurrentName']"
        self.rename_views_name_confirm_id = "//div[@id='modal-dialog']//button[@class='button-success']"

        self.delete_views_btn_id = "deleteViewButton"
        self.delete_views_confirm_btn_id = "//div[@id='modal-dialog']//button[@class='button-danger']"
        self.final_delete_confirmation_id = "modal-confirm-delete"

    def select_views_tab(self):
        """selecting views tab"""
        create_new_views_sitem = self.locator_finder_by_id(self.select_views_tab_id)
        create_new_views_sitem.click()

    def select_views_settings(self):
        """selecting view setting"""
        select_views_settings_sitem = self.locator_finder_by_xpath(self.select_views_settings_id, benchmark=True)
        select_views_settings_sitem.click()
        time.sleep(3)
        self.wait_for_ajax()

    def select_sorting_views(self):
        """sorting multiple views into descending"""
        select_sorting_views_sitem = self.locator_finder_by_xpath(self.select_sorting_views_id, benchmark=True)
        select_sorting_views_sitem.click()
        time.sleep(3)
        self.wait_for_ajax()

    def search_views(self, expected_text, search_locator):
        """ iterate search views """
        search_views = self.search_views_id
        for _ in range(3):
            try:
                search_views_sitem = self.locator_finder_by_xpath(search_views, benchmark=True)
                search_views_sitem.click()
                search_views_sitem.clear()
                search_views_sitem.send_keys(expected_text)
                time.sleep(2)
                self.wait_for_ajax()
                break
            except StaleElementReferenceException:
                self.tprint('stale element found, trying again\n')
            except NoSuchElementException:
                self.tprint("Can't find the view, trying again\n")
            except TimeoutException as ex:
                raise ex
            self.webdriver.refresh()

        self.tprint(f'Checking that we get the right results for {expected_text}\n')
        if self.current_package_version() <= semver.VersionInfo.parse("3.8.100"):
            if expected_text == 'firstView':
                found = self.locator_finder_by_xpath(search_locator).text
                assert found == expected_text, f"Expected views title {expected_text} but got {found}"
            elif expected_text == 'secondView':
                found = self.locator_finder_by_xpath(search_locator).text
                assert found == expected_text, f"Expected views title {expected_text} but got {found}"
        else:
            if expected_text == 'improved_arangosearch_view_01':
                found = self.locator_finder_by_xpath(search_locator).text
                assert found == expected_text, f"Expected views title {expected_text} but got {found}"
                time.sleep(2)
                self.wait_for_ajax()
            elif expected_text == 'improved_arangosearch_view_02':
                found = self.locator_finder_by_xpath(search_locator).text
                assert found == expected_text, f"Expected views title {expected_text} but got {found}"
                time.sleep(2)
                self.wait_for_ajax()
        self.webdriver.refresh()

    def select_first_view(self):
        """selecting first view"""
        select_first_view_sitem = self.locator_finder_by_xpath(self.select_first_view_id, benchmark=True)
        select_first_view_sitem.click()

    def select_collapse_btn(self):
        """selecting collapse btn"""
        if self.current_version > self.testing_version:
            collapse_btn = 'jsoneditor-compact'
            select_collapse_btn_sitem = self.locator_finder_by_class(collapse_btn)
        else:
            select_collapse_btn_sitem = self.locator_finder_by_xpath(self.select_collapse_btn_id, benchmark=True)
        select_collapse_btn_sitem.click()
        time.sleep(3)
        self.wait_for_ajax()

    def select_expand_btn(self):
        """selecting expand all btn"""
        if self.current_version > self.testing_version:
            expand_btn = 'jsoneditor-format'
            select_expand_btn_sitem = self.locator_finder_by_class(expand_btn)
        else:
            select_expand_btn_sitem = self.locator_finder_by_xpath(self.select_expand_btn_id, benchmark=True)
        select_expand_btn_sitem.click()
        time.sleep(3)
        self.wait_for_ajax()

    def select_editor_mode_btn(self, value):
        """selecting object tabs"""
        if value == 0:
            select_editor_btn_sitem = self.locator_finder_by_xpath("//*[text()='Tree ▾']")
        else:
            select_editor_btn_sitem = self.locator_finder_by_xpath("//*[text()='Code ▾']")
        select_editor_btn_sitem.click()
        time.sleep(3)
        self.wait_for_ajax()

    def switch_to_code_editor_mode(self):
        """switching editor mode to Code"""
        switch_to_code_editor_mode_sitem = self.locator_finder_by_xpath(self.switch_to_code_editor_mode_id, benchmark=True)
        switch_to_code_editor_mode_sitem.click()
        time.sleep(3)
        self.wait_for_ajax()

    def compact_json_data(self):
        """switching editor mode to Code compact view"""
        compact_json_data_sitem = self.locator_finder_by_class(self.compact_json_data_id)
        compact_json_data_sitem.click()
        time.sleep(3)
        self.wait_for_ajax()

    def switch_to_tree_editor_mode(self):
        """switching editor mode to Tree"""
        switch_to_tree_editor_mode_sitem = self.locator_finder_by_xpath(self.switch_to_tree_editor_mode_id)
        switch_to_tree_editor_mode_sitem.click()
        time.sleep(3)
        self.wait_for_ajax()

    def click_arangosearch_documentation_link(self):
        """Clicking on arangosearch documentation link"""
        click_arangosearch_documentation_link_id = \
            self.locator_finder_by_link_text('ArangoSearch Views documentation')
        title = self.switch_tab(click_arangosearch_documentation_link_id)
        # expected_title = '<code>arangosearch</code> Views Reference | ArangoSearch | Indexing | Manual | ArangoDB Documentation'
        expected_title = 'arangosearch Views Reference | ArangoDB Documentation'
        assert title in expected_title, f"Expected page title {expected_title} but got {title}"

    def select_inside_search(self, keyword):
        """Selecting search option inside views"""
        select_inside_search_sitem = self.locator_finder_by_xpath(self.select_inside_search_id, benchmark=True)
        select_inside_search_sitem.click()
        select_inside_search_sitem.clear()
        select_inside_search_sitem.send_keys(keyword)

    def search_result_traverse_down(self):
        """traverse search results down"""
        search_result_traverse_down_sitem = self.locator_finder_by_class(self.search_result_traverse_down_id)
        for _ in range(8):
            search_result_traverse_down_sitem.click()
            time.sleep(1)

    def search_result_traverse_up(self):
        """traverse search results up"""
        search_result_traverse_up_sitem = self.locator_finder_by_class(self.search_result_traverse_up_id)
        for _ in range(8):
            search_result_traverse_up_sitem.click()
            time.sleep(1)

    def clicking_rename_views_btn(self):
        """Select Views rename btn"""
        clicking_rename_btn_sitem = self.locator_finder_by_id(self.clicking_rename_views_btn_id)
        clicking_rename_btn_sitem.click()

    def rename_views_name(self, name):
        """changing view name"""
        rename_views_name_sitem = self.locator_finder_by_xpath(self.rename_views_name_id)
        rename_views_name_sitem.click()
        rename_views_name_sitem.clear()
        rename_views_name_sitem.send_keys(name)

    def rename_views_name_confirm(self):
        """Confirm rename views"""
        rename_views_name_confirm_sitem = self.locator_finder_by_xpath(self.rename_views_name_confirm_id)
        rename_views_name_confirm_sitem.click()
        time.sleep(2)
        self.wait_for_ajax()
        self.webdriver.back()

    def create_improved_views(self, view_name, types):
        # pylint: disable=too-many-locals
        """
        creating improved views tab
        This method will create the improved views for v3.9+
        """
        self.wait_for_ajax()
        self.tprint("Selecting views create button \n")
        create_new_views_id = self.locator_finder_by_id(self.create_new_view)
        create_new_views_id.click()
        time.sleep(2)

        self.wait_for_ajax()
        self.tprint(f"Select name for the {view_name} \n")
        name_id = 'newName'
        name_id_sitem = self.locator_finder_by_id(name_id)
        name_id_sitem.click()
        name_id_sitem.clear()
        name_id_sitem.send_keys(view_name)
        time.sleep(2)

        self.wait_for_ajax()
        self.tprint(f"Selecting primary compression for {view_name} \n")
        primary_compression = "newPrimarySortCompression"
        self.locator_finder_by_select(primary_compression, types)  # keep it default choice
        time.sleep(2)

        self.wait_for_ajax()
        self.tprint(f"Select primary sort for {view_name} \n")
        primary_sort = '//*[@id="accordion2"]/div/div[1]/a/span[2]/b'
        primary_sort_sitem = self.locator_finder_by_xpath(primary_sort)
        primary_sort_sitem.click()
        time.sleep(2)

        self.wait_for_ajax()
        self.tprint(f"Select primary field for {view_name} \n")
        primary_field = '//*[@id="newPrimarySort-row-0"]/td[1]/input'
        primary_field_sitem = self.locator_finder_by_xpath(primary_field)
        primary_field_sitem.click()
        primary_field_sitem.clear()
        primary_field_sitem.send_keys("attr")
        time.sleep(2)

        self.wait_for_ajax()
        self.tprint(f"Selecting direction for {view_name} \n")
        direction = '(//select)[2]'
        self.locator_finder_by_select_using_xpath(direction, types)  # keep it default choice

        self.wait_for_ajax()
        self.tprint(f"Select stored value for {view_name} \n")
        sorted_value = '//*[@id="accordion3"]/div/div[1]/a/span[2]/b'
        sorted_value_sitem = self.locator_finder_by_xpath(sorted_value)
        sorted_value_sitem.click()
        time.sleep(2)
        self.wait_for_ajax()

        if self.current_package_version() >= semver.VersionInfo.parse("3.9.0"):
            self.tprint('stored value has been skipped.\n')
        else:
            self.tprint(f'Select stored field for {view_name} \n')
            stored_field = "(//a[@class='accordion-toggle collapsed'])[2]"
            stored_field_sitem = self.locator_finder_by_xpath(stored_field)
            stored_field_sitem.click()
            stored_field_sitem.clear()
            stored_field_sitem.send_keys('attr')
            stored_field_sitem.send_keys(Keys.ENTER)
            time.sleep(2)
            self.wait_for_ajax()

        self.wait_for_ajax()
        self.tprint(f"Selecting stored direction for {view_name} \n")
        stored_direction = "(//select)[3]"
        self.locator_finder_by_select_using_xpath(stored_direction, types)  # keep it default choice
        time.sleep(2)

        self.wait_for_ajax()
        self.tprint(f"Select advance options for {view_name} \n")
        advance_option = "//span[contains(text(), 'Advanced')]"
        advance_option_sitem = self.locator_finder_by_xpath(advance_option)
        advance_option_sitem.click()
        time.sleep(2)

        self.wait_for_ajax()
        self.tprint(f"Select write buffer value for {view_name} \n")
        write_buffer = "newWriteBufferIdle"
        write_buffer_sitem = self.locator_finder_by_id(write_buffer)
        write_buffer_sitem.click()
        write_buffer_sitem.clear()
        write_buffer_sitem.send_keys("50")
        time.sleep(2)

        self.wait_for_ajax()
        self.tprint(f'Select write buffer active value for {view_name} \n')
        write_buffer_active = 'newWriteBufferActive'
        write_buffer_active_sitem = self.locator_finder_by_id(write_buffer_active)
        write_buffer_active_sitem.click()
        write_buffer_active_sitem.clear()
        write_buffer_active_sitem.send_keys('8')
        time.sleep(2)

        self.wait_for_ajax()
        self.tprint(f'Select max write buffer size max value for {view_name} \n')
        max_buffer_size = "//input[@value='33554432']"
        max_buffer_size_sitem = self.locator_finder_by_xpath(max_buffer_size)
        max_buffer_size_sitem.click()

        a = ActionChains(self.webdriver)
        a.key_down(Keys.CONTROL).send_keys('A').key_up(Keys.CONTROL).send_keys(Keys.DELETE)\
            .send_keys('33554434').perform()
        time.sleep(2)

        self.wait_for_ajax()
        self.tprint(f"Selecting creation button for {view_name} \n")
        create = 'modalButton1'
        create_sitem = self.locator_finder_by_id(create)
        create_sitem.click()
        time.sleep(2)
        self.webdriver.refresh()
        self.wait_for_ajax()

    def checking_improved_views(self, name, locator, is_cluster):
        """This method will check improved views"""
        self.wait_for_ajax()
        self.tprint(f"Checking {name} started \n")

        self.tprint(f"Selecting {name}'s settings button\n")
        self.select_views_settings()

        self.tprint("Sorting views to descending\n")
        self.select_sorting_views()
        self.tprint("Sorting views to ascending\n")
        self.select_sorting_views()

        self.tprint("Views search option testing\n")
        self.search_views("improved_arangosearch_view_01", self.select_improved_arangosearch_view_01)
        self.search_views("improved_arangosearch_view_02", self.select_improved_arangosearch_view_02)

        self.tprint(f"Selecting {name} for checking \n")
        select_view_sitem = self.locator_finder_by_xpath(locator, benchmark=True)
        select_view_sitem.click()

        self.select_collapse_btn()
        self.tprint("Selecting expand button \n")
        self.select_expand_btn()
        self.tprint("Selecting editor mode \n")
        self.select_editor_mode_btn(0)
        self.tprint("Switch editor mode to Code \n")
        self.switch_to_code_editor_mode()
        self.tprint("Switch editor mode to Compact mode Code \n")
        self.compact_json_data()

        self.tprint("Selecting editor mode \n")
        self.select_editor_mode_btn(1)
        self.tprint("Switch editor mode to Tree \n")
        self.switch_to_tree_editor_mode()

        self.tprint("Clicking on ArangoSearch documentation link \n")
        self.click_arangosearch_documentation_link()
        self.tprint("Selecting search option\n")
        self.select_inside_search("i")
        self.tprint("Traversing all results up and down \n")
        self.search_result_traverse_down()
        self.search_result_traverse_up()

        if is_cluster:
            self.tprint("Renaming views are disabled for the Cluster deployment")
        else:
            self.tprint(f"Rename {name} to modified_name started \n")
            self.clicking_rename_views_btn()
            self.rename_views_name("modified_views_name")
            self.rename_views_name_confirm()
            self.tprint("Rename the current Views completed \n")
        self.tprint(f"Checking {name} Completed \n")

    def create_collection(self, collection_name):
        """Creating collection for testing"""
        self.wait_for_ajax()
        collection = 'collections'  # TODO add navbar navigation here
        collection_sitem = self.locator_finder_by_id(collection)
        collection_sitem.click()
        time.sleep(1)
        create_col = 'createCollection'
        create_col_sitem = self.locator_finder_by_id(create_col)
        create_col_sitem.click()
        time.sleep(1)

        col_name = '//*[@id="new-collection-name"]'
        col_name_sitem = self.locator_finder_by_xpath(col_name)
        col_name_sitem.click()
        col_name_sitem.send_keys(collection_name)
        time.sleep(1)

        save_btn = 'modalButton1'
        save_btn_sitem = self.locator_finder_by_id(save_btn)
        save_btn_sitem.click()
        time.sleep(2)

    def adding_collection_to_the_link(self, collection_name):
        """This method will add collection to the views link"""
        self.wait_for_ajax()
        self.tprint('Selecting Link tab \n')
        links = "//div[@id='subNavigationBar']/ul[2]//a[.='Links']"
        links_sitem = self.locator_finder_by_xpath(links, benchmark=True)
        links_sitem.click()
        time.sleep(1)

        self.tprint('Entering collection name to the link \n')
        select_col = "(//input[@placeholder='Enter a collection name'])[1]"
        select_col_sitem = self.locator_finder_by_xpath(select_col)
        select_col_sitem.click()
        select_col_sitem.send_keys(collection_name)
        time.sleep(1)

        self.tprint('Adding collection to the link \n')
        add_col = "(//li[@class='active'])[1]"
        add_col_stiem = self.locator_finder_by_xpath(add_col)
        add_col_stiem.click()
        time.sleep(1)

        self.tprint('Saving the updated views links\n')
        save_link = '//*[@id="modal-dialog"]/div/div/div[2]/button'
        save_link_sitem = self.locator_finder_by_xpath(save_link)
        save_link_sitem.click()
        time.sleep(2)

    def modify_connected_collection_of_link(self, collection_name):
        """This method will modify the connected collection"""
        self.wait_for_ajax()
        self.tprint('Select my_collection \n')
        select_my_col = f"//*[text()='{collection_name}']"
        select_my_col_sitem = self.locator_finder_by_xpath(select_my_col, benchmark=True)
        select_my_col_sitem.click()
        time.sleep(1)

        self.tprint('add text_de analyzer to the link \n')
        analyzer = "(//input[@placeholder='Start typing for suggestions.'])[1]"
        analyzer_sitem = self.locator_finder_by_xpath(analyzer)
        analyzer_sitem.click()
        analyzer_sitem.send_keys('text_d')
        time.sleep(1)

        self.tprint("Selecting my_delimiter analyzer\n")
        delimiter = "(//li[@class='active'])[1]"
        delimiter_sitem = self.locator_finder_by_xpath(delimiter)
        delimiter_sitem.click()
        time.sleep(1)

        self.tprint('Selecting include all fields\n')
        include = "//*[text()='Include All Fields']"
        include_sitem = self.locator_finder_by_xpath(include)
        include_sitem.click()
        time.sleep(1)

        self.tprint('Selecting Track List fields\n')
        track_list = "// *[text() = 'Track List Positions']"
        track_list_sitem = self.locator_finder_by_xpath(track_list)
        track_list_sitem.click()
        time.sleep(1)

        self.tprint('Selecting stored id fields\n')
        stored_id_list = "// *[text() = 'Store ID Values']"
        stored_id_list_sitem = self.locator_finder_by_xpath(stored_id_list)
        stored_id_list_sitem.click()
        time.sleep(1)

        self.tprint('Selecting background fields\n')
        background = "// *[text() = 'In Background']"
        background_sitem = self.locator_finder_by_xpath(background)
        background_sitem.click()
        time.sleep(1)

        self.tprint('Saving updated links\n')
        save = "//*[text()='Save View']"
        save_sitem = self.locator_finder_by_xpath(save)
        save_sitem.click()
        time.sleep(2)

    def creating_black_collection_and_analyzer(self):
        """Creating blank col and analyzer for testing"""
        self.wait_for_ajax()
        self.tprint('creating blank collection and analyzer for link tab\n')
        self.navbar_goto("collections")
        time.sleep(1)
        create_col = 'createCollection'
        create_col_sitem = self.locator_finder_by_id(create_col)
        create_col_sitem.click()
        time.sleep(1)

        col_name = '//*[@id="new-collection-name"]'
        col_name_sitem = self.locator_finder_by_xpath(col_name, benchmark=True)
        col_name_sitem.click()
        col_name_sitem.send_keys('views_collection')
        time.sleep(1)

        save_btn = 'modalButton1'
        save_btn_sitem = self.locator_finder_by_id(save_btn)
        save_btn_sitem.click()
        time.sleep(2)

        # go back to view tab
        self.navbar_goto("views")
        time.sleep(1)

    def check_views_changes_saved(self, name, ex_msg=None):
        """checking the creation of the view using the green notification bar appears at the bottom"""
        self.wait_for_ajax()
        time.sleep(1)
        try:
            self.tprint(f'Checking successful creation of the {name} \n')
            success_message = 'noty_body'
            success_message_sitem = self.locator_finder_by_class(success_message).text
            self.tprint(f'Notification: {success_message_sitem}\n')
            if ex_msg is None:
                expected_msg = f"Success: Updated View: {name}"
            else:
                expected_msg = ex_msg
            assert expected_msg == success_message_sitem, f"Expected {expected_msg} but got {success_message_sitem}"
        except TimeoutException:
            self.tprint('Error occurred!! required manual inspection.\n')
        self.tprint(f'Creating {name} completed successfully \n')

    def open_tier_tab(self):
        """This method will open tier tab inside consolidation tab of views"""
        tier = "//tr[@id='row_change-view-policyType']//select"
        tier_sitem = self.locator_finder_by_xpath(tier)
        tier_sitem.click()
        time.sleep(1)

    def open_general_tab(self):
        """this method will open the general tab of views"""
        self.tprint("Selecting views general tab \n")
        general = "(//button[@id='accordion-button-2'])[1]"
        general_sitem = self.locator_finder_by_xpath(general, benchmark=True)
        general_sitem.click()
        time.sleep(1)

    def open_consolidation_policy_tab(self):
        """this method will open the consolidation_policy tab of views"""
        self.tprint("Selecting views consolidation_policy tab \n")
        consolidation = "(//span[@class='css-1eziwv'])[3]"
        consolidation_sitem = self.locator_finder_by_xpath(consolidation)
        consolidation_sitem.click()
        time.sleep(1)
    def open_primary_sort_tab(self):
        """this method will open the primary_sort tab of views"""
        self.tprint("Selecting views primary_sort tab \n")
        sort = "(//span[@class='css-1eziwv'])[4]"
        sort_sitem = self.locator_finder_by_xpath(sort)
        sort_sitem.click()
        time.sleep(1)

    def open_stored_value_tab(self):
        """this method will open the stored_value tab of views"""
        self.tprint("Selecting views stored_value tab \n")
        sort = "(//span[@class='css-1eziwv'])[5]"
        sort_sitem = self.locator_finder_by_xpath(sort)
        sort_sitem.click()
        time.sleep(1)

    def select_desired_primary_sort(self, sort):
        """this method will find the desired views from the list using given locator"""
        select_view = "(//*[name()='svg'][@class='css-8mmkcg'])[2]"
        select_index_sitem = self.locator_finder_by_xpath(select_view)
        select_index_sitem.click()
        time.sleep(1)

        element = self.locator_finder_by_xpath(f"//*[contains(text(), '{sort}')]")
        actions = ActionChains(self.webdriver)
        # Move the mouse pointer to the element containing the text
        actions.move_to_element(element)
        # Perform a click action
        actions.click().perform()

    def select_desired_views_from_the_list(self, view_type_name):
        """this method will find the desired views from the list using given locator"""
        select_view = "(//*[name()='svg'][@class='css-8mmkcg'])[1]"
        select_index_sitem = self.locator_finder_by_xpath(select_view)
        select_index_sitem.click()
        time.sleep(1)

        element = self.locator_finder_by_xpath(
            f"//*[contains(text(), '{view_type_name}')]"
        )
        actions = ActionChains(self.webdriver)
        # Move the mouse pointer to the element containing the text
        actions.move_to_element(element)
        # Perform a click action
        actions.click().perform()

    def create_improved_views_311(self, view_name, types, variation):
        """This method will create the improved views for v3.11+"""
        self.wait_for_ajax()
        self.tprint("Selecting views create button \n")
        if self.current_package_version() <= semver.VersionInfo.parse("3.11.100"):
            create_new_views = "//*[contains(text(),'Add View')]"
        else:
            create_new_views = "(//button[normalize-space()='Add view'])[1]"

        create_new_views_id = self.locator_finder_by_xpath(create_new_views, benchmark=True)
        create_new_views_id.click()
        time.sleep(2)

        self.wait_for_ajax()
        self.tprint(f"Select name for the {view_name} \n")
        name_id_sitem = self.locator_finder_by_id("name")
        name_id_sitem.click()
        name_id_sitem.clear()
        name_id_sitem.send_keys(view_name)
        time.sleep(2)

        self.tprint("Select view's type")
        if types == "search-alias":
            self.select_desired_views_from_the_list("search-alias")

        self.wait_for_ajax()
        # this will change the type of the views
        if types == "arangosearch" and variation == 1:
            self.select_desired_primary_sort("None")

        self.wait_for_ajax()
        if types == "arangosearch":
            self.tprint(f"Select primary sort for {view_name} \n")
            primary_sort = "//*[text()='Primary Sort']"
            primary_sort_sitem = self.locator_finder_by_xpath(primary_sort)
            primary_sort_sitem.click()
            time.sleep(2)

            self.wait_for_ajax()
            self.tprint(f"Select primary field for {view_name} \n")
            primary_field = "//*[text()='Field']"
            primary_field_sitem = self.locator_finder_by_xpath(primary_field)
            primary_field_sitem.click()
            self.send_key_action("attr")
            time.sleep(2)

            # self.tprint(f"Selecting direction for {view_name} \n")
            # direction = "//*[text()='Ascending']"
            # direction_sitem = self.locator_finder_by_xpath(direction)
            # direction_sitem.click()

            self.wait_for_ajax()
            self.tprint(f"Closing primary sort for {view_name}\n")
            primary_sort = "//*[text()='Primary Sort']"
            primary_sort_sitem = self.locator_finder_by_xpath(primary_sort)
            primary_sort_sitem.click()
            time.sleep(1)

            self.wait_for_ajax()
            self.tprint(f"Select stored value for {view_name} \n")
            sorted_value = "//*[text()='Stored Values']"
            sorted_value_sitem = self.locator_finder_by_xpath(sorted_value)
            sorted_value_sitem.click()
            time.sleep(1)

            field = "//*[text()='Fields']"
            field_sitem = self.locator_finder_by_xpath(field)
            field_sitem.click()

            self.wait_for_ajax()
            self.tprint(f"Closing stored value for {view_name} \n")
            sorted_value = "//*[text()='Stored Values']"
            sorted_value_sitem = self.locator_finder_by_xpath(sorted_value)
            sorted_value_sitem.click()
            time.sleep(1)

            self.wait_for_ajax()
            self.tprint(f"Select advance options for {view_name} \n")
            advance_option = "//*[text()='Advanced']"
            advance_option_sitem = self.locator_finder_by_xpath(advance_option)
            advance_option_sitem.click()
            time.sleep(1)

            # self.tprint(f"Select write buffer idle value for {view_name} \n")
            # write_buffer = "//*[text()='Write Buffer Idle']"
            # write_buffer_sitem = self.locator_finder_by_id(write_buffer)
            # write_buffer_sitem.click()
            # self.send_key_action('50')

            self.wait_for_ajax()
            self.tprint(f"Close advance options for {view_name} \n")
            advance_option = "//*[text()='Advanced']"
            advance_option_sitem = self.locator_finder_by_xpath(advance_option)
            advance_option_sitem.click()
            time.sleep(1)

            # self.tprint(f"Select write buffer active value for {view_name} \n")
            # write_buffer_active = "newWriteBufferActive"
            # write_buffer_active_sitem = self.locator_finder_by_id(write_buffer_active)
            # write_buffer_active_sitem.click()
            # write_buffer_active_sitem.clear()
            # write_buffer_active_sitem.send_keys("8")
            # time.sleep(2)
            #
            # self.tprint(f"Select max write buffer size max value for {view_name} \n")
            # max_buffer_size = "//input[@value='33554432']"
            # max_buffer_size_sitem = self.locator_finder_by_xpath(max_buffer_size)
            # max_buffer_size_sitem.click()
            #
            # a = ActionChains(self.webdriver)
            # a.key_down(Keys.CONTROL).send_keys("A").key_up(Keys.CONTROL).send_keys(
            #     Keys.DELETE
            # ).send_keys("33554434").perform()
            # time.sleep(2)
            #
        self.wait_for_ajax()
        self.tprint(f"Selecting creation button for {view_name} \n")
        if self.current_package_version() >= semver.VersionInfo.parse("3.11.100"):
            create = "(//button[normalize-space()='Create'])[1]"
        else:
            create = '//*[@id="chakra-modal-3"]/form/footer/div/button[2]'

        create_sitem = self.locator_finder_by_xpath(create)
        create_sitem.click()
        time.sleep(3)
        self.webdriver.refresh()

    def checking_improved_views_for_v310(self, name, locator, is_cluster):
        """This method will check improved views for v3.10.x"""
        self.wait_for_ajax()
        self.tprint(f'Checking {name} started \n')
        self.tprint(f"Selecting {name}'s settings button\n")
        self.select_views_settings()
        self.tprint("Sorting views to descending\n")
        self.select_sorting_views()
        self.tprint("Sorting views to ascending\n")
        self.select_sorting_views()
        self.select_views_settings()

        self.tprint("Views search option testing\n")
        self.search_views("improved_arangosearch_view_01", self.select_improved_arangosearch_view_01)
        self.search_views("improved_arangosearch_view_02", self.select_improved_arangosearch_view_02)

        self.tprint(f'Selecting {name} for checking \n')
        select_view_sitem = self.locator_finder_by_xpath(locator)
        select_view_sitem.click()
        time.sleep(1)

        self.tprint("Changing cleanup interval step \n")
        cleanup = "//tr[@id='row_change-view-cleanupIntervalStep']//input[@value='2']"
        cleanup_sitem = self.locator_finder_by_xpath(cleanup)
        cleanup_sitem.click()
        cleanup_sitem.clear()
        cleanup_sitem.send_keys("3")
        time.sleep(1)

        self.tprint("Changing commit interval \n")
        commit = "//tr[@id='row_change-view-commitIntervalMsec']//input[@value='1000']"
        commit_sitem = self.locator_finder_by_xpath(commit)
        commit_sitem.click()
        commit_sitem.clear()
        commit_sitem.send_keys("3000")
        time.sleep(1)

        self.tprint("Changing consolidation interval \n")
        consolidation = "//tr[@id='row_change-view-consolidationIntervalMsec']//input[@value='1000']"
        consolidation_sitem = self.locator_finder_by_xpath(consolidation)
        consolidation_sitem.click()
        consolidation_sitem.clear()
        consolidation_sitem.send_keys("2000")
        time.sleep(1)

        self.open_tier_tab()
        self.open_tier_tab()

        self.tprint("Selecting segment min \n")
        segment_min =  "//tr[@id='row_change-view-segmentsMin']//input[@value='1']"
        segment_min_sitem = self.locator_finder_by_xpath(segment_min)
        segment_min_sitem.click()
        segment_min_sitem.clear()
        segment_min_sitem.send_keys("3")
        time.sleep(2)

        self.tprint("Selecting segment max \n")
        segment_max = "//tr[@id='row_change-view-segmentsMax']//input[@value='10']"
        segment_max_sitem = self.locator_finder_by_xpath(segment_max)
        segment_max_sitem.click()
        segment_max_sitem.clear()
        segment_max_sitem.send_keys("12")
        time.sleep(2)

        self.tprint("Selecting segments byte max \n")
        segment_byte_max =  "//tr[@id='row_change-view-segmentsBytesMax']//input[@value='5368709120']"
        segment_byte_max_sitem = self.locator_finder_by_xpath(segment_byte_max)
        segment_byte_max_sitem.click()
        segment_byte_max_sitem.clear()
        segment_byte_max_sitem.send_keys("5368709128")
        time.sleep(2)

        self.tprint("Selecting segments bytes floor \n")
        segment_byte_floor = "//tr[@id='row_change-view-segmentsBytesFloor']//input[@value='2097152']"
        segment_byte_floor_sitem = self.locator_finder_by_xpath(segment_byte_floor)
        segment_byte_floor_sitem.click()
        segment_byte_floor_sitem.clear()
        segment_byte_floor_sitem.send_keys("2097158")
        time.sleep(2)

        self.tprint("Saving the changes \n")
        save_btn = "(//button[@class='button-success'])[1]"
        save_btn_sitem = self.locator_finder_by_xpath(save_btn)
        save_btn_sitem.click()
        time.sleep(1)

        self.check_views_changes_saved(name)

        # creating example collection & analyzer for the view
        self.creating_black_collection_and_analyzer()

        self.tprint(f'Selecting {name} again\n')
        select_view_sitem = self.locator_finder_by_xpath(locator)
        select_view_sitem.click()
        time.sleep(1)

        self.tprint('Selecting Link tab \n')
        links = '//*[@id="subNavigationBar"]/ul[2]/li[2]/a'
        links_sitem = self.locator_finder_by_xpath(links)
        links_sitem.click()
        time.sleep(1)

        self.tprint('Select views_collection \n')
        select_col = "(//input[@placeholder='Enter a collection name'])[1]"
        select_col_sitem = self.locator_finder_by_xpath(select_col)
        select_col_sitem.click()
        select_col_sitem.send_keys('views_collectio')
        select_col_sitem.send_keys(Keys.ENTER)
        time.sleep(1)

        select_views = "(//a[normalize-space()='views_collection'])[1]"
        select_views_sitem = self.locator_finder_by_xpath(select_views)
        select_views_sitem.click()
        time.sleep(1)

        self.tprint('Selecting include all fields\n')
        include = "//*[text()='Include All Fields']"
        include_sitem = self.locator_finder_by_xpath(include)
        include_sitem.click()
        time.sleep(1)

        self.tprint('Selecting Track List fields\n')
        track_list = "// *[text() = 'Track List Positions']"
        track_list_sitem = self.locator_finder_by_xpath(track_list)
        track_list_sitem.click()
        time.sleep(1)

        self.tprint('Selecting stored id fields\n')
        stored_id_list = "// *[text() = 'Store ID Values']"
        stored_id_list_sitem = self.locator_finder_by_xpath(stored_id_list)
        stored_id_list_sitem.click()
        time.sleep(1)

        self.tprint('Selecting background fields\n')
        background = "// *[text() = 'In Background']"
        background_sitem = self.locator_finder_by_xpath(background)
        background_sitem.click()
        time.sleep(1)

        self.tprint('Selecting analyzer for the views collection\n')
        analyzer =  "(//input[@placeholder='Start typing for suggestions.'])[1]"
        analyzer_sitem = self.locator_finder_by_xpath(analyzer)
        analyzer_sitem.click()
        analyzer_sitem.send_keys("text_d")
        analyzer_sitem.send_keys(Keys.ENTER)
        time.sleep(1)

        self.tprint("Saving the changes \n")
        save_btn = '//*[@id="Save"]/button'
        save_btn_sitem = self.locator_finder_by_xpath(save_btn)
        save_btn_sitem.click()
        time.sleep(1)

        self.check_views_changes_saved(name)

        # renaming views
        if is_cluster:
            self.tprint('Renaming views are disabled for the Cluster deployment')
        else:
            self.tprint(f"Rename {name} to modified_name started \n")
            self.tprint(f'Selecting {name} for renaming \n')

            self.navbar_goto("views")

            self.tprint(f'Selecting {name} for renaming \n')
            select_view_sitem = self.locator_finder_by_xpath(locator)
            select_view_sitem.click()   # already in the settings tab
            time.sleep(1)

            modified_name = "(//input[@value='improved_arangosearch_view_01'])[1]"
            modified_name_sitem = self.locator_finder_by_xpath(modified_name)
            modified_name_sitem.click()
            modified_name_sitem.clear()
            modified_name_sitem.send_keys('modified_views_name')

            self.tprint("Saving the changes for the views name \n")
            save = "//*[text()='Save View']"
            save_sitem = self.locator_finder_by_xpath(save)
            save_sitem.click()

            self.check_views_changes_saved(name, "Success: Updated View: modified_views_name")
            self.tprint("Rename the current Views completed \n")

        self.tprint(f'Checking {name} Completed \n')

    def checking_views_negative_scenario_for_views(self):
        """This method will check negative input for views name during creation"""
        self.navbar_goto("views")
        self.tprint('Selecting views create button \n')
        create_new_views_id = self.locator_finder_by_id(self.create_new_view, benchmark=True)
        create_new_views_id.click()
        time.sleep(2)
        self.wait_for_ajax()

        self.tprint('Expected error scenario for the Views name started \n')
        error_input = ['@', '/', 'שלום']
        print_statement = ['Checking views name with "@"',
                           'Checking views name with "/"',
                           'Checking views name with "שלום"']
        error = 'Only symbols, "_" and "-" are allowed.'
        error_message = [error, error, error]

        locator_id = '//*[@id="newName"]'
        error_locator_id = "//p[@class='errorMessage']"

        # method template (self, error_input, print_statement, error_message, locators_id, error_message_id)
        self.check_expected_error_messages_for_views(error_input,
                                                     print_statement,
                                                     error_message,
                                                     locator_id,
                                                     error_locator_id)
        self.tprint('Expected error scenario for the Views name completed \n')

        self.tprint('Expected error scenario for the Views write buffer idle started \n')
        error_input = ['@', '/', 'שלום', '9999999999999999']
        print_statement = ['Checking views name with "@"',
                           'Checking views name with "/"',
                           'Checking views name with "שלום"',
                           'Checking views name with "9999999999999999"']
        error = 'Only non-negative integers allowed.'
        error_message = [error, error, error, error]

        if self.current_package_version() >= semver.VersionInfo.parse("3.9.0"):
            self.tprint('Select advance options \n')
            advance_option = '//*[@id="accordion4"]/div/div[1]/a/span[2]/b'
            advance_option_sitem = self.locator_finder_by_xpath(advance_option)
            advance_option_sitem.click()
            time.sleep(2)
            self.wait_for_ajax()

            self.tprint('Select write buffer idle value\n')
            buffer_locator_id = "//input[@value='64']"
            error_locator_id = '//*[@id="row_newWriteBufferIdle"]/th[2]/p'

            # method template (self, error_input, print_statement, error_message, locators_id, error_message_id)
            self.check_expected_error_messages_for_views(error_input,
                                                         print_statement,
                                                         error_message,
                                                         buffer_locator_id,
                                                         error_locator_id)
            self.tprint('Expected error scenario for the Views write buffer idle completed \n')

        self.tprint('Closing the views creation \n')
        close_btn = '//*[@id="modalButton0"]'
        close_btn_sitem = self.locator_finder_by_xpath(close_btn)
        close_btn_sitem.click()
        time.sleep(3)
        self.wait_for_ajax()


    def delete_views(self, name, locator):
        """This method will delete views"""
        try:
            self.navbar_goto("views")
            self.wait_for_ajax()
            self.tprint(f"Selecting {name} for deleting \n")
            select_view_sitem = self.locator_finder_by_xpath(locator)
            select_view_sitem.click()
            time.sleep(1)
            self.wait_for_ajax()

            delete_views_btn_sitem = self.locator_finder_by_id(self.delete_views_btn_id)
            delete_views_btn_sitem.click()
            time.sleep(1)

            delete_views_confirm_btn_sitem = self.locator_finder_by_xpath(self.delete_views_confirm_btn_id)
            delete_views_confirm_btn_sitem.click()
            time.sleep(1)

            final_delete_confirmation_sitem = self.locator_finder_by_id(self.final_delete_confirmation_id)
            final_delete_confirmation_sitem.click()
            self.tprint(f"Selecting {name} for deleting completed \n")
            time.sleep(1)
            self.wait_for_ajax()
        except TimeoutException as e:
            self.tprint('TimeoutException occurred! \n')
            self.tprint(f'Info: Views has already been deleted or never created. \n{e}')
        except Exception as ex:
            traceback.print_exc()
            raise Exception('Critical Error occurred and need manual inspection!! \n') from ex

    def delete_created_collection(self, col_name):
        """this method will delete all the collection created for views"""
        self.wait_for_ajax()
        try:
            self.tprint('Selecting collection tab\n')
            self.navbar_goto("collections")
            time.sleep(1)

            self.tprint('Deleting collection started\n')
            my_collection = f"//*[text()='{col_name}']"
            my_collection_sitem = self.locator_finder_by_xpath(my_collection)
            my_collection_sitem.click()
            time.sleep(1)

            setting = "//*[text()='Settings']"
            setting_sitem = self.locator_finder_by_xpath(setting)
            setting_sitem.click()
            time.sleep(2)

            delete = "//*[text()='Delete']"
            delete_sitem = self.locator_finder_by_xpath(delete)
            delete_sitem.click()
            time.sleep(1)

            self.wait_for_ajax()
            confirm = "/html/body/div[2]/div/div[2]/div[2]/div/div[3]/button[1]"
            confirm_sitem = self.locator_finder_by_xpath(confirm)
            confirm_sitem.click()
            time.sleep(1)
        except TimeoutException:
            self.tprint('TimeoutException occurred! \n')
            self.tprint(f'Info: {col_name} has already been deleted or never created. \n')
        except Exception as ex:
            traceback.print_exc()
            raise Exception('Critical Error occurred and need manual inspection!! \n') from ex

    def delete_views_310(self, name):
        """this method will delete all the newer version views"""
        self.wait_for_ajax()
        self.navbar_goto("views")
        try:
            views = ''
            if name == 'modified_views_name':
                views = "//*[text()='modified_views_name']"
            elif name == 'improved_arangosearch_view_01':
                views = "//*[text()='improved_arangosearch_view_01']"
            elif name == 'improved_arangosearch_view_02':
                views = "//*[text()='improved_arangosearch_view_02']"

            views_sitem = self.locator_finder_by_xpath(views)
            views_sitem.click()
            time.sleep(2)
            self.wait_for_ajax()

            self.wait_for_ajax()
            delete = '//*[@id="Actions"]/button'
            delete_sitem = self.locator_finder_by_xpath(delete)
            delete_sitem.click()
            time.sleep(2)

            self.wait_for_ajax()
            confirm_delete_btn = ''
            if name == 'modified_views_name':
                confirm_delete_btn = '//*[@id="modal-content-delete-modified_views_name"]/div[3]/button[2]'
            elif name == 'improved_arangosearch_view_01':
                confirm_delete_btn = '//*[@id="modal-content-delete-improved_arangosearch_view_01"]/div[3]/button[2]'
            elif name == 'improved_arangosearch_view_02':
                confirm_delete_btn = '//*[@id="modal-content-delete-improved_arangosearch_view_02"]/div[3]/button[2]'

            confirm_delete_btn_sitem = self.locator_finder_by_xpath(confirm_delete_btn)
            confirm_delete_btn_sitem.click()
            time.sleep(2)

            self.webdriver.refresh()
            time.sleep(2)
            self.wait_for_ajax()

        except (TimeoutException, AttributeError) as ex:
            self.tprint('TimeoutException occurred! \n')
            self.tprint(f'Info: {name} has already been deleted or never created. \n{ex}')
        except NoSuchElementException:
            self.tprint('Element not found, which might be happen due to force cleanup.')
        except Exception as ex:
            traceback.print_exc()
            raise Exception('Critical Error occurred and need manual inspection!! \n') from ex

    def delete_views_312(self, name):
        """this method will delete all the newer version views > 3.11"""
        self.wait_for_ajax()
        self.navbar_goto("views")
        self.tprint(f"{name} start deleting \n")
        try:
            views = ""
            if name == "arangosearch_view_3111":
                views = "//*[text()='arangosearch_view_3111']"
            elif name == "arangosearch_view_3112":
                views = "//*[text()='arangosearch_view_3112']"
            elif name == "search_alias":
                views = "//*[text()='search_alias']"

            views_sitem = self.locator_finder_by_xpath(views)
            views_sitem.click()
            time.sleep(2)

            delete = "(//button[normalize-space()='Delete'])[1]"
            delete_sitem = self.locator_finder_by_xpath(delete)
            delete_sitem.click()
            time.sleep(2)

            self.wait_for_ajax()
            if self.current_package_version() > semver.VersionInfo.parse("3.11.100"):
                confirm_delete_btn = "//*[text()='Cancel']/following-sibling::button"
            else:
                confirm_delete_btn = "(//button[@class='button-danger'])[1]"

            confirm_delete_btn_sitem = self.locator_finder_by_xpath(confirm_delete_btn)
            confirm_delete_btn_sitem.click()
            time.sleep(2)

            self.webdriver.refresh()

        except TimeoutException:
            self.tprint("TimeoutException occurred! \n")
            self.tprint(f"Info: {name} has already been deleted or never created. \n")
        except Exception as ex:
            traceback.print_exc()
            raise Exception("Critical Error occurred and need manual inspection!! \n") from ex
