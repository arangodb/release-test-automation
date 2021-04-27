import time
from baseSelenium import BaseSelenium


class CollectionPage(BaseSelenium):

    def __init__(self, driver):
        super().__init__()
        self.driver = driver
        self.select_collection_page_id = "collections"
        self.select_create_collection_id = "createCollection"
        self.select_new_collection_name_id = "new-collection-name"
        self.select_collection_type_id = "new-collection-type"
        self.select_advance_option_id = "/html//div[@id='accordion2']//a[@href='#collapseOne']"
        self.wait_for_sync_id = "new-collection-sync"
        self.create_new_collection_btn_id = "modalButton1"
        self.select_collection_settings_id = "collectionsToggle"
        self.display_system_collection_id = "//div[@id='collectionsDropdown']" \
                                            "/ul[1]/li[2]/a/label[@class='checkbox checkboxLabel']"
        self.display_document_collection_id = "//div[@id='collectionsDropdown']" \
                                              "/ul[1]/li[3]/a/label[@class='checkbox checkboxLabel']"
        self.display_edge_collection_id = "//div[@id='collectionsDropdown']" \
                                          "/ul[1]/li[4]/a/label[@class='checkbox checkboxLabel']"
        self.select_status_loaded_id = "//div[@id='collectionsDropdown']" \
                                       "/ul[2]/li[2]/a[@href='#']/label[@class='checkbox checkboxLabel']"
        self.select_status_unloaded_id = "//div[@id='collectionsDropdown']" \
                                         "/ul[2]/li[3]/a[@href='#']/label[@class='checkbox checkboxLabel']"
        self.sort_by_name_id = "//div[@id='collectionsDropdown']" \
                               "/ul[3]/li[2]/a[@href='#']/label[@class='checkbox checkboxLabel']"
        self.sort_by_type_id = "//div[@id='collectionsDropdown']" \
                               "/ul[3]/li[3]/a[@href='#']/label[@class='checkbox checkboxLabel']"
        self.sort_descending_id = "//div[@id='collectionsDropdown']" \
                                  "/ul[3]/li[4]/a[@href='#']/label[@class='checkbox checkboxLabel']"

        self.select_doc_collection_id = "//div[@id='collection_TestDoc']//h5[@class='collectionName']"

        self.select_upload_btn_id = "/html//a[@id='importCollection']"

        self.select_choose_file_btn_id = "/html//input[@id='importDocuments']"
        self.select_confirm_upload_btn_id = "confirmDocImport"
        self.getting_total_row_count_id = "/html//a[@id='totalDocuments']"
        self.display_document_size_id = "documentSize"
        self.move_first_page_id = "//div[@id='documentsToolbarF']/ul[@class='arango-pagination']//a[.='1']"
        self.move_second_page_id = "//div[@id='documentsToolbarF']/ul[@class='arango-pagination']//a[.='2']"

        self.select_collection_setting_id = "//div[@id='subNavigationBar']/ul[2]//a[.='Settings']"
        self.select_hand_pointer_id = "/html//a[@id='markDocuments']"

        self.row1_id = "//div[@id='docPureTable']/div[2]/div[1]"
        self.row2_id = "//div[@id='docPureTable']/div[2]/div[3]"
        self.row3_id = "//div[@id='docPureTable']/div[2]/div[5]"
        self.row4_id = "//div[@id='docPureTable']/div[2]/div[7]"
        self.move_btn_id = "/html//button[@id='moveSelected']"
        self.move_doc_textbox_id = "move-documents-to"
        self.move_confirm_btn_id = "modalButton1"
        self.select_collection_delete_btn_id = "deleteSelected"
        self.collection_delete_confirm_btn_id = "//*[@id='modalButton1']"
        self.collection_really_dlt_btn_id = "/html//button[@id='modal-confirm-delete']"
        self.select_index_menu_id = "//*[@id='subNavigationBar']/ul[2]/li[2]/a"
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

        self.select_index_for_delete_id = "/html//table[@id='collectionEditIndexTable']" \
                                          "/tbody/tr[2]/th[9]/span[@title='Delete index']"
        self.select_index_confirm_delete = "indexConfirmDelete"
        self.select_info_tab_id = "//*[@id='subNavigationBar']/ul[2]/li[3]/a"

        self.select_schema_tab_id = "//*[@id='subNavigationBar']/ul[2]/li[5]/a"

        self.select_settings_tab_id = "//*[@id='subNavigationBar']/ul[2]/li[4]/a"
        self.select_settings_name_textbox_id = "change-collection-name"
        self.select_settings_wait_type_id = "change-collection-sync"
        self.select_new_settings_save_btn_id = "//*[@id='modalButton5']"

        self.select_load_index_into_memory_id = "//*[@id='modalButton2']"
        self.select_settings_unload_btn_id = "//*[@id='modalButton3']"
        self.select_truncate_btn_id = "//*[@id='modalButton1']"
        self.select_truncate_confirm_btn_id = "//*[@id='modal-confirm-delete']"
        self.delete_collection_id = "//*[@id='modalButton0']"
        self.delete_collection_confirm_id = "//*[@id='modal-confirm-delete']"

        self.select_edge_collection_upload_id = "//*[@id='collection_TestEdge']/div/h5"
        self.select_edge_collection_id = "//*[@id='collection_TestEdge']/div/h5"
        self.select_edge_settings_id = "//*[@id='subNavigationBar']/ul[2]/li[4]/a"
        self.select_test_doc_settings_id = "//*[@id='subNavigationBar']/ul[2]/li[4]/a"

        self.select_test_doc_collection_id = "//div[@id='collection_Test']//h5[@class='collectionName']"

    # selecting collection tab
    def select_collection_page(self):
        self.select_collection_page_id = \
            BaseSelenium.locator_finder_by_id(self, self.select_collection_page_id)
        self.select_collection_page_id.click()

    # Clicking on create new collection box
    def select_create_collection(self):
        self.select_create_collection_id = \
            BaseSelenium.locator_finder_by_id(self, self.select_create_collection_id)
        self.select_create_collection_id.click()

    # Providing new collection name
    def select_new_collection_name(self, name):
        self.select_new_collection_name_id = \
            BaseSelenium.locator_finder_by_id(self, self.select_new_collection_name_id)
        self.select_new_collection_name_id.click()
        self.select_new_collection_name_id.send_keys(name)

    # Selecting collection Document type where # '2' = Document, '3' = Edge
    def select_collection_type(self, value):
        self.select_collection_type_id = \
            BaseSelenium.locator_finder_by_select(self, self.select_collection_type_id, value)

    def select_advance_option(self):
        self.select_advance_option_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.select_advance_option_id)
        self.select_advance_option_id.click()

    # Selecting collection wait type where value # 0 = YES, '1' = NO
    def wait_for_sync(self, value):
        self.wait_for_sync_id = \
            BaseSelenium.locator_finder_by_select(self, self.wait_for_sync_id, value)

    # selecting collection tab
    def create_new_collection_btn(self):
        self.create_new_collection_btn_id = \
            BaseSelenium.locator_finder_by_id(self, self.create_new_collection_btn_id)
        self.create_new_collection_btn_id.click()
        time.sleep(3)

    # selecting collection settings icon
    def select_collection_settings(self):
        self.select_collection_settings_id = \
            BaseSelenium.locator_finder_by_id(self, self.select_collection_settings_id)
        self.select_collection_settings_id.click()

    # Displaying system's collection
    def display_system_collection(self):
        self.display_system_collection_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.display_system_collection_id)
        self.display_system_collection_id.click()
        time.sleep(2)

    # Displaying Document type collection
    def display_document_collection(self):
        self.display_document_collection_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.display_document_collection_id)
        self.display_document_collection_id.click()
        time.sleep(2)

    # Displaying Edge type collection
    def display_edge_collection(self):
        self.display_edge_collection_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.display_edge_collection_id)
        self.display_edge_collection_id.click()
        time.sleep(2)

    # Displaying status loaded collection
    def select_status_loaded(self):
        self.select_status_loaded_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.select_status_loaded_id)
        self.select_status_loaded_id.click()
        time.sleep(2)

    # Displaying status unloaded collection
    def select_status_unloaded(self):
        self.select_status_unloaded_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.select_status_unloaded_id)
        self.select_status_unloaded_id.click()
        time.sleep(2)

    # Sorting collection by type
    def sort_by_type(self):
        self.sort_by_type_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.sort_by_type_id)
        self.sort_by_type_id.click()
        time.sleep(2)

    # Sorting collection by descending
    def sort_descending(self):
        self.sort_descending_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.sort_descending_id)
        self.sort_descending_id.click()
        time.sleep(2)

    # Sorting collection by name
    def sort_by_name(self):
        self.sort_by_name_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.sort_by_name_id)
        self.sort_by_name_id.click()
        time.sleep(2)

    # selecting TestDoc Collection
    def select_doc_collection(self):
        self.select_doc_collection_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.select_doc_collection_id)
        self.select_doc_collection_id.click()

    # selecting collection upload btn
    def select_upload_btn(self):
        self.select_upload_btn_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.select_upload_btn_id)
        self.select_upload_btn_id.click()
        time.sleep(3)

    # This method will upload the file with the file path given
    def select_choose_file_btn(self, path):
        self.select_choose_file_btn_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.select_choose_file_btn_id)
        time.sleep(2)
        self.select_choose_file_btn_id.send_keys(path)

    # Confirm file upload btn
    def select_confirm_upload_btn(self):
        self.select_confirm_upload_btn_id = \
            BaseSelenium.locator_finder_by_id(self, self.select_confirm_upload_btn_id)
        self.select_confirm_upload_btn_id.click()

    # Confirm file upload btn
    def getting_total_row_count(self):
        self.getting_total_row_count_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.getting_total_row_count_id)
        return self.getting_total_row_count_id.text

    # Choose how many rows of docs will be display
    def display_document_size(self, value):
        self.display_document_size_id = \
            BaseSelenium.locator_finder_by_select(self, self.display_document_size_id, value)
        time.sleep(2)

    # After changing the display size checking everything loads
    def traverse_search_pages(self):
        self.move_second_page_id = \
            BaseSelenium.locator_finder_by_hover_item(self, self.move_second_page_id)
        time.sleep(2)
        self.move_first_page_id = \
            BaseSelenium.locator_finder_by_hover_item(self, self.move_first_page_id)
        time.sleep(2)

    # Selecting Hand selection button
    def select_hand_pointer(self):
        self.select_hand_pointer_id = \
            BaseSelenium.locator_finder_by_hover_item(self, self.select_hand_pointer_id)

    # selecting multiple document rows from the current collection
    def select_multiple_item(self):
        # selecting multiple rows of collection
        time.sleep(2)
        self.row1_id = \
            BaseSelenium.locator_finder_by_hover_item(self, self.row1_id)
        self.row2_id = \
            BaseSelenium.locator_finder_by_hover_item(self, self.row2_id)
        self.row3_id = \
            BaseSelenium.locator_finder_by_hover_item(self, self.row3_id)
        self.row4_id = \
            BaseSelenium.locator_finder_by_hover_item(self, self.row4_id)
        time.sleep(1)

    # selecting collection move button after selecting
    def move_btn(self):
        self.move_btn_id = \
            BaseSelenium.locator_finder_by_hover_item(self, self.move_btn_id)
        time.sleep(1)

    # selecting Collection to move the selected data
    def move_doc_textbox(self, collection):
        self.move_doc_textbox_id = \
            BaseSelenium.locator_finder_by_id(self, self.move_doc_textbox_id)
        self.move_doc_textbox_id.click()
        self.move_doc_textbox_id.send_keys(collection)

    # Confirming move data to the Collection
    def move_confirm_btn(self):
        self.move_confirm_btn_id = \
            BaseSelenium.locator_finder_by_id(self, self.move_confirm_btn_id)
        self.move_confirm_btn_id.click()

    # Selecting delete button for selected data
    def select_collection_delete_btn(self):
        self.select_collection_delete_btn_id = \
            BaseSelenium.locator_finder_by_id(self, self.select_collection_delete_btn_id)
        self.select_collection_delete_btn_id.click()

    # Selecting delete button for selected data
    def collection_delete_confirm_btn(self):
        self.collection_delete_confirm_btn_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.collection_delete_confirm_btn_id)
        self.collection_delete_confirm_btn_id.click()

    # Selecting really delete button for selected data
    def collection_really_dlt_btn(self):
        self.collection_really_dlt_btn_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.collection_really_dlt_btn_id)
        self.collection_really_dlt_btn_id.click()

    # Selecting index menu from collection
    def select_index_menu(self):
        self.select_index_menu_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.select_index_menu_id)
        self.select_index_menu_id.click()

    # Selecting index menu from collection
    def create_new_index_btn(self):
        self.create_new_index_btn_id = \
            BaseSelenium.locator_finder_by_id(self, self.create_new_index_btn_id)
        self.create_new_index_btn_id.click()
        time.sleep(2)

    # Selecting type of index here 1 = Geo, 2 = persistent, 3 = Fulltext, 4 = TTL type
    def select_index_type(self, value):
        self.select_index_type_id = \
            BaseSelenium.locator_finder_by_select(self, self.select_index_type_id, value)

    # Selecting index menu from collection
    def select_create_index_btn(self):
        self.select_create_index_btn_id = \
            BaseSelenium.locator_finder_by_id(self, self.select_create_index_btn_id)
        self.select_create_index_btn_id.click()
        time.sleep(2)

    # Filling up all the information for geo index
    def creating_geo_index(self):
        self.select_geo_fields_id = \
            BaseSelenium.locator_finder_by_hover_item_id(self, self.select_geo_fields_id)
        self.select_geo_fields_id.send_keys("gfields").perform()
        self.select_geo_name_id = \
            BaseSelenium.locator_finder_by_hover_item_id(self, self.select_geo_name_id)
        self.select_geo_name_id.send_keys("gname").perform()
        self.select_geo_json_id = \
            BaseSelenium.locator_finder_by_hover_item_id(self, self.select_geo_json_id)
        self.select_geo_background_id = \
            BaseSelenium.locator_finder_by_hover_item_id(self, self.select_geo_background_id)
        time.sleep(1)

    # Filling up all the information for persistent index
    def creating_persistent_index(self):
        self.select_persistent_fields_id = \
            BaseSelenium.locator_finder_by_hover_item_id(self, self.select_persistent_fields_id)
        self.select_persistent_fields_id.send_keys("pfields").perform()
        self.select_persistent_name_id = \
            BaseSelenium.locator_finder_by_hover_item_id(self, self.select_persistent_name_id)
        self.select_persistent_name_id.send_keys("pname").perform()
        self.select_persistent_unique_id = \
            BaseSelenium.locator_finder_by_hover_item_id(self, self.select_persistent_unique_id)
        self.select_persistent_sparse_id = \
            BaseSelenium.locator_finder_by_hover_item_id(self, self.select_persistent_sparse_id)
        self.select_persistent_duplicate_id = \
            BaseSelenium.locator_finder_by_hover_item_id(self, self.select_persistent_duplicate_id)
        self.select_persistent_background_id = \
            BaseSelenium.locator_finder_by_hover_item_id(self, self.select_persistent_background_id)
        time.sleep(1)

    # Filling up all the information for Fulltext index
    def creating_fulltext_index(self):
        self.select_fulltext_field_id = \
            BaseSelenium.locator_finder_by_hover_item_id(self, self.select_fulltext_field_id)
        self.select_fulltext_field_id.send_keys("ffields").perform()
        self.select_fulltext_name_id = \
            BaseSelenium.locator_finder_by_hover_item_id(self, self.select_fulltext_name_id)
        self.select_fulltext_name_id.send_keys("fname").perform()
        self.select_fulltext_length_id = \
            BaseSelenium.locator_finder_by_hover_item_id(self, self.select_fulltext_length_id)
        self.select_fulltext_length_id.send_keys(100)
        self.select_fulltext_background_id = \
            BaseSelenium.locator_finder_by_hover_item_id(self, self.select_fulltext_background_id)
        time.sleep(1)

    # Filling up all the information for TTL index
    def creating_ttl_index(self):
        self.select_ttl_field_id = \
            BaseSelenium.locator_finder_by_hover_item_id(self, self.select_ttl_field_id)
        self.select_ttl_field_id.send_keys("tfields").perform()
        self.select_ttl_name_id = \
            BaseSelenium.locator_finder_by_hover_item_id(self, self.select_ttl_name_id)
        self.select_ttl_name_id.send_keys("tname").perform()
        self.select_ttl_expiry_id = \
            BaseSelenium.locator_finder_by_hover_item_id(self, self.select_ttl_expiry_id)
        self.select_ttl_expiry_id.send_keys(1000)
        self.select_ttl_background_id = \
            BaseSelenium.locator_finder_by_hover_item_id(self, self.select_ttl_background_id)
        time.sleep(1)

    # this method will delete all the indexes one by one
    def delete_all_index(self):
        self.select_index_for_delete_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.select_index_for_delete_id)
        self.select_index_for_delete_id.click()
        self.select_index_confirm_delete = \
            BaseSelenium.locator_finder_by_id(self, self.select_index_confirm_delete)
        self.select_index_confirm_delete.click()

    # Selecting info tab from the collection submenu
    def select_info_tab(self):
        self.select_info_tab_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.select_info_tab_id)
        self.select_info_tab_id.click()
        time.sleep(2)

    # Selecting Schema tab from the collection submenu
    def select_schema_tab(self):
        self.select_schema_tab_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.select_schema_tab_id)
        self.select_schema_tab_id.click()
        time.sleep(2)

    # Selecting settings tab from the collection submenu
    def select_settings_tab(self):
        self.select_settings_tab_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.select_settings_tab_id)
        self.select_settings_tab_id.click()
        self.select_settings_name_textbox_id = \
            BaseSelenium.locator_finder_by_id(self, self.select_settings_name_textbox_id)
        self.select_settings_name_textbox_id.click()
        self.select_settings_name_textbox_id.send_keys("testDocRenamed")
        self.select_settings_wait_type_id = \
            BaseSelenium.locator_finder_by_select(self, self.select_settings_wait_type_id, 0)
        self.select_new_settings_save_btn_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.select_new_settings_save_btn_id)
        self.select_new_settings_save_btn_id.click()
        time.sleep(2)
        print("Loading Index into memory\n")
        self.select_load_index_into_memory_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.select_load_index_into_memory_id)
        self.select_load_index_into_memory_id.click()
        time.sleep(2)

    # Loading and Unloading collection
    def select_settings_unload_btn(self):
        self.select_settings_unload_btn_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.select_settings_unload_btn_id)
        self.select_settings_unload_btn_id.click()
        time.sleep(2)

    # Loading and Unloading collection
    def select_truncate_btn(self):
        self.select_truncate_btn_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.select_truncate_btn_id)
        self.select_truncate_btn_id.click()
        time.sleep(1)
        self.select_truncate_confirm_btn_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.select_truncate_confirm_btn_id)
        self.select_truncate_confirm_btn_id.click()
        time.sleep(2)

    # Deleting Collection from settings tab
    def delete_collection(self):
        self.delete_collection_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.delete_collection_id)
        self.delete_collection_id.click()
        time.sleep(1)
        self.delete_collection_confirm_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.delete_collection_confirm_id)
        self.delete_collection_confirm_id.click()

    # selecting Edge collection for data uploading
    def select_edge_collection_upload(self):
        self.select_edge_collection_upload_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.select_edge_collection_upload_id)
        self.select_edge_collection_upload_id.click()

    # selecting TestEdge Collection
    def select_edge_collection(self):
        self.select_edge_collection_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.select_edge_collection_id)
        self.select_edge_collection_id.click()
        self.select_edge_settings_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.select_edge_settings_id)
        self.select_edge_settings_id.click()

    # selecting TestEdge Collection
    def select_test_doc_col(self):
        self.select_test_doc_collection_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.select_test_doc_collection_id)
        self.select_test_doc_collection_id.click()
        self.select_test_doc_settings_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.select_test_doc_settings_id)
        self.select_test_doc_settings_id.click()
