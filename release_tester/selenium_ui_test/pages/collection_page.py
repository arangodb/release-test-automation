#!/usr/bin/env python3
""" collection page object """
import time
import traceback
import json
import semver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium_ui_test.pages.navbar import NavigationBarPage


# can't circumvent long lines.. nAttr nLines
# pylint: disable=line-too-long disable=too-many-instance-attributes disable=too-many-statements
# pylint: disable=too-many-public-methods disable=too-many-lines disable=too-many-locals
# pylint: disable=too-many-branches


class CollectionPage(NavigationBarPage):
    """Collection page class"""

    def __init__(self, webdriver, cfg, video_start_time):
        """class initialization"""
        super().__init__(webdriver, cfg, video_start_time)
        self.select_collection_page_id = "collections"
        self.select_create_collection_id = "createCollection"
        self.select_new_collection_name_id = "new-collection-name"
        self.select_collection_type_id = "new-collection-type"
        # fixme
        # self.select_advance_option_id = "/html//div[@id='accordion2']//a[@href='#collapseOne']"
        self.select_advance_option_id = '//*[@id="accordion2"]/div/div[1]/a/span[2]/b'
        self.wait_for_sync_id = "new-collection-sync"
        self.create_new_collection_btn_id = "modalButton1"
        self.select_collection_settings_id = "collectionsToggle"
        self.display_system_collection_id = (
            "//div[@id='collectionsDropdown']/ul[1]/li[2]/a/label[@class='checkbox checkboxLabel']"
        )
        self.display_document_collection_id = (
            "//div[@id='collectionsDropdown']/ul[1]/li[3]/a/label[@class='checkbox checkboxLabel']"
        )
        self.display_edge_collection_id = (
            "//div[@id='collectionsDropdown']/ul[1]/li[4]/a/label[@class='checkbox checkboxLabel']"
        )
        self.select_status_loaded_id = (
            "//div[@id='collectionsDropdown']/ul[2]/li[2]/a[@href='#']/label[@class='checkbox checkboxLabel']"
        )
        self.select_status_unloaded_id = (
            "//div[@id='collectionsDropdown']/ul[2]/li[3]/a[@href='#']/label[@class='checkbox checkboxLabel']"
        )
        self.sort_by_name_id = '//*[@id="collectionsDropdown"]/ul[2]/li[2]/a/label/i'
        self.sort_by_type_id = '//*[@id="collectionsDropdown"]/ul[2]/li[3]/a/label/i'
        self.sort_descending_id = '//*[@id="collectionsDropdown"]/ul[2]/li[4]/a/label/i'

        if self.current_package_version() >= semver.VersionInfo.parse("3.11.99"):
            self.select_doc_collection_id = "(//a[normalize-space()='TestDoc'])[1]"
        else:
            self.select_doc_collection_id = '//*[@id="collection_TestDoc"]/div/h5'

        self.select_upload_btn_id = "/html//a[@id='importCollection']"

        self.select_choose_file_btn_id = "/html//input[@id='importDocuments']"
        self.select_confirm_upload_btn_id = "confirmDocImport"
        self.getting_total_row_count_id = "/html//a[@id='totalDocuments']"
        self.display_document_size_id = "documentSize"
        self.move_first_page_id = "//div[@id='documentsToolbarF']/ul[@class='arango-pagination']//a[.='1']"
        self.move_second_page_id = "//div[@id='documentsToolbarF']/ul[@class='arango-pagination']//a[.='2']"

        self.select_collection_setting_id = "//div[@id='subNavigationBarPage']/ul[2]//a[.='Settings']"
        self.select_hand_pointer_id = "/html//a[@id='markDocuments']"

        self.row1_id = "//div[@id='docPureTable']/div[2]/div[1]"
        self.row2_id = "//div[@id='docPureTable']/div[2]/div[3]"
        self.row3_id = "//div[@id='docPureTable']/div[2]/div[5]"
        self.row4_id = "//div[@id='docPureTable']/div[2]/div[7]"
        self.move_btn_id = "/html//button[@id='moveSelected']"
        self.move_doc_textbox_id = "move-documents-to"
        self.move_confirm_btn_id = "modalButton1"
        self.select_collection_delete_btn_id = "deleteSelected"
        self.collection_delete_confirm_btn_id = """//div[@id="modalPlaceholder"]//button[text()="Delete"]"""
        self.collection_really_dlt_btn_id = "/html//button[@id='modal-confirm-delete']"
        self.select_index_type_id = "newIndexType"

        self.select_geo_fields_id = "newGeoFields"
        self.select_geo_name_id = "newGeoName"
        self.select_geo_json_id = "newGeoJson"
        self.select_geo_background_id = "newGeoBackground"
        self.select_persistent_fields_id = "newPersistentFields"
        self.select_persistent_name_id = "newPersistentName"
        self.select_persistent_unique_id = "newPersistentUnique"
        self.select_persistent_sparse_id = "newPersistentSparse"
        self.select_persistent_duplicate_id = "newPersistentDeduplicate"
        self.select_persistent_background_id = "newPersistentBackground"

        self.select_fulltext_field_id = "newFulltextFields"
        self.select_fulltext_name_id = "newFulltextName"
        self.select_fulltext_length_id = "newFulltextMinLength"
        self.select_fulltext_background_id = "newFulltextBackground"

        self.select_ttl_field_id = "newTtlFields"
        self.select_ttl_name_id = "newTtlName"
        self.select_ttl_expiry_id = "newTtlExpireAfter"
        self.select_ttl_background_id = "newTtlBackground"

        self.select_index_for_delete_id = '//*[@id="content-react"]/div/div/div/table/tbody/tr[2]/td[10]/div/button'
        self.select_index_confirm_delete = "indexConfirmDelete"
        self.select_info_tab_id = "//*[@id='subNavigationBarPage']/ul[2]/li[3]/a"

        self.select_schema_tab_id = "//*[@id='subNavigationBarPage']/ul[2]/li[5]/a"


        self.select_settings_name_textbox_id = '//*[@id="change-collection-name"]'
        self.select_settings_wait_type_id = "change-collection-sync"
        self.select_newer_settings_save_btn_id = "modalButton4"
        self.select_new_settings_save_btn_id = "modalButton5"

        self.select_load_index_into_memory_id = "//*[@id='modalButton2']"
        self.select_settings_unload_btn_id = "modalButton3"
        self.select_truncate_btn_id = "modalButton1"
        self.select_truncate_confirm_btn_id = "//*[@id='modal-confirm-delete']"
        self.delete_collection_id = "//*[@id='modalButton0']"
        self.delete_collection_confirm_id = "//*[@id='modal-confirm-delete']"

        self.select_edge_collection_upload_id = "//*[@id='collection_TestEdge']/div/h5"
        self.select_edge_collection_id = "//*[@id='collection_TestEdge']/div/h5"
        self.select_edge_settings_id = "//*[@id='subNavigationBarPage']/ul[2]/li[4]/a"
        self.select_test_doc_settings_id = "//*[@id='subNavigationBarPage']/ul[2]/li[4]/a"

        self.select_test_doc_collection_id = "//div[@id='collection_Test']//h5[@class='collectionName']"
        # self.select_collection_search_id = "//*[@id='searchInput']"

        self.select_export_doc_as_jason_id = "//*[@id='exportCollection']/span/i"
        self.select_export_doc_confirm_btn_id = "exportDocuments"

        self.select_filter_collection_id = "//*[@id='filterCollection']/span/i"
        self.select_filter_input_id = "attribute_name0"
        self.select_filter_operator_id = "operator0"
        self.select_filter_attribute_value_id = "attribute_value0"
        self.select_filter_btn_id = "//*[@id='filterSend']"
        self.select_row4_id = "//div[@id='docPureTable']/div[2]/div[5]"
        self.document_id = "document-id"
        self.select_filter_reset_btn_id = "/html//button[@id='resetView']"
        self.select_renamed_doc_collection_id = '//*[@id="collection_testDocRenamed"]/div/h5'
        self.select_computed_value_col_id = '//*[@id="collection_ComputedValueCol"]/div/h5'

    def select_collection_page(self):
        """selecting collection tab"""
        self.navbar_goto("collections")
        self.webdriver.refresh()
        self.wait_for_ajax()
        time.sleep(1)

    def select_create_collection(self):
        """Clicking on create new collection box"""
        select_create_collection_sitem = self.locator_finder_by_id(self.select_create_collection_id, benchmark=True)
        select_create_collection_sitem.click()
        time.sleep(1)

    def select_new_collection_name(self, name):
        """Providing new collection name"""
        select_new_collection_name_sitem = self.locator_finder_by_id(self.select_new_collection_name_id)
        select_new_collection_name_sitem.click()
        select_new_collection_name_sitem.send_keys(name)
        time.sleep(1)

    def select_collection_type(self, value):
        """Selecting collection Document type where # '2' = Document, '3' = Edge"""
        self.locator_finder_by_select(self.select_collection_type_id, value)
        time.sleep(1)

    def select_number_of_shards(self, shard_value):
        """selecting number of shards for the collection"""
        shards = "new-collection-shards"
        shards_sitem = self.locator_finder_by_id(shards)
        shards_sitem.click()
        shards_sitem.clear()
        shards_sitem.send_keys(shard_value)
        time.sleep(2)

    def select_replication_factor(self, rf_value):
        """selecting number of replication factor for the collection"""
        rf_sitem = self.locator_finder_by_id("new-replication-factor")
        rf_sitem.click()
        rf_sitem.clear()
        rf_sitem.send_keys(rf_value)
        time.sleep(2)

    def select_advance_option(self):
        """Selecting collection advance options"""
        select_advance_option_sitem = self.locator_finder_by_xpath(self.select_advance_option_id)
        select_advance_option_sitem.click()
        time.sleep(1)

    def wait_for_sync(self, value):
        """Selecting collection wait type where value # 0 = YES, '1' = NO"""
        self.locator_finder_by_select(self.wait_for_sync_id, value)
        time.sleep(1)

    def create_new_collection_btn(self):
        """Select create new collection button"""
        create_new_collection_btn_sitem = self.locator_finder_by_id(self.create_new_collection_btn_id)
        create_new_collection_btn_sitem.click()
        time.sleep(3)

    def create_new_collections(self, name, doc_type, is_cluster):
        """This method will create new collection based on their name and type"""
        self.tprint('selecting collection tab \n')
        self.navbar_goto("collections")
        time.sleep(1)

        if self.current_package_version() >= semver.VersionInfo.parse("3.11.99"):
            select_create_collection_id = "//*[text()='Add collection']"
            select_create_collection_sitem = self.locator_finder_by_xpath(select_create_collection_id, benchmark=True)
        else:
            select_create_collection_id = "createCollection"
            select_create_collection_sitem = self.locator_finder_by_id(select_create_collection_id, benchmark=True)

        select_create_collection_sitem.click()
        time.sleep(3)

        self.tprint("Selecting new collection name \n")
        if self.current_package_version() >= semver.VersionInfo.parse("3.11.99"):
            select_new_collection_name_sitem = self.locator_finder_by_id("name")
        else:
            select_new_collection_name_sitem = self.locator_finder_by_id("new-collection-name")

        select_new_collection_name_sitem.click()
        select_new_collection_name_sitem.send_keys(name)
        time.sleep(3)

        self.tprint(f'Selecting collection type for {name} \n')
        if self.current_package_version() >= semver.VersionInfo.parse("3.11.99"):
            if doc_type == 1:
                # type dropdown menu
                type_dropdown = "(//div[@class=' css-nmh171'])[1]"
                type_dropdown_sitem = self.locator_finder_by_xpath(type_dropdown)
                type_dropdown_sitem.click()
                time.sleep(3)

                # choosing type
                chosen_type = "//*[text()='Edge']"
                chosen_type_sitem = self.locator_finder_by_xpath(chosen_type)
                chosen_type_sitem.click()
                time.sleep(3)
        else:
            self.locator_finder_by_select("new-collection-type", doc_type)
        time.sleep(3)

        if is_cluster:
            if self.current_package_version() >= semver.VersionInfo.parse("3.11.99"):
                advance_option = "//div[contains(text(), 'Advanced')]"
                advance_option_sitem = self.locator_finder_by_xpath(advance_option)
                advance_option_sitem.click()
                time.sleep(1)

                try:
                    self.tprint(f"selecting number of Shards for the {name} \n")
                    shards = "numberOfShards"
                    shards_sitem = self.locator_finder_by_id(shards)
                    shards_sitem.click()
                    shards_sitem.clear()
                    shards_sitem.send_keys(Keys.BACKSPACE, "9")
                    time.sleep(2)

                    self.tprint(f"selecting number of replication factor for {name} \n")
                    rf = "replicationFactor"
                    rf_sitem = self.locator_finder_by_id(rf)
                    rf_sitem.click()
                    rf_sitem.clear()
                    rf_sitem.send_keys(Keys.BACKSPACE, "3")
                    time.sleep(2)
                except Exception as e:
                    self.tprint("Might be failed due to forced-one-shard option is enabled, need a fix \n")
                    self.tprint(str(e))
            else:
                if self.is_one_sharded:
                    print("We're in one sharded mode - skipping shards related options...")
                    time.sleep(2)
                else:
                    self.tprint(f"selecting number of Shards for the {name} \n")
                    time.sleep(15)
                    shards = "new-collection-shards"
                    shards_sitem = self.locator_finder_by_id(shards)
                    shards_sitem.click()
                    shards_sitem.clear()
                    shards_sitem.send_keys(9)
                    time.sleep(2)

                    self.tprint(f"selecting number of replication factor for {name} \n")
                    rf = "new-replication-factor"
                    rf_sitem = self.locator_finder_by_id(rf)
                    rf_sitem.click()
                    rf_sitem.clear()
                    rf_sitem.send_keys(3)
                    time.sleep(2)

        if self.current_package_version() >= semver.VersionInfo.parse("3.11.99"):
            if not is_cluster:
                # selecting sync btn if deployment is not a cluster
                wait_for_sync = "//*[contains(text(),'Advanced')]"
                self.locator_finder_by_xpath(wait_for_sync).click()

            # toggle sync option
            sync_toggle = "//*[contains(text(),'Wait for sync')]"
            self.locator_finder_by_xpath(sync_toggle).click()

        else:
            self.tprint(f"Selecting collection advance options for {name} \n")
            select_advance_option_sitem = self.locator_finder_by_xpath(self.select_advance_option_id)
            select_advance_option_sitem.click()
            time.sleep(1)
            self.locator_finder_by_select(self.wait_for_sync_id, 0)
        time.sleep(1)

        self.tprint(f"Selecting create button for {name} \n")
        if self.current_package_version() >= semver.VersionInfo.parse("3.11.99"):
            create_button = "(//button[normalize-space()='Create'])[1]"
            create_button_sitem = self.locator_finder_by_xpath(create_button)
            create_button_sitem.click()
        else:
            create_new_collection_btn_sitem = self.locator_finder_by_id("modalButton1")
            create_new_collection_btn_sitem.click()
        time.sleep(3)
        self.webdriver.refresh()

    def ace_set_value(self, query):
        """This method will take a string argument and will execute the query on ace editor"""
        warning = 'button-warning'
        warning_sitem = self.locator_finder_by_class(warning)
        # Set x and y offset positions of element
        x_offset = 100
        y_offset = 100
        # Performs mouse move action onto the element
        actions = ActionChains(self.webdriver).move_to_element_with_offset(warning_sitem, x_offset, y_offset)
        actions.click()
        actions.key_down(Keys.CONTROL).send_keys('a').send_keys(Keys.BACKSPACE).key_up(Keys.CONTROL)
        time.sleep(1)
        actions.send_keys(f'{query}')
        actions.perform()
        time.sleep(1)

        self.tprint("Saving current computed value")
        save_computed_value = 'saveComputedValuesButton'
        save_computed_value_sitem = self.locator_finder_by_id(save_computed_value)
        save_computed_value_sitem.click()
        time.sleep(2)

        self.webdriver.refresh()

    def checking_search_options(self, search=""):
        """Checking search functionality for v312 and else part is for v311 & v310"""
        self.tprint("selecting collection tab \n")
        self.navbar_goto("collections")
        time.sleep(1)
        if self.current_package_version() >= semver.VersionInfo.parse("3.11.99"):
            # choose filter for clear any preselected filter
            filter_btn = "//button[contains(text(), 'Filters')]"
            filter_btn_sitem = self.locator_finder_by_xpath(filter_btn)
            filter_btn_sitem.click()
            time.sleep(3)

            # select clear all filter button
            clear_all_filter = "//button[contains(text(), 'Clear')]"
            clear_all_filter_sitem = self.locator_finder_by_xpath(clear_all_filter)
            clear_all_filter_sitem.click()
            time.sleep(3)

            self.tprint('the current UI for cleaning anything else \n')
            self.webdriver.refresh()

            self.tprint("filter btn again for searching \n")
            add_filter_btn = "//button[contains(text(),'Filters')]"
            add_filter_btn_stiem = self.locator_finder_by_xpath(add_filter_btn)
            add_filter_btn_stiem.click()
            time.sleep(3)

            self.tprint("selecting collection filter \n")
            id_filter_name = "//*[@aria-label='Add filter']"
            id_filter_name_stiem = self.locator_finder_by_xpath(id_filter_name)
            id_filter_name_stiem.click()
            time.sleep(3)

            self.tprint('selecting name filter from the list \n')
            search_filter = "//button[contains(text(),'Name')]"
            search_filter_sitem = self.locator_finder_by_xpath(search_filter)
            search_filter_sitem.click()
            time.sleep(3)

            self.tprint("selecting search placeholder and send search input TestDoc \n")
            search_collection_test_doc = "//*[@placeholder='Search']"
            search_collection_test_doc_sitem = self.locator_finder_by_xpath(search_collection_test_doc)
            search_collection_test_doc_sitem.click()
            search_collection_test_doc_sitem.clear()
            search_collection_test_doc_sitem.send_keys("TestDoc")
            time.sleep(3)

            self.tprint("invoke refresh to go out from the search option and test search works \n")
            self.webdriver.refresh()

            self.tprint("trying to find the expected collection from the search")
            search_test_doc_col = "//a[contains(text(), 'TestDoc')]"
            search_test_doc_col_sitem = self.locator_finder_by_xpath(search_test_doc_col)
            time.sleep(3)

            expected_msg = "TestDoc"
            assert (
                expected_msg == search_test_doc_col_sitem.text
            ), f"Expected {expected_msg} but got {search_test_doc_col_sitem.text}"

            self.tprint("after getting TestDoc now clear the name filter")
            # selecting filter btn again
            add_filter_btn_again = "//button[contains(text(),'Filters')]"
            add_filter_btn_again_stiem = self.locator_finder_by_xpath(add_filter_btn_again)
            add_filter_btn_again_stiem.click()
            time.sleep(3)

            # selecting clear btn again
            clear_all_filter_again = "//button[contains(text(), 'Clear')]"
            clear_all_filter_again_sitem = self.locator_finder_by_xpath(clear_all_filter_again)
            clear_all_filter_again_sitem.click()
            time.sleep(3)

            # select refresh() to clear anything else in the UI
            self.webdriver.refresh()

        # testing search options for v310 and v311

        else:
            select_collection_search_id = "//*[@id='searchInput']"
            select_collection_search_sitem = self.locator_finder_by_xpath(
                select_collection_search_id
            )
            select_collection_search_sitem.click()
            select_collection_search_sitem.clear()
            select_collection_search_sitem.send_keys(search)

        time.sleep(2)

    def select_collection_settings(self):
        """selecting collection settings icon"""
        select_collection_settings_sitem = self.locator_finder_by_id(self.select_collection_settings_id, benchmark=True)
        select_collection_settings_sitem.click()
        time.sleep(2)

    def display_system_collection(self):
        """Displaying system's collection"""
        display_system_collection_sitem = self.locator_finder_by_xpath(self.display_system_collection_id)
        display_system_collection_sitem.click()
        time.sleep(2)

    def display_document_collection(self):
        """Displaying Document type collection"""
        display_document_collection_sitem = self.locator_finder_by_xpath(self.display_document_collection_id)
        display_document_collection_sitem.click()
        time.sleep(2)

    def display_edge_collection(self):
        """Displaying Edge type collection"""
        display_edge_collection_sitem = self.locator_finder_by_xpath(self.display_edge_collection_id)
        display_edge_collection_sitem.click()
        time.sleep(2)

    def select_status_loaded(self):
        """Displaying status loaded collection"""
        select_status_loaded_sitem = self.locator_finder_by_xpath(self.select_status_loaded_id, benchmark=True)
        select_status_loaded_sitem.click()
        time.sleep(2)

    def select_status_unloaded(self):
        """Displaying status unloaded collection"""
        select_status_unloaded_sitem = self.locator_finder_by_xpath(self.select_status_unloaded_id)
        select_status_unloaded_sitem.click()
        time.sleep(2)

    def sort_by_type(self):
        """Sorting collection by type"""
        if self.current_package_version() == semver.VersionInfo.parse("3.8.0"):
            sort_by_type = '//*[@id="collectionsDropdown"]/ul[3]/li[3]/a/label'
            sort_by_type_sitem = self.locator_finder_by_xpath(sort_by_type)
        else:
            sort_by_type_sitem = self.locator_finder_by_xpath(self.sort_by_type_id)

        sort_by_type_sitem.click()
        time.sleep(2)

    def sort_by_name(self):
        """Sorting collection by name"""

        if self.current_package_version() == semver.VersionInfo.parse("3.8.0"):
            name = '//*[@id="collectionsDropdown"]/ul[3]/li[2]/a/label'
            sort_by_name_sitem = self.locator_finder_by_xpath(name)
        else:
            sort_by_name_sitem = self.locator_finder_by_xpath(self.sort_by_name_id)
        sort_by_name_sitem.click()
        time.sleep(2)

    def sort_descending(self):
        """Sorting collection by descending"""
        if self.current_package_version() == semver.VersionInfo.parse("3.8.0"):
            sort_by_descending = '//*[@id="collectionsDropdown"]/ul[3]/li[4]/a/label/i'
            sort_descending_sitem = self.locator_finder_by_xpath(sort_by_descending)
        else:
            sort_descending_sitem = self.locator_finder_by_xpath(self.sort_descending_id)
        sort_descending_sitem.click()
        time.sleep(2)

    def select_upload_btn(self):
        """selecting collection upload btn"""
        select_upload_btn_sitem = self.locator_finder_by_xpath(self.select_upload_btn_id)
        select_upload_btn_sitem.click()
        time.sleep(3)

    def select_choose_file_btn(self, path):
        """This method will upload the file with the file path given"""
        select_choose_file_btn_sitem = self.locator_finder_by_xpath(self.select_choose_file_btn_id)
        time.sleep(2)
        select_choose_file_btn_sitem.send_keys(path)

    def select_confirm_upload_btn(self):
        """Confirm file upload btn"""
        select_confirm_upload_btn_sitem = self.locator_finder_by_id(self.select_confirm_upload_btn_id)
        select_confirm_upload_btn_sitem.click()

    def getting_total_row_count(self):
        """getting_total_row_count"""
        # ATTENTION: this will only be visible & successfull if the browser window is wide enough!
        size = self.webdriver.get_window_size()
        if size["width"] > 1000:
            getting_total_row_count_sitem = self.locator_finder_by_xpath(self.getting_total_row_count_id, 20)
            return getting_total_row_count_sitem.text
        self.tprint("your browser window is to narrow! " + str(size))
        return "-1"

    def download_doc_as_json(self):
        """Exporting documents as JSON file from the collection"""
        if self.webdriver.name == "chrome":  # this will check browser name
            self.tprint("Download has been disabled for the Chrome browser \n")
        else:
            select_export_doc_as_jason_sitem = self.locator_finder_by_xpath(self.select_export_doc_as_jason_id)
            select_export_doc_as_jason_sitem.click()
            time.sleep(1)
            select_export_doc_confirm_btn_sitem = self.locator_finder_by_id(self.select_export_doc_confirm_btn_id)
            select_export_doc_confirm_btn_sitem.click()
            time.sleep(2)
            # self.clear_download_bar()

    def filter_documents(self, value):
        """Checking Filter functionality"""
        select_filter_collection_sitem = self.locator_finder_by_xpath(self.select_filter_collection_id)
        select_filter_collection_sitem.click()
        time.sleep(1)

        select_row4_sitem = self.locator_finder_by_xpath(self.select_row4_id)
        select_row4_sitem.click()
        time.sleep(1)
        document_sitem = self.locator_finder_by_id(self.document_id)
        string = document_sitem.text
        # self.tprint(string[8:])
        self.webdriver.back()
        time.sleep(1)

        select_filter_input_sitem = self.locator_finder_by_id(self.select_filter_input_id)
        select_filter_input_sitem.click()
        select_filter_input_sitem.clear()
        select_filter_input_sitem.send_keys("_id")
        time.sleep(1)

        self.locator_finder_by_select(self.select_filter_operator_id, value)
        time.sleep(1)

        select_filter_attribute_value_sitem = self.locator_finder_by_id(self.select_filter_attribute_value_id)
        select_filter_attribute_value_sitem.click()
        select_filter_attribute_value_sitem.clear()
        select_filter_attribute_value_sitem.send_keys(string)
        time.sleep(1)

        select_filter_btn_sitem = self.locator_finder_by_xpath(self.select_filter_btn_id)
        select_filter_btn_sitem.click()
        time.sleep(3)

        select_filter_reset_btn_sitem = self.locator_finder_by_xpath(self.select_filter_reset_btn_id)
        select_filter_reset_btn_sitem.click()
        time.sleep(2)

    def display_document_size(self, value):
        """Choose how many rows of docs will be display"""
        self.locator_finder_by_select(self.display_document_size_id, value)
        time.sleep(2)

    def traverse_search_pages(self):
        """After changing the document display size checking everything loads"""
        self.wait_for_ajax()
        self.locator_finder_by_hover_item(self.move_second_page_id)
        time.sleep(2)
        self.wait_for_ajax()
        self.locator_finder_by_hover_item(self.move_first_page_id)
        time.sleep(2)

    def select_hand_pointer(self):
        """Selecting Hand selection button"""
        self.locator_finder_by_hover_item(self.select_hand_pointer_id)
        time.sleep(1)

    def select_multiple_item(self):
        """selecting multiple document rows from the current collection"""
        time.sleep(2)
        self.wait_for_ajax()
        self.locator_finder_by_hover_item(self.row1_id)
        self.locator_finder_by_hover_item(self.row2_id)
        self.locator_finder_by_hover_item(self.row3_id)
        self.locator_finder_by_hover_item(self.row4_id)
        time.sleep(1)
        self.wait_for_ajax()

    def move_btn(self):
        """selecting collection move button after selecting"""
        self.locator_finder_by_hover_item(self.move_btn_id)
        time.sleep(1)

    def move_doc_textbox(self, collection):
        """selecting Collection to move the selected data"""
        self.wait_for_ajax()
        move_doc_textbox_sitem = self.locator_finder_by_id(self.move_doc_textbox_id, 20)
        move_doc_textbox_sitem.click()
        move_doc_textbox_sitem.send_keys(collection)
        time.sleep(1)

    def move_confirm_btn(self):
        """Confirming move data to the Collection"""
        self.wait_for_ajax()
        move_confirm_btn_sitem = self.locator_finder_by_id(self.move_confirm_btn_id, 20)
        move_confirm_btn_sitem.click()
        time.sleep(1)

    def select_collection_delete_btn(self):
        """Selecting delete button for selected data"""
        select_collection_delete_btn_sitem = self.locator_finder_by_id(self.select_collection_delete_btn_id)
        select_collection_delete_btn_sitem.click()
        time.sleep(1)

    def collection_delete_confirm_btn(self):
        """Selecting delete button for selected data"""
        collection_delete_confirm_btn_sitem = self.locator_finder_by_xpath(self.collection_delete_confirm_btn_id)
        collection_delete_confirm_btn_sitem.click()
        time.sleep(1)

    def collection_really_dlt_btn(self):
        """Selecting really delete button for selected data"""
        collection_really_dlt_btn_sitem = self.locator_finder_by_xpath(self.collection_really_dlt_btn_id)
        collection_really_dlt_btn_sitem.click()
        self.webdriver.refresh()
        time.sleep(1)

    def select_index_menu(self):
        """Selecting index menu from collection"""
        self.wait_for_ajax()
        self.click_submenu_entry("Indexes")

    def select_desired_index_from_the_list(self, index_name):
        """this method will find the desired index from the list using given locator"""
        select_index = "(//*[name()='svg'][@class='css-8mmkcg'])"
        select_index_sitem = self.locator_finder_by_xpath(select_index)
        select_index_sitem.click()
        time.sleep(1)

        element = self.locator_finder_by_xpath(f"//*[contains(text(), '{index_name}')]")
        actions = ActionChains(self.webdriver)
        # Move the mouse pointer to the element containing the text
        actions.move_to_element(element)
        # Perform a click action
        actions.click().perform()

    def create_index(self, index_name):
        """This method will create indexes for >= v3.11.0"""
        self.tprint(f"Creating {index_name} index started \n")
        if self.current_package_version() >= semver.VersionInfo.parse("3.11.99"):
            add_index = '//button[text()="Add index"]'
        else:
            add_index = '//button[text()="Add Index"]'

        create_new_index_btn_sitem = self.locator_finder_by_xpath(add_index)
        create_new_index_btn_sitem.click()
        time.sleep(2)

        self.tprint(f"selecting {index_name} from the list\n")

        if index_name == 'Persistent':
            # selecting persistent index's filed
            persistent_field = "/html//input[@id='fields']"
            persistent_field_sitem = self.locator_finder_by_xpath(persistent_field, benchmark=True)
            persistent_field_sitem.click()
            persistent_field_sitem.send_keys('name')

            # selecting persistent index's name
            persistent_name = "/html//input[@id='name']"
            persistent_name_sitem = self.locator_finder_by_xpath(persistent_name)
            persistent_name_sitem.click()
            persistent_name_sitem.send_keys(index_name)

            # selecting persistent index's extra value
            extra_value = "/html//input[@id='storedValues']"
            extra_value_sitem = self.locator_finder_by_xpath(extra_value)
            extra_value_sitem.click()
            extra_value_sitem.send_keys('email, likes')

            # selecting persistent index's sparse value
            sparse = "(//span[@aria-hidden='true'])[1]"
            sparse_sitem = self.locator_finder_by_xpath(sparse)
            sparse_sitem.click()

            # selecting persistent index's duplicate array value
            duplicate_array = (
                "(//label[normalize-space()='Deduplicate array values'])[1]"
            )
            duplicate_array_sitem = self.locator_finder_by_xpath(duplicate_array)
            duplicate_array_sitem.click()

            memory_cache = "(//label[normalize-space()='Enable in-memory cache for index lookups'])[1]"
            memory_cache_sitem = self.locator_finder_by_xpath(memory_cache)
            memory_cache_sitem.click()

        elif index_name == 'Geo':
            self.select_desired_index_from_the_list('Geo Index')
            # selecting geo index's filed
            geo_field = "/html//input[@id='fields']"
            geo_field_sitem = self.locator_finder_by_xpath(geo_field, benchmark=True)
            geo_field_sitem.click()
            geo_field_sitem.send_keys('region')

            # selecting geo index's name
            geo_name = "/html//input[@id='name']"
            geo_name_sitem = self.locator_finder_by_xpath(geo_name)
            geo_name_sitem.click()
            geo_name_sitem.send_keys(index_name)

        elif index_name == 'Fulltext':
            self.select_desired_index_from_the_list('Fulltext Index')
            # selecting fullText index's filed
            full_text_field = "/html//input[@id='fields']"
            full_text_field_sitem = self.locator_finder_by_xpath(full_text_field, benchmark=True)
            full_text_field_sitem.click()
            full_text_field_sitem.send_keys('region')

            # selecting fullText index's name
            full_text_name = "/html//input[@id='name']"
            full_text_name_sitem = self.locator_finder_by_xpath(full_text_name)
            full_text_name_sitem.click()
            full_text_name_sitem.send_keys(index_name)

            # selecting fullText index's min length
            min_length = "/html//input[@id='minLength']"
            min_length_sitem = self.locator_finder_by_xpath(min_length)
            min_length_sitem.click()
            min_length_sitem.send_keys()

        elif index_name == 'TTL':
            self.select_desired_index_from_the_list('TTL Index')
            # selecting ttl index's filed
            ttl_field = "/html//input[@id='fields']"
            ttl_field_sitem = self.locator_finder_by_xpath(ttl_field, benchmark=True)
            ttl_field_sitem.click()
            ttl_field_sitem.send_keys('region')

            # selecting ttl index's name
            ttl_name = "/html//input[@id='name']"
            ttl_name_sitem = self.locator_finder_by_xpath(ttl_name)
            ttl_name_sitem.click()
            ttl_name_sitem.send_keys(index_name)

            ttl_expire = "/html//input[@id='expireAfter']"
            ttl_expire_sitem = self.locator_finder_by_xpath(ttl_expire)
            ttl_expire_sitem.click()
            ttl_expire_sitem.send_keys(1000)

        elif index_name == 'Inverted Index':
            action = ActionChains(self.webdriver)
            self.select_desired_index_from_the_list('Inverted Index')

            if self.current_package_version() >= semver.VersionInfo.parse("3.11.99"):
                fields = '//label[text()="Fields"][1]'
            else:
                fields = "(//div[contains(@class,'css-1d6mnfj')])[2]"

            fields_sitem = self.locator_finder_by_xpath(fields, benchmark=True)
            fields_sitem.click()
            action.send_keys('region').send_keys(Keys.ENTER).send_keys('name').send_keys(Keys.ENTER).perform()
            time.sleep(1)

            analyzer = "//*[text()='Analyzer']"
            analyzer_sitem = self.locator_finder_by_xpath(analyzer)
            analyzer_sitem.click()
            action.send_keys(Keys.DOWN).send_keys(Keys.ENTER).perform()
            time.sleep(1)

            include_all_fields = "//*[text()='Include All Fields']"
            include_all_fields_sitem = self.locator_finder_by_xpath(include_all_fields)
            include_all_fields_sitem.click()
            time.sleep(1)

            track_all_position = "//*[text()='Track List Positions']"
            track_all_position_sitem = self.locator_finder_by_xpath(track_all_position)
            track_all_position_sitem.click()
            time.sleep(1)

            search_fields = "//*[text()='Search Field']"
            search_fields_sitem = self.locator_finder_by_xpath(search_fields)
            search_fields_sitem.click()
            time.sleep(1)

            if self.current_package_version() > semver.VersionInfo.parse("3.11.0"):
                self.locator_finder_by_xpath("//*[text()='Name']").click()
            else:
                self.locator_finder_by_xpath("//*[text()='Name']").click()
            action.send_keys('Inverted').perform()
            time.sleep(1)

            general_writebuffer_idle = "//*[text()='Writebuffer Idle']"
            general_writebuffer_idle_sitem = self.locator_finder_by_xpath(general_writebuffer_idle)
            general_writebuffer_idle_sitem.click()
            action.key_down(Keys.CONTROL).\
                send_keys("a").\
                key_up(Keys.CONTROL).send_keys(Keys.BACKSPACE).\
                send_keys(100).perform()
            time.sleep(1)

            general_writebuffer_active = "//*[text()='Writebuffer Active']"
            general_writebuffer_active_sitem = self.locator_finder_by_xpath(general_writebuffer_active)
            general_writebuffer_active_sitem.click()
            action.key_down(Keys.CONTROL). \
                send_keys("a"). \
                key_up(Keys.CONTROL).send_keys(Keys.BACKSPACE). \
                send_keys(1).perform()
            time.sleep(1)

            general_writebuffer_size_max = "//*[text()='Writebuffer Size Max']"
            general_writebuffer_size_max_sitem = self.locator_finder_by_xpath(
                general_writebuffer_size_max)
            general_writebuffer_size_max_sitem.click()
            action.key_down(Keys.CONTROL). \
                send_keys("a"). \
                key_up(Keys.CONTROL).send_keys(Keys.BACKSPACE). \
                send_keys(33554438).perform()
            time.sleep(1)

            general_cleanup_startup_steps = "//*[text()='Cleanup Interval Step']"
            general_cleanup_startup_steps_sitem = self.locator_finder_by_xpath(
                general_cleanup_startup_steps)
            general_cleanup_startup_steps_sitem.click()
            action.key_down(Keys.CONTROL). \
                send_keys("a"). \
                key_up(Keys.CONTROL).send_keys(Keys.BACKSPACE). \
                send_keys(3).perform()
            time.sleep(1)

            general_commit_interval = "//*[text()='Commit Interval (msec)']"
            general_commit_interval_sitem = self.locator_finder_by_xpath(
                general_commit_interval)
            general_commit_interval_sitem.click()
            action.key_down(Keys.CONTROL). \
                send_keys("a"). \
                key_up(Keys.CONTROL).send_keys(Keys.BACKSPACE). \
                send_keys(1010).perform()
            time.sleep(1)

            general_consolidation_interval = "//*[text()='Consolidation Interval (msec)']"
            general_consolidation_interval_sitem = self.locator_finder_by_xpath(
                general_consolidation_interval)
            general_consolidation_interval_sitem.click()
            action.key_down(Keys.CONTROL). \
                send_keys("a"). \
                key_up(Keys.CONTROL).send_keys(Keys.BACKSPACE). \
                send_keys(1010).perform()
            time.sleep(1)

            primary_sort = "//*[text()='Primary Sort']"
            primary_sort_sitem = self.locator_finder_by_xpath(
                primary_sort)
            primary_sort_sitem.click()
            time.sleep(1)

            primary_sort_field = "//*[text()='Field']"
            primary_sort_field_sitem = self.locator_finder_by_xpath(
                primary_sort_field)
            primary_sort_field_sitem.click()
            action.key_down(Keys.CONTROL). \
                send_keys("a"). \
                key_up(Keys.CONTROL).send_keys(Keys.BACKSPACE). \
                send_keys("name").perform()
            time.sleep(1)

            stored_value = "//*[text()='Stored Values']"
            stored_value_sitem = self.locator_finder_by_xpath(
                stored_value)
            stored_value_sitem.click()
            time.sleep(1)

            action.key_down(Keys.CONTROL). \
                send_keys("a"). \
                key_up(Keys.CONTROL).send_keys(Keys.BACKSPACE). \
                send_keys("age").perform()
            time.sleep(1)

            consolidation_policy = "//*[text()='Consolidation Policy']"
            consolidation_policy_sitem = self.locator_finder_by_xpath(
                consolidation_policy)
            consolidation_policy_sitem.click()
            time.sleep(1)

            segment_min = "//*[text()='Segments Min']"
            segment_min_sitem = self.locator_finder_by_xpath(
                segment_min)
            segment_min_sitem.click()
            action.key_down(Keys.CONTROL). \
                send_keys("a"). \
                key_up(Keys.CONTROL).send_keys(Keys.BACKSPACE). \
                send_keys(2).perform()
            time.sleep(1)

            segment_max = "//*[text()='Segments Max']"
            segment_max_sitem = self.locator_finder_by_xpath(
                segment_max)
            segment_max_sitem.click()
            action.key_down(Keys.CONTROL). \
                send_keys("a"). \
                key_up(Keys.CONTROL).send_keys(Keys.BACKSPACE). \
                send_keys(12).perform()
            time.sleep(1)

            segment_byte_max = "//*[text()='Segments Bytes Max']"
            segment_byte_max_sitem = self.locator_finder_by_xpath(
                segment_byte_max)
            segment_byte_max_sitem.click()
            action.key_down(Keys.CONTROL). \
                send_keys("a"). \
                key_up(Keys.CONTROL).send_keys(Keys.BACKSPACE). \
                send_keys(5368709120).perform()
            time.sleep(1)

            segment_bytes_floor = "//*[text()='Segments Bytes Floor']"
            segment_bytes_floor_sitem = self.locator_finder_by_xpath(
                segment_bytes_floor)
            segment_bytes_floor_sitem.click()
            action.key_down(Keys.CONTROL). \
                send_keys("a"). \
                key_up(Keys.CONTROL).send_keys(Keys.BACKSPACE). \
                send_keys(5368709128).perform()
            time.sleep(1)

        elif index_name == 'MDI':
            try:
                self.navbar_goto("collections")
                self.webdriver.refresh()
                self.wait_for_ajax()
                self.tprint("Selecting computed values collections. \n")
                col = "(//a[normalize-space()='ComputedValueCol'])[1]"
                self.locator_finder_by_xpath(col).click()
                time.sleep(1)

                self.select_index_menu()

                create_new_index_btn_sitem = self.locator_finder_by_xpath(add_index)
                create_new_index_btn_sitem.click()
                time.sleep(2)

                self.select_desired_index_from_the_list("MDI Index")

                mdi_field = "/html//input[@id='fields']"
                mdi_field = self.locator_finder_by_xpath(mdi_field)
                mdi_field.click()
                mdi_field.send_keys('x,y')

                # selecting MDI index's name
                mdi_name = "/html//input[@id='name']"
                mdi_name_sitem = self.locator_finder_by_xpath(mdi_name)
                mdi_name_sitem.click()
                mdi_name_sitem.send_keys(index_name)
            except Exception as e:
                self.tprint(e)
                # retry
                self.webdriver.refresh()
                self.create_index('MDI')
            finally:
                pass
        else:
            try:
                self.navbar_goto("collections")
                self.tprint("Selecting computed values collections. \n")
                col = '//*[@id="collection_ComputedValueCol"]/div/h5'
                self.locator_finder_by_xpath(col).click()
                time.sleep(1)

                self.select_index_menu()

                create_new_index_btn_sitem = self.locator_finder_by_xpath(add_index)
                create_new_index_btn_sitem.click()
                time.sleep(2)

                self.tprint('ZKD Index (EXPERIMENTAL)')
                zkd_field = "/html//input[@id='fields']"
                zkd_field = self.locator_finder_by_xpath(zkd_field)
                zkd_field.click()
                zkd_field.send_keys('x,y')

                # selecting ZKD index's name
                zkd_name = "/html//input[@id='name']"
                zkd_name_sitem = self.locator_finder_by_xpath(zkd_name)
                zkd_name_sitem.click()
                zkd_name_sitem.send_keys(index_name)
            except Exception as e:
                self.tprint(e)
                # retry
                self.webdriver.refresh()
                self.create_index('ZKD')
            finally:
                pass

        # create the index
        create_btn = "//*[text()='Create']"
        create_btn_sitem = self.locator_finder_by_xpath(create_btn)
        create_btn_sitem.click()
        time.sleep(2)


    def create_new_index(self, index_name, value, is_cluster, check=False):
        """ create a new Index """
        self.tprint(f"Creating {index_name} index started \n")
        add_index = "/html//i[@id='addIndex']"
        self.locator_finder_by_xpath(add_index).click()
        time.sleep(2)

        self.tprint(f"selecting {index_name} from the list\n")
        self.locator_finder_by_select(self.select_index_type_id, value)

        if index_name == "Persistent":
            self.select_persistent_fields_id = self.locator_finder_by_hover_item_id(self.select_persistent_fields_id)
            time.sleep(1)
            self.select_persistent_fields_id.send_keys("pfields").perform()
            self.select_persistent_name_id = self.locator_finder_by_hover_item_id(self.select_persistent_name_id)
            self.select_persistent_fields_id.send_keys("Persistent").perform()
            time.sleep(1)

            if not is_cluster:
                self.select_persistent_unique_id = self.locator_finder_by_hover_item_id(
                    self.select_persistent_unique_id
                )

            self.select_persistent_sparse_id = self.locator_finder_by_hover_item_id(self.select_persistent_sparse_id)
            self.select_persistent_duplicate_id = self.locator_finder_by_hover_item_id(
                self.select_persistent_duplicate_id
            )
            self.select_persistent_background_id = self.locator_finder_by_hover_item_id(self.select_persistent_background_id)
            time.sleep(1)

        elif index_name == "Geo":
            self.select_geo_fields_id = self.locator_finder_by_hover_item_id(self.select_geo_fields_id)
            self.select_geo_fields_id.send_keys("gfields").perform()
            time.sleep(1)
            self.select_geo_name_id = self.locator_finder_by_hover_item_id(self.select_geo_name_id)
            self.select_geo_name_id.send_keys("Geo").perform()
            time.sleep(1)
            self.select_geo_json_id = self.locator_finder_by_hover_item_id(self.select_geo_json_id)
            self.select_geo_background_id = self.locator_finder_by_hover_item_id(self.select_geo_background_id)
            time.sleep(1)
            self.wait_for_ajax()

        elif index_name == "Fulltext":
            self.select_fulltext_field_id = self.locator_finder_by_hover_item_id(self.select_fulltext_field_id)
            self.select_fulltext_field_id.send_keys("ffields").perform()
            time.sleep(1)
            self.select_fulltext_name_id = self.locator_finder_by_hover_item_id(self.select_fulltext_name_id)
            self.select_fulltext_name_id.send_keys("Fulltext").perform()
            time.sleep(1)
            self.select_fulltext_length_id = self.locator_finder_by_hover_item_id(self.select_fulltext_length_id)
            self.select_fulltext_length_id.send_keys(100)
            self.select_fulltext_background_id = self.locator_finder_by_hover_item_id(
                self.select_fulltext_background_id
            )
            time.sleep(1)
            self.wait_for_ajax()

        elif index_name == "TTL":
            self.select_ttl_field_id = self.locator_finder_by_hover_item_id(self.select_ttl_field_id)
            self.select_ttl_field_id.send_keys("tfields").perform()
            time.sleep(1)
            self.select_ttl_name_id = self.locator_finder_by_hover_item_id(self.select_ttl_name_id)
            self.select_ttl_name_id.send_keys("TTL").perform()
            time.sleep(1)
            self.select_ttl_expiry_id = self.locator_finder_by_hover_item_id(self.select_ttl_expiry_id)
            self.select_ttl_expiry_id.send_keys(1000)
            self.select_ttl_background_id = self.locator_finder_by_hover_item_id(self.select_ttl_background_id)
            time.sleep(1)
            self.wait_for_ajax()

        # experimental feature
        elif index_name == 'ZKD':
            if check:
                self.navbar_goto("collections")
                self.tprint("Selecting computed values collections. \n")
                col = '//*[@id="collection_ComputedValueCol"]/div/h5'
                self.locator_finder_by_xpath(col).click()
                self.select_index_menu()

                self.tprint(f"Creating {index_name} index started \n")
                self.locator_finder_by_xpath(add_index).click()
                time.sleep(2)

                self.tprint(f"selecting {index_name} from the list\n")
                self.locator_finder_by_select(self.select_index_type_id, 5)

                time.sleep(1)

                select_zkd_field_sitem = self.locator_finder_by_id('newZkdFields')
                select_zkd_field_sitem.click()
                select_zkd_field_sitem.clear()
                select_zkd_field_sitem.send_keys('x,y')
                time.sleep(1)
            else:
                select_zkd_field_sitem = self.locator_finder_by_id('newZkdFields')
                select_zkd_field_sitem.click()
                select_zkd_field_sitem.clear()
                select_zkd_field_sitem.send_keys('zkdfileds')
                time.sleep(1)

            select_zkd_name_sitem = self.locator_finder_by_id('newZkdName')
            select_zkd_name_sitem.click()
            select_zkd_name_sitem.clear()
            select_zkd_name_sitem.send_keys('ZKD')
            time.sleep(1)
        elif index_name == 'MDI':
            if check:
                self.navbar_goto("collections")
                self.tprint("Selecting computed values collections. \n")
                col = '//*[@id="collection_ComputedValueCol"]/div/h5'
                self.locator_finder_by_xpath(col).click()
                self.select_index_menu()

                self.tprint(f"Creating {index_name} index started \n")
                self.locator_finder_by_xpath(add_index).click()
                time.sleep(2)

                self.tprint(f"selecting {index_name} from the list\n")
                self.locator_finder_by_select(self.select_index_type_id, 5)

                time.sleep(1)

                select_mdi_field_sitem = self.locator_finder_by_id('newMdiFields')
                select_mdi_field_sitem.click()
                select_mdi_field_sitem.clear()
                select_mdi_field_sitem.send_keys('x,y')
                time.sleep(1)
            else:
                select_mdi_field_sitem = self.locator_finder_by_id('newMdiFields')
                select_mdi_field_sitem.click()
                select_mdi_field_sitem.clear()
                select_mdi_field_sitem.send_keys('mdifileds')
                time.sleep(1)

            select_mdi_name_sitem = self.locator_finder_by_id('newMdiName')
            select_mdi_name_sitem.click()
            select_mdi_name_sitem.clear()
            select_mdi_name_sitem.send_keys('MDI')
            time.sleep(1)

        select_create_index_btn_id = "createIndex"
        self.locator_finder_by_id(select_create_index_btn_id).click()
        time.sleep(10)
        self.webdriver.refresh()

        if check:
            self.navbar_goto("collections")
            self.select_collection("TestDoc")
            self.select_index_menu()

        self.tprint(f"Creating {index_name} index completed \n")

    def delete_index_311(self, check=False):
        """this method will delete all the indexes one by one for =<3.11.99"""
        try:
            delete = '//*[@id="collectionEditIndexTable"]/tbody/tr[2]/th[10]/span'
            if check:
                select_index_for_delete_sitem = self.locator_finder_by_xpath(delete)
            else:
                select_index_for_delete_sitem = \
                    self.locator_finder_by_xpath(self.select_index_for_delete_id)
            select_index_for_delete_sitem.click()
            time.sleep(2)
            select_index_confirm_delete_sitem = \
                self.locator_finder_by_id(self.select_index_confirm_delete)
            select_index_confirm_delete_sitem.click()
            self.webdriver.refresh()
        except TimeoutException as e:
            self.tprint(f'Something went wrong {e}\n')

    def delete_index_312(self, _):
        """this method will delete all the indexes one by one for >= 3.12.0"""
        try:
            self.webdriver.refresh()
            self.wait_for_ajax()

            if self.current_package_version() > semver.VersionInfo.parse("3.11.99"):
                delete = "//button[@aria-label='Delete Index'][1]"
            else:
                delete = "(//*[name()='svg'][@class='chakra-icon css-onkibi'])[2]"

            delete_sitem = self.locator_finder_by_xpath(delete)
            delete_sitem.click()
            time.sleep(1)
            self.wait_for_ajax()

            delete_confirmation = "(//button[normalize-space()='Delete'])[1]"
            delete_confirmation_sitem = self.locator_finder_by_xpath(delete_confirmation)
            delete_confirmation_sitem.click()
            time.sleep(1)
            self.wait_for_ajax()

            if self.current_package_version() > semver.VersionInfo.parse("3.11.99"):
                delete_final_confirmation = '(//button[text()="Delete"])[2]'
                delete_final_confirmation_sitem = self.locator_finder_by_xpath(delete_final_confirmation)
                delete_final_confirmation_sitem.click()
                time.sleep(1)
                self.wait_for_ajax()

        except TimeoutException as e:
            try:
                self.tprint(f"Trying again to delete the inverted index \n{e}")
                self.webdriver.refresh()
                self.wait_for_ajax()

                delete = "(//*[name()='svg'][@class='chakra-icon css-onkibi'])[3]"
                delete_sitem = self.locator_finder_by_xpath(delete)
                delete_sitem.click()
                time.sleep(1)
                delete_confirmation = "(//button[normalize-space()='Delete'])[1]"
                delete_confirmation_sitem = self.locator_finder_by_xpath(delete_confirmation)
                delete_confirmation_sitem.click()

            except BaseException as ex:
                self.tprint(f'Something went wrong {ex}\n')
                self.navbar_goto("collections")

    def select_info_tab(self):
        """Selecting info tab from the collection submenu"""
        self.click_submenu_entry("Info")
        time.sleep(2)
        self.wait_for_ajax()

    def select_schema_tab(self):
        """Selecting Schema tab from the collection submenu"""
        if self.current_package_version() >= semver.VersionInfo.parse("3.8.0"):
            if self.current_package_version() >= semver.VersionInfo.parse("3.9.100"):
                schema = '//*[@id="subNavigationBar"]/ul[2]/li[6]/a'
                select_schema_tab_sitem = self.locator_finder_by_xpath(schema, benchmark=True)
            else:
                select_schema_tab_sitem = self.locator_finder_by_xpath(self.select_schema_tab_id, benchmark=True)
            select_schema_tab_sitem.click()
            time.sleep(2)
        else:
            self.tprint('Schema check not supported for the current package version \n')
        self.wait_for_ajax()

    def select_settings_tab(self, is_cluster, check=False):
        """Selecting settings tab from the collection submenu"""
        self.click_submenu_entry("Settings")
        # selecting Settings tab can occasionally lead to never-ending content loading - code below prevents it
        time.sleep(5)
        self.webdriver.refresh()
        self.wait_for_ajax()
        time.sleep(15)
        if check:
            if not is_cluster:
                select_settings_name_textbox_sitem = self.locator_finder_by_xpath(self.select_settings_name_textbox_id)
                select_settings_name_textbox_sitem.click()
                select_settings_name_textbox_sitem.clear()
                select_settings_name_textbox_sitem.send_keys("testDocRenamed")
                self.locator_finder_by_select(self.select_settings_wait_type_id, 0)
            select_new_settings_save_btn_sitem = None
            try:
                select_new_settings_save_btn_sitem = self.locator_finder_by_id(self.select_newer_settings_save_btn_id)
                if select_new_settings_save_btn_sitem.text != "Save":
                    select_new_settings_save_btn_sitem = self.locator_finder_by_id(self.select_new_settings_save_btn_id)
            except TimeoutException:
                select_new_settings_save_btn_sitem = self.locator_finder_by_id(self.select_new_settings_save_btn_id)

            select_new_settings_save_btn_sitem.click()
            time.sleep(2)
            self.tprint("Loading Index into memory\n")
            select_load_index_into_memory_sitem = self.locator_finder_by_xpath(self.select_load_index_into_memory_id)
            select_load_index_into_memory_sitem.click()
            time.sleep(2)
        # self.wait_for_ajax()

    def ace_set_value_x(self, locator, query, check=False):
        """take a string and adjacent locator argument of ace-editor and execute the query"""
        # to unify ace_locator class attribute has been used
        ace_locator = self.locator_finder_by_class(locator)
        # Set x and y offset positions of adjacent element
        x_offset = 100
        y_offset = 100
        # Performs mouse move action onto the element
        actions = ActionChains(self.webdriver).move_to_element_with_offset(ace_locator, x_offset, y_offset)
        actions.click()
        actions.key_down(Keys.CONTROL).send_keys('a').send_keys(Keys.BACKSPACE).key_up(Keys.CONTROL)
        time.sleep(1)
        actions.send_keys(f'{query}')
        actions.perform()
        time.sleep(1)

        if check:
            self.tprint("Saving current computed value")
            save_computed_value = 'saveComputedValuesButton'
            save_computed_value_sitem = self.locator_finder_by_id(save_computed_value)
            save_computed_value_sitem.click()
            time.sleep(2)
            self.webdriver.refresh()
            time.sleep(2)
        else:
            create_btn = 'modalButton1'
            self.locator_finder_by_id(create_btn).click()
            time.sleep(1)

    def select_computed_value_col(self):
        """this method will select ComputedValueCol"""
        self.wait_for_ajax()
        col = "//*[text()='ComputedValueCol']"
        self.locator_finder_by_xpath(col).click()
        time.sleep(1)

    def navigate_to_col_content_tab(self):
        """ this method will take to collection content tab"""
        content = "//div[@id='subNavigationBar']/ul[2]//a[.='Content']"
        content_sitem = self.locator_finder_by_xpath(content)
        content_sitem.click()
        time.sleep(1)

    def test_computed_values(self):
        """ Testing computed value feature for v3.10.x"""
        self.navbar_goto("collections")
        self.webdriver.refresh()
        self.wait_for_ajax()
        time.sleep(2)
        self.tprint("Selecting computed values collections. \n")
        col = "//*[text()='ComputedValueCol']"
        self.locator_finder_by_xpath(col).click()
        time.sleep(1)

        self.tprint("Selecting computed value tab \n")
        computed = "//*[contains(text(),'Computed Values')]"
        self.locator_finder_by_xpath(computed).click()
        time.sleep(1)

        python_query = [
            {"name": "dateCreatedHumanReadable",
             "expression": "RETURN DATE_ISO8601(DATE_NOW())",
             "overwrite": True},
            {"name": "dateCreatedForIndexing",
             "expression": "RETURN DATE_NOW()",
             "overwrite": True},
            {"name": "FullName",
             "expression": "RETURN MERGE(@doc.name,"
                           " {full: CONCAT(@doc.name.first, ' ', @doc.name.last)})",
             "overwrite": True,
             "computeOn": ["insert", "update", "replace"]}]
        compute_query = json.dumps(python_query)
        # button near to ace editor
        warning = 'button-warning'
        self.ace_set_value_x(warning, compute_query, True)

        self.tprint('go back to collection tab')
        # Define the maximum number of retries
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                self.webdriver.refresh()
                self.wait_for_ajax()
                # Navigate to collections page
                self.navbar_goto("collections")
                self.wait_for_ajax()

                # Attempt to select computed value column
                self.select_computed_value_col()

                # If successful, break out of the loop
                break
            except Exception as e:
                # If an error occurs, print the error message
                self.tprint(f"Error occurred while selecting computed value column: {e}")

                # Increment retry count
                retry_count += 1

                # If maximum retries reached, raise an error
                if retry_count == max_retries:
                    raise RuntimeError("Failed to select computed value column after multiple retries") from e

                # Wait for a few seconds before retrying
                time.sleep(3)

        self.navigate_to_col_content_tab()

        # self.tprint('Select add new document to collection button')
        add = '//*[@id="addDocumentButton"]/span/i'
        add_sitem = self.locator_finder_by_xpath(add)
        add_sitem.click()

        # self.tprint('inserting data\n')
        insert_data = "jsoneditor-format"
        col_query = {"name": {"first": "Sam",
                              "last": "Smith"},
                     "address": "Hans-Sachs-Str",
                     "x": 12.9,
                     "y": -284.0}
        insert_query = json.dumps(col_query)
        self.ace_set_value_x(insert_data, insert_query)
        self.navbar_goto('queries')
        time.sleep(1)

        self.tprint('select query execution area\n')
        self.select_query_execution_area()
        self.tprint('sending query to the area\n')
        self.send_key_action('FOR user IN ComputedValueCol RETURN user')
        self.tprint('execute the query\n')
        self.query_execution_btn()
        self.scroll()

        self.tprint('Checking that dateCreatedHumanReadable computed value as been created\n')
        computed_value = "//*[text()='dateCreatedHumanReadable']"
        computed_value_sitem = self.locator_finder_by_xpath(computed_value).text
        time.sleep(1)
        computed_value = 'dateCreatedHumanReadable'
        try:
            assert computed_value == computed_value_sitem, \
                f"Expected page title {computed_value} but got {computed_value_sitem}"
        except AssertionError:
            self.tprint(f'Assertion Error occurred! for {computed_value}\n')

        self.tprint('Checking that FullName computed value as been created\n')
        computed_full_name = "//*[text()='FullName']"
        computed_full_name_sitem = self.locator_finder_by_xpath(computed_full_name).text
        time.sleep(1)
        full_name_value = 'FullName'
        try:
            assert full_name_value == computed_full_name_sitem, \
                f"Expected page title {computed_value} but got {computed_full_name_sitem}"
        except AssertionError:
            self.tprint(f'Assertion Error occurred! for {computed_value}\n')

        self.tprint('Checking that dateCreatedForIndexing computed value as been created\n')
        computed_index_value = "//*[text()='dateCreatedForIndexing']"
        computed_index_value_sitem = self.locator_finder_by_xpath(computed_index_value).text
        index_value = 'dateCreatedForIndexing'
        time.sleep(1)
        try:
            assert index_value == computed_index_value_sitem, \
                f"Expected page title {index_value} but got {computed_index_value_sitem}"
        except AssertionError:
            self.tprint(f'Assertion Error occurred! for {index_value}\n')

        # go back to collection page
        self.navbar_goto("collections")

    def select_settings_unload_btn(self):
        """Loading and Unloading collection"""
        select_settings_unload_btn_sitem = self.locator_finder_by_id(self.select_settings_unload_btn_id)
        select_settings_unload_btn_sitem.click()
        time.sleep(2)
        self.wait_for_ajax()

    def select_truncate_btn(self):
        """Loading and Unloading collection"""
        select_truncate_btn_sitem = self.locator_finder_by_id(self.select_truncate_btn_id)
        select_truncate_btn_sitem.click()
        time.sleep(1)
        select_truncate_confirm_btn_sitem = self.locator_finder_by_xpath(self.select_truncate_confirm_btn_id)
        select_truncate_confirm_btn_sitem.click()
        time.sleep(2)
        self.wait_for_ajax()

    def select_delete_collection(self, expec_fail=False):
        """Deleting Collection from settings tab"""
        self.wait_for_ajax()
        time.sleep(2)
        delete_collection_sitem = self.locator_finder_by_xpath(self.delete_collection_id, expec_fail=expec_fail)
        delete_collection_sitem.click()
        time.sleep(2)
        delete_collection_confirm_sitem = self.locator_finder_by_xpath(self.delete_collection_confirm_id)
        delete_collection_confirm_sitem.click()
        self.wait_for_ajax()
        time.sleep(2)

    def select_edge_collection_upload(self):
        """selecting Edge collection for data uploading"""
        self.select_collection("TestEdge")

    def select_edge_collection(self):
        """selecting TestEdge Collection"""
        self.select_collection("TestEdge")
        self.click_submenu_entry("Settings")

    def select_test_doc_collection(self):
        """selecting TestEdge Collection"""
        self.select_collection("Test")
        self.click_submenu_entry("Settings")

    def select_collection(self, collection_name):
        """ select a collection """
        selector = """//div[contains(@class, 'tile')][@id='collection_%s']""" % collection_name
        self.locator_finder_by_xpath(selector).click()

    def select_doc_collection(self):
        """selecting testDoc collection"""
        self.tprint("Selecting TestDoc Collection \n")
        try:
            if self.current_package_version() >= semver.VersionInfo.parse("3.11.99"):
                test_doc_col = "(//a[normalize-space()='TestDoc'])[1]"
            else:
                test_doc_col = '//*[@id="collection_TestDoc"]/div/h5'

            select_test_doc_collection_sitem = self.locator_finder_by_xpath(test_doc_col)
            select_test_doc_collection_sitem.click()
            time.sleep(1)
        except BaseException as e:
            self.tprint(f'trying again in case of found statle element {e}\n')
            self.webdriver.refresh()
            self.select_doc_collection()

    def create_sample_collection(self, test_name):
        """selecting collection tab"""
        try:
            # Clicking on create new collection box
            create_collection_sitem = self.locator_finder_by_id(self.select_create_collection_id)
            create_collection_sitem.click()
            time.sleep(2)

            # Providing new collection name
            collection_name_sitem = self.locator_finder_by_id(self.select_new_collection_name_id)
            collection_name_sitem.click()
            collection_name_sitem.send_keys("testDoc")

            # creating collection by tapping on save button
            save_sitem = self.locator_finder_by_id("modalButton1")
            save_sitem.click()

            try:
                notification_sitem = self.locator_finder_by_css_selectors("noty_body")
                time.sleep(1)
                expected_text = 'Collection: Collection "testDoc" successfully created.'
                assert (
                    notification_sitem.text == expected_text
                ), f"Expected text{expected_text} but got {notification_sitem.text}"
            except TimeoutException:
                self.tprint("FAIL: Unexpected error occurred!")

        except TimeoutException as ex:
            if test_name == "access":
                self.tprint("Collection creation failed, which is expected")
            if test_name == "read/write":
                raise Exception("FAIL: Unexpected error occurred!") from ex

    def delete_collection(self, collection_name, collection_locator, is_cluster):
        """This method deletes the collection identified by its name"""
        self.tprint(f"Deleting {collection_name} collection started \n")
        self.navbar_goto("collections")
        self.webdriver.refresh() # this is where we can get occasionally logged out
        self.wait_for_ajax()

        # changing the default collection locator according to the >= v3.12.x
        if self.current_package_version() >= semver.VersionInfo.parse("3.11.100"):
            if collection_name == "TestDoc":
                collection_locator = "(//a[normalize-space()='TestDoc'])[1]"
            elif collection_name == "TestEdge":
                collection_locator = "(//a[normalize-space()='TestEdge'])[1]"
            elif collection_name == "Test":
                collection_locator = "(//a[normalize-space()='Test'])[1]"
            elif collection_name == "TestDocRenamed":
                collection_locator = "(//a[normalize-space()='TestDocRenamed'])[1]"
            elif collection_name == "ComputedValueCol":
                collection_locator = "(//a[normalize-space()='ComputedValueCol'])[1]"

        try:
            self.locator_finder_by_xpath(collection_locator).click()
            # we don't care about the cluster specific things:
            self.select_settings_tab(is_cluster)
            self.select_delete_collection()

            self.tprint(f"Deleting {collection_name} collection Completed \n")
            # self.webdriver.refresh()
        except (TimeoutException, AttributeError):
            self.tprint("TimeoutException occurred! \n")
            self.tprint("Info: Collection has already been deleted or never created. \n")
        except NoSuchElementException:
            self.tprint('Element not found, which might be happen due to force cleanup.')
        except Exception as ex:
            traceback.print_exc()
            raise Exception("Critical Error occurred and need manual inspection!! \n") from ex
        # this is to 'stabilise' the FE app after collection deletion (otherwise we may get logged out)
        self.navbar_goto("users")
        self.webdriver.refresh()
        self.wait_for_ajax()
        time.sleep(20)
