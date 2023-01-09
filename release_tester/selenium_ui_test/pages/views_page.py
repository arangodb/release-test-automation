#!/usr/bin/python3
"""page object for views editing"""
import time
import semver
import traceback

from selenium_ui_test.pages.navbar import NavigationBarPage
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException, TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

# can't circumvent long lines.. nAttr nLines
# pylint: disable=line-too-long disable=too-many-instance-attributes disable=too-many-statements disable=too-many-public-methods


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

    def __init__(self, driver, cfg):
        """View page initialization"""
        super().__init__(driver, cfg)
        self.current_version = self.current_package_version()
        self.testing_version = semver.VersionInfo.parse("3.9.100")
        self.select_views_tab_id = "/html//a[@id='views']"
        self.create_new_views_id = "/html//a[@id='createView']"
        self.naming_new_view_id = "/html//input[@id='newName']"
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
        select_views_tab_sitem = self.locator_finder_by_xpath(self.select_views_tab_id)
        select_views_tab_sitem.click()

    def create_new_views(self, name):
        """creating new views tab"""
        print(f"Creating {name} started \n")
        create_new_views_sitem = self.locator_finder_by_xpath(self.create_new_views_id)
        create_new_views_sitem.click()

        print("Naming new views \n")
        naming_new_view_sitem = self.locator_finder_by_xpath(self.naming_new_view_id)
        naming_new_view_sitem.click()
        naming_new_view_sitem.send_keys(name)

        print("Creating new views tab \n")
        select_create_btn_sitem = self.locator_finder_by_xpath(self.select_create_btn_id)
        select_create_btn_sitem.click()
        time.sleep(2)
        self.wait_for_ajax()
        print(f"Creating {name} completed \n")

    def select_views_settings(self):
        """selecting view setting"""
        select_views_settings_sitem = self.locator_finder_by_xpath(self.select_views_settings_id)
        select_views_settings_sitem.click()
        time.sleep(3)
        self.wait_for_ajax()

    def select_sorting_views(self):
        """sorting multiple views into descending"""
        select_sorting_views_sitem = self.locator_finder_by_xpath(self.select_sorting_views_id)
        select_sorting_views_sitem.click()
        time.sleep(3)
        self.wait_for_ajax()

    def search_views(self, expected_text, search_locator):
        search_views = self.search_views_id
        for i in range(3):
            try:
                search_views_sitem = self.locator_finder_by_xpath(search_views)
                search_views_sitem.click()
                search_views_sitem.clear()
                search_views_sitem.send_keys(expected_text)
                time.sleep(2)
                self.wait_for_ajax()
                break
            except StaleElementReferenceException:
                print('stale element found, trying again\n')
            except NoSuchElementException:
                print("Can't find the view, trying again\n")
            except TimeoutException as ex:
                raise ex
            self.webdriver.refresh()

        print(f'Checking that we get the right results for {expected_text}\n')
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
        select_first_view_sitem = self.locator_finder_by_xpath(self.select_first_view_id)
        select_first_view_sitem.click()

    def select_collapse_btn(self):
        """selecting collapse btn"""
        if self.current_version > self.testing_version:
            collapse_btn = 'jsoneditor-compact'
            select_collapse_btn_sitem = self.locator_finder_by_class(collapse_btn)
        else:
            select_collapse_btn_sitem = self.locator_finder_by_xpath(self.select_collapse_btn_id)
        select_collapse_btn_sitem.click()
        time.sleep(3)
        self.wait_for_ajax()

    def select_expand_btn(self):
        """selecting expand all btn"""
        if self.current_version > self.testing_version:
            expand_btn = 'jsoneditor-format'
            select_expand_btn_sitem = self.locator_finder_by_class(expand_btn)
        else:
            select_expand_btn_sitem = self.locator_finder_by_xpath(self.select_expand_btn_id)
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
        switch_to_code_editor_mode_sitem = self.locator_finder_by_xpath(self.switch_to_code_editor_mode_id)
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
        expected_title = '<code>arangosearch</code> Views Reference | ArangoSearch | Indexing | Manual | ArangoDB Documentation'
        assert title in expected_title, f"Expected page title {expected_title} but got {title}"

    def select_inside_search(self, keyword):
        """Selecting search option inside views"""
        select_inside_search_sitem = self.locator_finder_by_xpath(self.select_inside_search_id)
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
        print("Selecting views create button \n")
        create_new_views_id = self.locator_finder_by_xpath(self.create_new_views_id)
        create_new_views_id.click()
        time.sleep(2)

        self.wait_for_ajax()
        print(f"Select name for the {view_name} \n")
        name_id = "newName"
        name_id_sitem = self.locator_finder_by_id(name_id)
        name_id_sitem.click()
        name_id_sitem.clear()
        name_id_sitem.send_keys(view_name)
        time.sleep(2)

        self.wait_for_ajax()
        print(f"Selecting primary compression for {view_name} \n")
        primary_compression = "newPrimarySortCompression"
        self.locator_finder_by_select(primary_compression, types)  # keep it default choice
        time.sleep(2)

        self.wait_for_ajax()
        print(f"Select primary sort for {view_name} \n")
        primary_sort = '//*[@id="accordion2"]/div/div[1]/a/span[2]/b'
        primary_sort_sitem = self.locator_finder_by_xpath(primary_sort)
        primary_sort_sitem.click()
        time.sleep(2)

        self.wait_for_ajax()
        print(f"Select primary field for {view_name} \n")
        primary_field = '//*[@id="newPrimarySort-row-0"]/td[1]/input'
        primary_field_sitem = self.locator_finder_by_xpath(primary_field)
        primary_field_sitem.click()
        primary_field_sitem.clear()
        primary_field_sitem.send_keys("attr")
        time.sleep(2)

        self.wait_for_ajax()
        print(f"Selecting direction for {view_name} \n")
        direction = '(//select)[2]'
        self.locator_finder_by_select_using_xpath(direction, types)  # keep it default choice

        self.wait_for_ajax()
        print(f"Select stored value for {view_name} \n")
        sorted_value = '//*[@id="accordion3"]/div/div[1]/a/span[2]/b'
        sorted_value_sitem = self.locator_finder_by_xpath(sorted_value)
        sorted_value_sitem.click()
        time.sleep(2)
        self.wait_for_ajax()

        if self.current_package_version() >= semver.VersionInfo.parse("3.9.0"):
            print('stored value has been skipped.\n')
        else:
            print(f'Select stored field for {view_name} \n')
            stored_field = "(//a[@class='accordion-toggle collapsed'])[2]"
            stored_field_sitem = self.locator_finder_by_xpath(stored_field)
            stored_field_sitem.click()
            stored_field_sitem.clear()
            stored_field_sitem.send_keys('attr')
            stored_field_sitem.send_keys(Keys.ENTER)
            time.sleep(2)
            self.wait_for_ajax()

        print(f"Selecting stored direction for {view_name} \n")
        stored_direction = "(//select)[3]"
        self.locator_finder_by_select_using_xpath(stored_direction, types)  # keep it default choice
        time.sleep(2)

        self.wait_for_ajax()
        print(f"Select advance options for {view_name} \n")
        advance_option = '//*[@id="accordion4"]/div/div[1]/a/span[2]/b'
        advance_option_sitem = self.locator_finder_by_xpath(advance_option)
        advance_option_sitem.click()
        time.sleep(2)

        self.wait_for_ajax()
        print(f"Select write buffer value for {view_name} \n")
        write_buffer = "newWriteBufferIdle"
        write_buffer_sitem = self.locator_finder_by_id(write_buffer)
        write_buffer_sitem.click()
        write_buffer_sitem.clear()
        write_buffer_sitem.send_keys("50")
        time.sleep(2)

        self.wait_for_ajax()
        print(f'Select write buffer active value for {view_name} \n')
        write_buffer_active = 'newWriteBufferActive'
        write_buffer_active_sitem = self.locator_finder_by_id(write_buffer_active)
        write_buffer_active_sitem.click()
        write_buffer_active_sitem.clear()
        write_buffer_active_sitem.send_keys('8')
        time.sleep(2)

        print(f'Select max write buffer size max value for {view_name} \n')
        max_buffer_size = "//input[@value='33554432']"
        max_buffer_size_sitem = self.locator_finder_by_xpath(max_buffer_size)
        max_buffer_size_sitem.click()

        a = ActionChains(self.webdriver)
        a.key_down(Keys.CONTROL).send_keys('A').key_up(Keys.CONTROL).send_keys(Keys.DELETE)\
            .send_keys('33554434').perform()
        time.sleep(2)

        self.wait_for_ajax()
        print(f"Selecting creation button for {view_name} \n")
        create = 'modalButton1'
        create_sitem = self.locator_finder_by_id(create)
        create_sitem.click()
        time.sleep(2)
        self.webdriver.refresh()
    
    def delete_new_views(self, name):
        """this method will delete all the newer version views"""
        self.wait_for_ajax()
        self.select_views_tab()
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

            settings_tab = "//*[text()='Settings']"
            settings_tab_sitem = self.locator_finder_by_xpath(settings_tab)
            settings_tab_sitem.click()
            time.sleep(2)
            self.wait_for_ajax()

            delete_btn = '//*[@id="modal-dialog"]/div[2]/button[1]'
            delete_btn_sitem = self.locator_finder_by_xpath(delete_btn)
            delete_btn_sitem.click()
            time.sleep(2)

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

        except TimeoutException as e:
            print('TimeoutException occurred! \n')
            print('Info: Views has already been deleted or never created. \n')
        except Exception:
            traceback.print_exc()
            raise Exception('Critical Error occurred and need manual inspection!! \n')


    def checking_improved_views(self, name, locator, is_cluster):
        """This method will check improved views"""
        print(f"Checking {name} started \n")

        print(f"Selecting {name}'s settings button\n")
        self.select_views_settings()

        print("Sorting views to descending\n")
        self.select_sorting_views()
        print("Sorting views to ascending\n")
        self.select_sorting_views()

        print("Views search option testing\n")
        self.search_views("improved_arangosearch_view_01", self.select_improved_arangosearch_view_01)
        self.search_views("improved_arangosearch_view_02", self.select_improved_arangosearch_view_02)

        print(f"Selecting {name} for checking \n")
        select_view_sitem = self.locator_finder_by_xpath(locator)
        select_view_sitem.click()

        self.select_collapse_btn()
        print("Selecting expand button \n")
        self.select_expand_btn()
        print("Selecting editor mode \n")
        self.select_editor_mode_btn(0)
        print("Switch editor mode to Code \n")
        self.switch_to_code_editor_mode()
        print("Switch editor mode to Compact mode Code \n")
        self.compact_json_data()

        print("Selecting editor mode \n")
        self.select_editor_mode_btn(1)
        print("Switch editor mode to Tree \n")
        self.switch_to_tree_editor_mode()

        print("Clicking on ArangoSearch documentation link \n")
        self.click_arangosearch_documentation_link()
        print("Selecting search option\n")
        self.select_inside_search("i")
        print("Traversing all results up and down \n")
        self.search_result_traverse_down()
        self.search_result_traverse_up()

        if is_cluster:
            print("Renaming views are disabled for the Cluster deployment")
        else:
            print(f"Rename {name} to modified_name started \n")
            self.clicking_rename_views_btn()
            self.rename_views_name("modified_views_name")
            self.rename_views_name_confirm()
            print("Rename the current Views completed \n")
        print(f"Checking {name} Completed \n")

    
    def create_collection(self, collection_name):
        """Creating collection for testing"""
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
        print('Selecting Link tab \n')
        links = "//div[@id='subNavigationBar']/ul[2]//a[.='Links']"
        links_sitem = self.locator_finder_by_xpath(links)
        links_sitem.click()
        time.sleep(1)

        print('Entering collection name to the link \n')
        select_col = "(//input[@placeholder='Enter a collection name'])[1]"
        select_col_sitem = self.locator_finder_by_xpath(select_col)
        select_col_sitem.click()
        select_col_sitem.send_keys(collection_name)
        time.sleep(1)

        print('Adding collection to the link \n')
        add_col = "(//li[@class='active'])[1]"
        add_col_stiem = self.locator_finder_by_xpath(add_col)
        add_col_stiem.click()
        time.sleep(1)

        print('Saving the updated views links\n')
        save_link = '//*[@id="modal-dialog"]/div/div/div[2]/button'
        save_link_sitem = self.locator_finder_by_xpath(save_link)
        save_link_sitem.click()
        time.sleep(2)

    def modify_connected_collection_of_link(self, collection_name):
        """This method will modify the connected collection"""
        print('Select my_collection \n')
        select_my_col = f"//*[text()='{collection_name}']"
        select_my_col_sitem = self.locator_finder_by_xpath(select_my_col)
        select_my_col_sitem.click()
        time.sleep(1)

        print('add text_de analyzer to the link \n')
        analyzer = "(//input[@placeholder='Start typing for suggestions.'])[1]"
        analyzer_sitem = self.locator_finder_by_xpath(analyzer)
        analyzer_sitem.click()
        analyzer_sitem.send_keys('text_d')
        time.sleep(1)

        print("Selecting my_delimiter analyzer\n")
        delimiter = "(//li[@class='active'])[1]"
        delimiter_sitem = self.locator_finder_by_xpath(delimiter)
        delimiter_sitem.click()
        time.sleep(1)

        print('Selecting include all fields\n')
        include = "//*[text()='Include All Fields']"
        include_sitem = self.locator_finder_by_xpath(include)
        include_sitem.click()
        time.sleep(1)

        print('Selecting Track List fields\n')
        track_list = "// *[text() = 'Track List Positions']"
        track_list_sitem = self.locator_finder_by_xpath(track_list)
        track_list_sitem.click()
        time.sleep(1)

        print('Selecting stored id fields\n')
        stored_id_list = "// *[text() = 'Store ID Values']"
        stored_id_list_sitem = self.locator_finder_by_xpath(stored_id_list)
        stored_id_list_sitem.click()
        time.sleep(1)

        print('Selecting background fields\n')
        background = "// *[text() = 'In Background']"
        background_sitem = self.locator_finder_by_xpath(background)
        background_sitem.click()
        time.sleep(1)

        print('Saving updated links\n')
        save = "//*[text()='Save View']"
        save_sitem = self.locator_finder_by_xpath(save)
        save_sitem.click()
        time.sleep(2)

    def creating_black_collection_and_analyzer(self):
        """Creating blank col and analyzer for testing"""
        print('creating blank collection and analyzer for link tab\n')
        # creating multiple character collection
        self.create_collection('my_collection')
        # creating single character collection
        self.create_collection('z')
        # go back to view tab
        self.navbar_goto("views")
        time.sleep(1)

    def checking_improved_views_for_v310(self, name, locator, is_cluster):
        """This method will check improved views for v3.10.x"""
        print(f'Checking {name} started \n')
        print(f"Selecting {name}'s settings button\n")
        self.select_views_settings()
        print("Sorting views to descending\n")
        self.select_sorting_views()
        print("Sorting views to ascending\n")
        self.select_sorting_views()
        self.select_views_settings()

        print("Views search option testing\n")
        self.search_views("improved_arangosearch_view_01", self.select_improved_arangosearch_view_01)
        self.search_views("improved_arangosearch_view_02", self.select_improved_arangosearch_view_02)

        print(f'Selecting {name} for checking \n')
        select_view_sitem = self.locator_finder_by_xpath(locator)
        select_view_sitem.click()
        time.sleep(1)

        print(f'Checking cleanup interval for the {name} \n')
        cleanup_interval = "/html/body/div[2]/div/div[2]/div[2]/div/div/div/div[1]/table/tbody/tr[2]/th[2]/input"
        cleanup_interval_sitem = self.locator_finder_by_xpath(cleanup_interval)
        cleanup_interval_sitem.click()
        cleanup_interval_sitem.clear()
        cleanup_interval_sitem.send_keys(3)
        time.sleep(1)

        print(f'Checking commit interval for the {name} \n')
        commit_interval = "/html/body/div[2]/div/div[2]/div[2]/div/div/div/div[1]/table/tbody/tr[3]/th[2]/input"
        commit_interval_sitem = self.locator_finder_by_xpath(commit_interval)
        commit_interval_sitem.click()
        commit_interval_sitem.clear()
        commit_interval_sitem.send_keys(1100)
        time.sleep(1)

        print(f'Checking consolidation interval time for the {name} \n')
        consolidation_interval = "/html/body/div[2]/div/div[2]/div[2]/div/div/div/div[1]/table/tbody/tr[4]/th[2]/input"
        consolidation_interval_sitem = self.locator_finder_by_xpath(consolidation_interval)
        consolidation_interval_sitem.click()
        consolidation_interval_sitem.clear()
        consolidation_interval_sitem.send_keys(1200)
        time.sleep(2)

        consolidation_template_str = lambda \
            leaflet: f'/html/body/div[2]/div/div[2]/div[2]/div/div/div/div[2]/table/tbody/tr[{leaflet}]/th[2]/input'

        consolidation_list = [consolidation_template_str(2),
                              consolidation_template_str(3),
                              consolidation_template_str(4),
                              consolidation_template_str(5)
                              ]
        print("Selecting segment min \n")
        segment_min = consolidation_list[0]
        segment_min_sitem = self.locator_finder_by_xpath(segment_min)
        segment_min_sitem.click()
        segment_min_sitem.clear()
        segment_min_sitem.send_keys("3")
        time.sleep(2)

        print("Selecting segment max \n")
        segment_max = consolidation_list[1]
        segment_max_sitem = self.locator_finder_by_xpath(segment_max)
        segment_max_sitem.click()
        segment_max_sitem.clear()
        segment_max_sitem.send_keys("12")
        time.sleep(2)

        print("Selecting segments byte max \n")
        segment_byte_max = consolidation_list[2]
        segment_byte_max_sitem = self.locator_finder_by_xpath(segment_byte_max)
        segment_byte_max_sitem.click()
        segment_byte_max_sitem.clear()
        segment_byte_max_sitem.send_keys("5368709128")
        time.sleep(2)

        print("Selecting segments bytes floor \n")
        segment_byte_floor = consolidation_list[3]
        segment_byte_floor_sitem = self.locator_finder_by_xpath(segment_byte_floor)
        segment_byte_floor_sitem.click()
        segment_byte_floor_sitem.clear()
        segment_byte_floor_sitem.send_keys("2097158")
        time.sleep(2)

        print(f'Checking unsaved changes pop-up dialogue \n')
        self.navbar_goto("graphs")
        time.sleep(3)

        cancel_popup = "modalButton0"
        cancel_popup_sitem = self.locator_finder_by_id(cancel_popup)
        cancel_popup_sitem.click()
        time.sleep(1)

        # at this point views will save and good to add more things to it
        print(f'Saving the changes for the {name} \n')
        save_changes = "//*[text()='Save View']"
        save_changes_sitem = self.locator_finder_by_xpath(save_changes)
        save_changes_sitem.click()
        time.sleep(2)

        # creating example collection & analyzer for the view
        self.creating_black_collection_and_analyzer()

        print(f'Selecting {name} again\n')
        select_view_sitem = self.locator_finder_by_xpath(locator)
        select_view_sitem.click()
        time.sleep(1)

        print('checking collection link started \n')
        self.adding_collection_to_the_link('my_collectio')
        self.modify_connected_collection_of_link('my_collection')

        self.adding_collection_to_the_link('z')
        self.modify_connected_collection_of_link('z')
        print('checking collection link completed \n')

        # json tab check start here
        print("Selecting json tab\n")
        json_tab = "//*[text()='JSON']"
        json_tab_sitem = self.locator_finder_by_xpath(json_tab)
        json_tab_sitem.click()
        time.sleep(1)

        self.select_collapse_btn()
        time.sleep(1)
        print("Selecting expand button \n")
        self.select_expand_btn()
        time.sleep(1)

        print('Discard the changes for JSON tab\n')
        discard = '//*[@id="Save"]/button'
        discard_sitem = self.locator_finder_by_xpath(discard)
        discard_sitem.click()
        time.sleep(1)

        # renaming views
        if is_cluster:
            print('Renaming views are disabled for the Cluster deployment')
        else:
            print(f"Rename {name} to modified_name started \n")
            print(f'Selecting {name} for renaming \n')

            self.select_views_tab()

            print(f'Selecting {name} for renaming \n')
            select_view_sitem = self.locator_finder_by_xpath(locator)
            select_view_sitem.click()   # already in the settings tab
            time.sleep(1)

            modified_name = "//input[@value='improved_arangosearch_view_01']"
            modified_name_sitem = self.locator_finder_by_xpath(modified_name)
            modified_name_sitem.click()
            modified_name_sitem.clear()
            modified_name_sitem.send_keys('modified_views_name')
            time.sleep(1)

            save = "//*[text()='Save View']"
            save_sitem = self.locator_finder_by_xpath(save)
            save_sitem.click()
            print("Rename the current Views completed \n")
        print(f'Checking {name} Completed \n')

    def checking_views_negative_scenario_for_views(self):
        """This method will check negative input for views name during creation"""
        self.select_views_tab()
        print('Selecting views create button \n')
        create_new_views_id = self.locator_finder_by_xpath(self.create_new_views_id)
        create_new_views_id.click()
        time.sleep(2)
        self.wait_for_ajax()

        print('Expected error scenario for the Views name started \n')
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
        print('Expected error scenario for the Views name completed \n')

        print('Expected error scenario for the Views write buffer idle started \n')
        error_input = ['@', '/', 'שלום', '9999999999999999']
        print_statement = ['Checking views name with "@"',
                           'Checking views name with "/"',
                           'Checking views name with "שלום"',
                           'Checking views name with "9999999999999999"']
        error = 'Only non-negative integers allowed.'
        error_message = [error, error, error, error]

        if self.current_package_version() >= semver.VersionInfo.parse("3.9.0"):
            print(f'Select advance options \n')
            advance_option = '//*[@id="accordion4"]/div/div[1]/a/span[2]/b'
            advance_option_sitem = self.locator_finder_by_xpath(advance_option)
            advance_option_sitem.click()
            time.sleep(2)
            self.wait_for_ajax()

            print(f'Select write buffer idle value\n')
            buffer_locator_id = "//input[@value='64']"
            error_locator_id = '//*[@id="row_newWriteBufferIdle"]/th[2]/p'

            # method template (self, error_input, print_statement, error_message, locators_id, error_message_id)
            self.check_expected_error_messages_for_views(error_input,
                                                         print_statement,
                                                         error_message,
                                                         buffer_locator_id,
                                                         error_locator_id)
            print('Expected error scenario for the Views write buffer idle completed \n')

        print('Closing the views creation \n')
        close_btn = '//*[@id="modalButton0"]'
        close_btn_sitem = self.locator_finder_by_xpath(close_btn)
        close_btn_sitem.click()
        time.sleep(3)
        self.wait_for_ajax()


    def delete_views(self, name, locator):
        """This method will delete views"""
        
        try:
            self.select_views_tab()
            self.wait_for_ajax()
            print(f"Selecting {name} for deleting \n")
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
            print(f"Selecting {name} for deleting completed \n")
            time.sleep(1)
            self.wait_for_ajax()
        except TimeoutException as e:
            print('TimeoutException occurred! \n')
            print('Info: Views has already been deleted or never created. \n')
        except Exception:
            traceback.print_exc()
            raise Exception('Critical Error occurred and need manual inspection!! \n')

    def delete_created_collection(self, col_name):
        """this method will delete all the collection created for views"""
        try:
            print('Selecting collection tab\n')
            self.navbar_goto("collections")
            time.sleep(1)

            print('Deleting collection started\n')
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

            confirm = "/html/body/div[2]/div/div[2]/div[2]/div/div[3]/button[1]"
            confirm_sitem = self.locator_finder_by_xpath(confirm)
            confirm_sitem.click()
            time.sleep(1)
        except TimeoutException:
            print('TimeoutException occurred! \n')
            print(f'Info: {col_name} has already been deleted or never created. \n')
        except Exception:
            traceback.print_exc()
            raise Exception('Critical Error occurred and need manual inspection!! \n')

    
    def delete_new_views(self, name):
        """this method will delete all the newer version views"""
        self.select_views_tab()
        print(f"{name} start deleting \n")
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

            delete = '//*[@id="Actions"]/button'
            delete_sitem = self.locator_finder_by_xpath(delete)
            delete_sitem.click()
            time.sleep(2)

            delete_btn = '/html/body/div[10]/div/div[3]/button[2]'
            delete_btn_sitem = self.locator_finder_by_xpath(delete_btn)
            delete_btn_sitem.click()
            time.sleep(2)

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

            self.driver.refresh()
            time.sleep(2)
        except TimeoutException:
            print('TimeoutException occurred! \n')
            print(f'Info: {name} has already been deleted or never created. \n')
        except Exception:
            traceback.print_exc()
            raise Exception('Critical Error occurred and need manual inspection!! \n')
