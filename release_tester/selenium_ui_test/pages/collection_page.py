import time
from selenium_ui_test.pages.navbar import NavigationBarPage
from selenium.common.exceptions import ElementNotInteractableException, TimeoutException
import traceback

# can't circumvent long lines.. nAttr nLines
# pylint: disable=C0301 disable=R0902 disable=R0915 disable=R0904


class CollectionPage(NavigationBarPage):
    """Collection page class"""

    def __init__(self, driver):
        """class initialization"""
        super().__init__(driver)
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
            "//div[@id='collectionsDropdown']" "/ul[1]/li[2]/a/label[@class='checkbox checkboxLabel']"
        )
        self.display_document_collection_id = (
            "//div[@id='collectionsDropdown']" "/ul[1]/li[3]/a/label[@class='checkbox checkboxLabel']"
        )
        self.display_edge_collection_id = (
            "//div[@id='collectionsDropdown']" "/ul[1]/li[4]/a/label[@class='checkbox checkboxLabel']"
        )
        self.select_status_loaded_id = (
            "//div[@id='collectionsDropdown']" "/ul[2]/li[2]/a[@href='#']/label[@class='checkbox checkboxLabel']"
        )
        self.select_status_unloaded_id = (
            "//div[@id='collectionsDropdown']" "/ul[2]/li[3]/a[@href='#']/label[@class='checkbox checkboxLabel']"
        )
        self.sort_by_name_id = "sortName"
        self.sort_by_type_id = "sortType"
        self.sort_descending_id = "sortOrder"

        self.select_doc_collection_id = "//div[@id='collection_TestDoc']//h5[@class='collectionName']"

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
        self.select_index_menu_id = "//*[@id='subNavigationBarPage']/ul[2]/li[2]/a"
        self.create_new_index_btn_id = "addIndex"
        self.select_index_type_id = "newIndexType"

        self.select_geo_fields_id = "newGeoFields"
        self.select_geo_name_id = "newGeoName"
        self.select_geo_json_id = "newGeoJson"
        self.select_geo_background_id = "newGeoBackground"

        self.select_create_index_btn_id = "createIndex"

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

        self.select_index_for_delete_id = (
            "/html//table[@id='collectionEditIndexTable']" "/tbody/tr[2]/th[9]/span[@title='Delete index']"
        )
        self.select_index_confirm_delete = "indexConfirmDelete"
        self.select_info_tab_id = "//*[@id='subNavigationBarPage']/ul[2]/li[3]/a"

        self.select_schema_tab_id = "//*[@id='subNavigationBarPage']/ul[2]/li[5]/a"

        self.select_settings_tab_id = "//*[@id='subNavigationBarPage']/ul[2]/li[4]/a"
        self.select_settings_name_textbox_id = "change-collection-name"
        self.select_settings_wait_type_id = "change-collection-sync"
        self.select_newer_settings_save_btn_id = "modalButton4"
        self.select_new_settings_save_btn_id = "modalButton5"

        self.select_load_index_into_memory_id = "//*[@id='modalButton2']"
        self.select_settings_unload_btn_id = "//*[@id='modalButton3']"
        self.select_truncate_btn_id = "//*[@id='modalButton1']"
        self.select_truncate_confirm_btn_id = "//*[@id='modal-confirm-delete']"
        self.delete_collection_id = "//*[@id='modalButton0']"
        self.delete_collection_confirm_id = "//*[@id='modal-confirm-delete']"

        self.select_edge_collection_upload_id = "//*[@id='collection_TestEdge']/div/h5"
        self.select_edge_collection_id = "//*[@id='collection_TestEdge']/div/h5"
        self.select_edge_settings_id = "//*[@id='subNavigationBarPage']/ul[2]/li[4]/a"
        self.select_test_doc_settings_id = "//*[@id='subNavigationBarPage']/ul[2]/li[4]/a"

        self.select_test_doc_collection_id = "//div[@id='collection_Test']//h5[@class='collectionName']"
        self.select_collection_search_id = "//*[@id='searchInput']"

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

    def select_collection_page(self):
        """selecting collection tab"""
        select_collection_page_sitem = self.locator_finder_by_id(self.select_collection_page_id)
        select_collection_page_sitem.click()
        time.sleep(1)

    def select_create_collection(self):
        """Clicking on create new collection box"""
        select_create_collection_sitem = self.locator_finder_by_id(self.select_create_collection_id)
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
        rf = "new-replication-factor"
        rf_sitem = self.locator_finder_by_id(rf)
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

    def checking_search_options(self, search):
        """Checking search functionality"""
        select_collection_search_sitem = self.locator_finder_by_xpath(self.select_collection_search_id)
        select_collection_search_sitem.click()
        select_collection_search_sitem.clear()
        select_collection_search_sitem.send_keys(search)
        time.sleep(2)

    def select_collection_settings(self):
        """selecting collection settings icon"""
        select_collection_settings_sitem = self.locator_finder_by_id(self.select_collection_settings_id)
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
        select_status_loaded_sitem = self.locator_finder_by_xpath(self.select_status_loaded_id)
        select_status_loaded_sitem.click()
        time.sleep(2)

    def select_status_unloaded(self):
        """Displaying status unloaded collection"""
        select_status_unloaded_sitem = self.locator_finder_by_xpath(self.select_status_unloaded_id)
        select_status_unloaded_sitem.click()
        time.sleep(2)

    def sort_by_type(self):
        """Sorting collection by type"""
        sort_by_type_sitem = self.locator_finder_by_idx(self.sort_by_type_id, 30)
        sort_by_type_sitem = sort_by_type_sitem.find_element_by_xpath("./..")
        while True:
            try:
                sort_by_type_sitem.click()
                break
            except ElementNotInteractableException:
                time.sleep(1)

    def sort_by_name(self):
        """Sorting collection by name"""
        sort_by_name_sitem = self.locator_finder_by_idx(self.sort_by_name_id)
        sort_by_name_sitem = sort_by_name_sitem.find_element_by_xpath("./..")
        while True:
            try:
                sort_by_name_sitem.click()
                break
            except ElementNotInteractableException:
                time.sleep(1)

    def sort_descending(self):
        """Sorting collection by descending"""
        sort_descending_sitem = self.locator_finder_by_idx(self.sort_descending_id)
        sort_descending_sitem = sort_descending_sitem.find_element_by_xpath("./..")
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
        getting_total_row_count_sitem = self.locator_finder_by_xpath(self.getting_total_row_count_id, 20)
        return getting_total_row_count_sitem.text

    def download_doc_as_json(self):
        """Exporting documents as JSON file from the collection"""
        if self.webdriver.name == "chrome":  # this will check browser name
            print("Download has been disabled for the Chrome browser \n")
        else:
            select_export_doc_as_jason_sitem = self.locator_finder_by_xpath(self.select_export_doc_as_jason_id)
            select_export_doc_as_jason_sitem.click()
            time.sleep(1)
            select_export_doc_confirm_btn_sitem = self.locator_finder_by_id(self.select_export_doc_confirm_btn_id)
            select_export_doc_confirm_btn_sitem.click()
            time.sleep(2)
            # super().clear_download_bar()

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
        # print(string[8:])
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
        self.click_submenu_entry("Indexes")

    # def create_new_index_btn(self):
    #     """Selecting index menu from collection"""
    #     create_new_index_btn_sitem = self.locator_finder_by_id(self.create_new_index_btn_id)
    #     create_new_index_btn_sitem.click()
    #     time.sleep(2)
    #     self.wait_for_ajax()

    # def select_index_type(self, value):
    #     """Selecting type of index here: Geo, Persistent, Fulltext or TTL"""
    #     self.select_value(self.select_index_type_id, value)

    # def select_create_index_btn(self):
    #     """Selecting index menu from collection"""
    #     select_create_index_btn_sitem = self.locator_finder_by_id(self.select_create_index_btn_id)
    #     select_create_index_btn_sitem.click()
    #     time.sleep(2)
    #     self.wait_for_ajax()

    # def creating_geo_index(self):
    #     """Filling up all the information for geo index"""
    #     select_geo_fields_sitem = self.locator_finder_by_hover_item_id(self.select_geo_fields_id)
    #     select_geo_fields_sitem.send_keys("gfields").perform()
    #     select_geo_name_sitem = self.locator_finder_by_hover_item_id(self.select_geo_name_id)
    #     select_geo_name_sitem.send_keys("gname").perform()
    #     self.locator_finder_by_hover_item_id(self.select_geo_json_id)
    #     self.locator_finder_by_hover_item_id(self.select_geo_background_id)
    #     time.sleep(2)
    #     self.wait_for_ajax()

    # def creating_persistent_index(self):
    #     """Filling up all the information for persistent index"""
    #     select_persistent_fields_sitem = self.locator_finder_by_hover_item_id(self.select_persistent_fields_id)
    #     select_persistent_fields_sitem.send_keys("pfields").perform()
    #     select_persistent_name_sitem = self.locator_finder_by_hover_item_id(self.select_persistent_name_id)
    #     select_persistent_name_sitem.send_keys("pname").perform()
    #     self.locator_finder_by_hover_item_id(self.select_persistent_unique_id)
    #     self.locator_finder_by_hover_item_id(self.select_persistent_sparse_id)
    #     self.locator_finder_by_hover_item_id(self.select_persistent_duplicate_id)
    #     self.locator_finder_by_hover_item_id(self.select_persistent_background_id)
    #     time.sleep(2)
    #     self.wait_for_ajax()

    # def creating_fulltext_index(self):
    #     """Filling up all the information for Fulltext index"""
    #     select_fulltext_field_sitem = self.locator_finder_by_hover_item_id(self.select_fulltext_field_id)
    #     select_fulltext_field_sitem.send_keys("ffields").perform()
    #     select_fulltext_name_sitem = self.locator_finder_by_hover_item_id(self.select_fulltext_name_id)
    #     select_fulltext_name_sitem.send_keys("fname").perform()
    #     select_fulltext_length_sitem = self.locator_finder_by_hover_item_id(self.select_fulltext_length_id)
    #     select_fulltext_length_sitem.send_keys(100)
    #     self.locator_finder_by_hover_item_id(self.select_fulltext_background_id)
    #     time.sleep(2)
    #     self.wait_for_ajax()

    # def creating_ttl_index(self):
    #     """Filling up all the information for TTL index"""
    #     select_ttl_field_sitem = self.locator_finder_by_hover_item_id(self.select_ttl_field_id)
    #     select_ttl_field_sitem.send_keys("tfields").perform()
    #     select_ttl_name_sitem = self.locator_finder_by_hover_item_id(self.select_ttl_name_id)
    #     select_ttl_name_sitem.send_keys("tname").perform()
    #     select_ttl_expiry_sitem = self.locator_finder_by_hover_item_id(self.select_ttl_expiry_id)
    #     select_ttl_expiry_sitem.send_keys(1000)
    #     self.locator_finder_by_hover_item_id(self.select_ttl_background_id)
    #     time.sleep(2)
    #     self.wait_for_ajax()

    def create_new_index(self, index_name, value, cluster_status):
        print(f"Creating {index_name} index started \n")
        create_new_index_btn_sitem = self.locator_finder_by_id(self.create_new_index_btn_id)
        create_new_index_btn_sitem.click()
        time.sleep(2)

        print(f"selecting {index_name} from the list\n")
        self.locator_finder_by_select(self, self.select_index_type_id, value)

        if index_name == "Persistent":
            self.select_persistent_fields_id = self.locator_finder_by_hover_item_id(
                self, self.select_persistent_fields_id
            )
            time.sleep(1)
            self.select_persistent_fields_id.send_keys("pfields").perform()
            self.select_persistent_name_id = self.locator_finder_by_hover_item_id(self, self.select_persistent_name_id)
            self.select_persistent_name_id.send_keys("pname").perform()
            time.sleep(1)

            if cluster_status:
                self.select_persistent_unique_id = self.locator_finder_by_hover_item_id(
                    self, self.select_persistent_unique_id
                )

            self.select_persistent_sparse_id = self.locator_finder_by_hover_item_id(
                self, self.select_persistent_sparse_id
            )
            self.select_persistent_duplicate_id = self.locator_finder_by_hover_item_id(
                self, self.select_persistent_duplicate_id
            )
            self.select_persistent_background_id = self.locator_finder_by_hover_item_id(
                self, self.select_persistent_background_id
            )
            time.sleep(1)

        elif index_name == "Geo":
            self.select_geo_fields_id = self.locator_finder_by_hover_item_id(self, self.select_geo_fields_id)
            self.select_geo_fields_id.send_keys("gfields").perform()
            time.sleep(1)
            self.select_geo_name_id = self.locator_finder_by_hover_item_id(self, self.select_geo_name_id)
            self.select_geo_name_id.send_keys("gname").perform()
            time.sleep(1)
            self.select_geo_json_id = self.locator_finder_by_hover_item_id(self, self.select_geo_json_id)
            self.select_geo_background_id = self.locator_finder_by_hover_item_id(self, self.select_geo_background_id)
            time.sleep(1)
            self.wait_for_ajax()

        elif index_name == "Fulltext":
            self.select_fulltext_field_id = self.locator_finder_by_hover_item_id(self, self.select_fulltext_field_id)
            self.select_fulltext_field_id.send_keys("ffields").perform()
            time.sleep(1)
            self.select_fulltext_name_id = self.locator_finder_by_hover_item_id(self, self.select_fulltext_name_id)
            self.select_fulltext_name_id.send_keys("fname").perform()
            time.sleep(1)
            self.select_fulltext_length_id = self.locator_finder_by_hover_item_id(self, self.select_fulltext_length_id)
            self.select_fulltext_length_id.send_keys(100)
            self.select_fulltext_background_id = self.locator_finder_by_hover_item_id(
                self, self.select_fulltext_background_id
            )
            time.sleep(1)
            self.wait_for_ajax()

        elif index_name == "TTL":
            self.select_ttl_field_id = self.locator_finder_by_hover_item_id(self, self.select_ttl_field_id)
            self.select_ttl_field_id.send_keys("tfields").perform()
            time.sleep(1)
            self.select_ttl_name_id = self.locator_finder_by_hover_item_id(self, self.select_ttl_name_id)
            self.select_ttl_name_id.send_keys("tname").perform()
            time.sleep(1)
            self.select_ttl_expiry_id = self.locator_finder_by_hover_item_id(self, self.select_ttl_expiry_id)
            self.select_ttl_expiry_id.send_keys(1000)
            self.select_ttl_background_id = self.locator_finder_by_hover_item_id(self, self.select_ttl_background_id)
            time.sleep(1)
            self.wait_for_ajax()

        # experimental feature
        elif index_name == "ZKD":
            select_zkd_field_sitem = self.locator_finder_by_id("newZkdFields")
            select_zkd_field_sitem.click()
            select_zkd_field_sitem.clear()
            select_zkd_field_sitem.send_keys("zkdfileds")

            select_zkd_name_sitem = self.locator_finder_by_id("newZkdName")
            select_zkd_name_sitem.click()
            select_zkd_name_sitem.clear()
            select_zkd_name_sitem.send_keys("zkdname")

        select_create_index_btn_sitem = self.locator_finder_by_id(self.select_create_index_btn_id)
        select_create_index_btn_sitem.click()
        time.sleep(2)
        self.wait_for_ajax()

        print(f"Creating {index_name} index completed \n")

    # this method will delete all the indexes one by one
    def delete_all_index(self):
        """this method will delete all the indexes one by one"""
        select_index_for_delete_sitem = self.locator_finder_by_xpath(self, self.select_index_for_delete_id)
        select_index_for_delete_sitem.click()

        select_index_confirm_delete_sitem = self.locator_finder_by_id(self.select_index_confirm_delete)
        select_index_confirm_delete_sitem.click()
        self.webdriver.refresh()

    def select_info_tab(self):
        """Selecting info tab from the collection submenu"""
        self.click_submenu_entry("Info")
        time.sleep(2)
        self.wait_for_ajax()

    def select_schema_tab(self):
        """Selecting Schema tab from the collection submenu"""
        if super().current_package_version() >= 3.8:
            select_schema_tab_sitem = self.locator_finder_by_xpath(self.select_schema_tab_id)
            select_schema_tab_sitem.click()
            time.sleep(2)
        else:
            print("Schema check not supported for the current package \n")
        time.sleep(2)
        self.wait_for_ajax()

    def select_settings_tab(self, is_cluster):
        """Selecting settings tab from the collection submenu"""
        self.click_submenu_entry("Settings")
        if not is_cluster:
            select_settings_name_textbox_sitem = self.locator_finder_by_id(self.select_settings_name_textbox_id)
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
        print("Loading Index into memory\n")
        select_load_index_into_memory_sitem = self.locator_finder_by_xpath(self.select_load_index_into_memory_id)
        select_load_index_into_memory_sitem.click()
        time.sleep(2)
        self.wait_for_ajax()

    def select_settings_unload_btn(self):
        """Loading and Unloading collection"""
        select_settings_unload_btn_sitem = self.locator_finder_by_xpath(self.select_settings_unload_btn_id)
        select_settings_unload_btn_sitem.click()
        time.sleep(2)
        self.wait_for_ajax()

    def select_truncate_btn(self):
        """Loading and Unloading collection"""
        select_truncate_btn_sitem = self.locator_finder_by_xpath(self.select_truncate_btn_id)
        select_truncate_btn_sitem.click()
        time.sleep(1)
        select_truncate_confirm_btn_sitem = self.locator_finder_by_xpath(self.select_truncate_confirm_btn_id)
        select_truncate_confirm_btn_sitem.click()
        time.sleep(2)
        self.wait_for_ajax()

    def select_delete_collection(self):
        """Deleting Collection from settings tab"""
        delete_collection_sitem = self.locator_finder_by_xpath(self.delete_collection_id)
        delete_collection_sitem.click()
        time.sleep(1)
        delete_collection_confirm_sitem = self.locator_finder_by_xpath(self.delete_collection_confirm_id)
        delete_collection_confirm_sitem.click()

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
        selector = """//div[contains(@class, 'tile')][@id='collection_%s']""" % collection_name
        self.locator_finder_by_xpath(selector).click()

    def delete_collection(self, collection_name, collection_locator):
        """This method will delete all the collection"""
        print(f"Deleting {collection_name} collection started \n")
        self.select_collection_page()

        try:
            self.locator_finder_by_xpath(self, collection_locator).click()

            self.select_settings_tab()
            self.select_delete_collection()

            print(f"Deleting {collection_name} collection Completed \n")
            self.driver.refresh()
        except TimeoutException:
            print("TimeoutException occurred! \n")
            print("Info: Collection has already been deleted or never created. \n")
        except Exception:
            traceback.print_exc()
            raise Exception("Critical Error occurred and need manual inspection!! \n")

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
                print("Unexpected error occurred!")

        except TimeoutException as ex:
            if test_name == "access":
                print("Collection creation failed, which is expected")
            if test_name == "read/write":
                raise Exception("Unexpected error occurred!") from ex
