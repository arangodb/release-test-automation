#!/usr/bin/env python3
""" collection page object """
import time
import semver
import traceback
import json
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import ElementNotInteractableException, TimeoutException, NoSuchElementException
from selenium_ui_test.pages.navbar import NavigationBarPage


# can't circumvent long lines.. nAttr nLines
# pylint: disable=line-too-long disable=too-many-instance-attributes disable=too-many-statements disable=too-many-public-methods


class CollectionPage(NavigationBarPage):
    """Collection page class"""

    def __init__(self, webdriver, cfg):
        """class initialization"""
        super().__init__(webdriver, cfg)
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
        # self.sort_by_name_id = "sortName"
        # self.sort_by_type_id = "sortType"
        # self.sort_descending_id = "sortOrder"
        self.sort_by_name_id = '//*[@id="collectionsDropdown"]/ul[2]/li[2]/a/label/i'
        self.sort_by_type_id = '//*[@id="collectionsDropdown"]/ul[2]/li[3]/a/label/i'
        self.sort_descending_id = '//*[@id="collectionsDropdown"]/ul[2]/li[4]/a/label/i'

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

        self.select_index_for_delete_id = "/html//table[@id='collectionEditIndexTable']/tbody/tr[2]/th[9]/span[" \
                                          "@title='Delete index']"
        self.select_index_confirm_delete = "indexConfirmDelete"
        self.select_info_tab_id = "//*[@id='subNavigationBarPage']/ul[2]/li[3]/a"

        self.select_schema_tab_id = "//*[@id='subNavigationBarPage']/ul[2]/li[5]/a"

        self.select_settings_tab_id = "//*[@id='subNavigationBarPage']/ul[2]/li[4]/a"
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
        self.select_settings_tab_id = "//*[@id='subNavigationBar']/ul[2]/li[4]/a"
        self.select_renamed_doc_collection_id = '//*[@id="collection_testDocRenamed"]/div/h5'
        self.select_computedValueCol_id = '//*[@id="collection_ComputedValueCol"]/div/h5'

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
        print('selecting collection tab \n')
        select_collection_page_sitem = self.locator_finder_by_id(self.select_collection_page_id)
        select_collection_page_sitem.click()
        time.sleep(1)

        print('Clicking on create new collection box \n')
        select_create_collection_sitem = self.locator_finder_by_id(self.select_create_collection_id)
        select_create_collection_sitem.click()
        time.sleep(1)

        print('Selecting new collection name \n')
        select_new_collection_name_sitem = self.locator_finder_by_id(self.select_new_collection_name_id)
        select_new_collection_name_sitem.click()
        select_new_collection_name_sitem.send_keys(name)
        time.sleep(1)

        print(f'Selecting collection type for {name} \n')  # collection Document type where # '2' = Document, '3' = Edge
        self.locator_finder_by_select(self.select_collection_type_id, doc_type)
        time.sleep(1)

        if is_cluster:
            print(f'selecting number of Shards for the {name} \n')
            shards = 'new-collection-shards'
            shards_sitem = self.locator_finder_by_id(shards)
            shards_sitem.click()
            shards_sitem.clear()
            shards_sitem.send_keys(9)
            time.sleep(2)

            print(f'selecting number of replication factor for {name} \n')
            rf = 'new-replication-factor'
            rf_sitem = self.locator_finder_by_id(rf)
            rf_sitem.click()
            rf_sitem.clear()
            rf_sitem.send_keys(3)
            time.sleep(2)

        print(f'Selecting collection advance options for {name} \n')
        select_advance_option_sitem = self.locator_finder_by_xpath(self.select_advance_option_id)
        select_advance_option_sitem.click()
        time.sleep(1)

        # Selecting collection wait type where value # 0 = YES, '1' = NO)
        self.locator_finder_by_select(self.wait_for_sync_id, 0)
        time.sleep(1)

        print(f'Selecting create button for {name} \n')
        create_new_collection_btn_sitem = self.locator_finder_by_id(self.create_new_collection_btn_id)
        create_new_collection_btn_sitem.click()
        time.sleep(3)
        self.webdriver.refresh()

    def ace_set_value(self, query):
        """This method will take a string argument and will execute the query on ace editor"""
        warning = 'button-warning'
        warning_sitem = self.locator_finder_by_class(warning)
        # Set x and y offset positions of element
        xOffset = 100
        yOffset = 100
        # Performs mouse move action onto the element
        actions = ActionChains(self.webdriver).move_to_element_with_offset(warning_sitem, xOffset, yOffset)
        actions.click()
        actions.key_down(Keys.CONTROL).send_keys('a').send_keys(Keys.BACKSPACE).key_up(Keys.CONTROL)
        time.sleep(1)
        actions.send_keys(f'{query}')
        actions.perform()
        time.sleep(1)

        print("Saving current computed value")
        save_computed_value = 'saveComputedValuesButton'
        save_computed_value_sitem = self.locator_finder_by_id(save_computed_value)
        save_computed_value_sitem.click()
        time.sleep(2)

        self.webdriver.refresh()

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
        if (size["width"] > 1000):
            getting_total_row_count_sitem = self.locator_finder_by_xpath(self.getting_total_row_count_id, 20)
            return getting_total_row_count_sitem.text
        else:
            print("your browser window is to narrow! " + str(size))
            return "-1"


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
    
    def select_testdoc_collection(self):
        print('Selecting TestDoc Collection \n')
        select_doc_collection_sitem = self.locator_finder_by_xpath(self.select_doc_collection_id)
        select_doc_collection_sitem.click()
        time.sleep(1)
    
    def create_index(self, index_name):
        """This method will create indexes for >= v3.11.0"""
        print(f"Creating {index_name} index started \n")
        add_index = '//*[@id="content-react"]/div/div/button'
        create_new_index_btn_sitem = self.locator_finder_by_xpath(add_index)
        create_new_index_btn_sitem.click()
        time.sleep(2)

        print(f"selecting {index_name} from the list\n")

        if index_name == 'Persistent':
            # selecting persistent index's filed
            persistent_field = "/html//input[@id='fields']"
            persistent_field_sitem = self.locator_finder_by_xpath(persistent_field)
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
            duplicate_array = '//*[@id="content-react"]/div/div[3]/form/div/div[1]/div[11]/label/span/span'
            duplicate_array_sitem = self.locator_finder_by_xpath(duplicate_array)
            duplicate_array_sitem.click()

            memory_cache = '//*[@id="content-react"]/div/div[3]/form/div/div[1]/div[15]/label/span/span'
            memory_cache_sitem = self.locator_finder_by_xpath(memory_cache)
            memory_cache_sitem.click()

        elif index_name == 'Geo':
            self.select_desired_index_from_the_list('Geo Index')
            # selecting geo index's filed
            geo_field = "/html//input[@id='fields']"
            geo_field_sitem = self.locator_finder_by_xpath(geo_field)
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
            full_text_field_sitem = self.locator_finder_by_xpath(full_text_field)
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
            ttl_field_sitem = self.locator_finder_by_xpath(ttl_field)
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

            fields = "(//div[contains(@class,'css-1d6mnfj')])[2]"
            fields_sitem = self.locator_finder_by_xpath(fields)
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

        else:
            try:
                self.navbar_goto("collections")
                print("Selecting computed values collections. \n")
                col = '//*[@id="collection_ComputedValueCol"]/div/h5'
                self.locator_finder_by_xpath(col).click()
                time.sleep(1)

                self.select_index_menu()

                create_new_index_btn_sitem = self.locator_finder_by_xpath(add_index)
                create_new_index_btn_sitem.click()
                time.sleep(2)

                print('ZKD Index (EXPERIMENTAL)')
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
                print(e)
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
        print(f"Creating {index_name} index started \n")
        add_index = "/html//i[@id='addIndex']"
        self.locator_finder_by_xpath(add_index).click()
        time.sleep(2)

        print(f"selecting {index_name} from the list\n")
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
                print("Selecting computed values collections. \n")
                col = '//*[@id="collection_ComputedValueCol"]/div/h5'
                self.locator_finder_by_xpath(col).click()
                self.select_index_menu()

                print(f"Creating {index_name} index started \n")
                self.locator_finder_by_xpath(add_index).click()
                time.sleep(2)

                print(f"selecting {index_name} from the list\n")
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

        select_create_index_btn_id = "createIndex"
        self.locator_finder_by_id(select_create_index_btn_id).click()
        time.sleep(10)
        self.webdriver.refresh()

        if check:
            self.navbar_goto("collections")
            self.select_collection("TestDoc")
            self.select_index_menu()

        print(f"Creating {index_name} index completed \n")

    def delete_all_index(self, check=False):
        """this method will delete all the indexes one by one"""
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
            print('Something went wrong', e, '\n')
    
    def delete_index(self, index):
        """this method will delete all the indexes one by one"""
        try:
            delete = f"(//*[name()='svg'][@class='chakra-icon css-onkibi'])[{index}]"
            delete_sitem = self.locator_finder_by_xpath(delete)
            delete_sitem.click()
            time.sleep(1)
            delete_confirmation = "//*[text()='Delete']"
            delete_confirmation_stiem = self.locator_finder_by_xpath(delete_confirmation)
            delete_confirmation_stiem.click()
            time.sleep(1)
        except TimeoutException as e:
            print('Something went wrong', e, '\n')
            print("Trying again to delete the inverted index")
            self.driver.refresh()
            self.select_collection_page()
            self.select_testdoc_collection()
            self.select_index_menu()
            self.delete_index(3)

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
                select_schema_tab_sitem = self.locator_finder_by_xpath(schema)
            else:
                select_schema_tab_sitem = self.locator_finder_by_xpath(self.select_schema_tab_id)
            select_schema_tab_sitem.click()
            time.sleep(2)
        else:
            print('Schema check not supported for the current package version \n')
        self.wait_for_ajax()

    def select_settings_tab(self, is_cluster, check=False):
        """Selecting settings tab from the collection submenu"""
        self.click_submenu_entry("Settings")
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
            print("Loading Index into memory\n")
            select_load_index_into_memory_sitem = self.locator_finder_by_xpath(self.select_load_index_into_memory_id)
            select_load_index_into_memory_sitem.click()
            time.sleep(2)
        self.wait_for_ajax()
    
    def ace_set_value(self, locator, query, check=False):
        """take a string and adjacent locator argument of ace-editor and execute the query"""
        # to unify ace_locator class attribute has been used
        ace_locator = self.locator_finder_by_class(locator)
        # Set x and y offset positions of adjacent element
        xOffset = 100
        yOffset = 100
        # Performs mouse move action onto the element
        actions = ActionChains(self.webdriver).move_to_element_with_offset(ace_locator, xOffset, yOffset)
        actions.click()
        actions.key_down(Keys.CONTROL).send_keys('a').send_keys(Keys.BACKSPACE).key_up(Keys.CONTROL)
        time.sleep(1)
        actions.send_keys(f'{query}')
        actions.perform()
        time.sleep(1)

        if check:
            print("Saving current computed value")
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

    def select_computedValueCol(self):
        """this method will select ComputedValueCol"""
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
        print("Selecting computed values collections. \n")
        if self.current_package_version() >= semver.VersionInfo.parse('3.11.99'):
            col = "//*[text()='ComputedValueCol']"
        else:
            col = '//*[@id="collection_ComputedValueCol"]/div/h5'
        self.locator_finder_by_xpath(col).click()
        time.sleep(1)

        print("Selecting computed value tab \n")
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
        self.ace_set_value(warning, compute_query, True)

        # print('go back to collection tab')
        self.navbar_goto("collections")
        self.select_computedValueCol()
        
        self.navigate_to_col_content_tab()

        # print('Select add new document to collection button')
        add = '//*[@id="addDocumentButton"]/span/i'
        add_sitem = self.locator_finder_by_xpath(add)
        add_sitem.click()

        # print('inserting data\n')
        insert_data = "jsoneditor-format"
        col_query = {"name": {"first": "Sam",
                              "last": "Smith"},
                     "address": "Hans-Sachs-Str",
                     "x": 12.9,
                     "y": -284.0}
        insert_query = json.dumps(col_query)
        self.ace_set_value(insert_data, insert_query)
        self.navbar_goto('queries')
        time.sleep(1)

        print('select query execution area\n')
        self.select_query_execution_area()
        print('sending query to the area\n')
        self.send_key_action('FOR user IN ComputedValueCol RETURN user')
        print('execute the query\n')
        self.query_execution_btn()
        self.scroll()

        print('Checking that dateCreatedHumanReadable computed value as been created\n')
        computed_value = "//*[text()='dateCreatedHumanReadable']"
        computed_value_sitem = self.locator_finder_by_xpath(computed_value).text
        time.sleep(1)
        computed_value = 'dateCreatedHumanReadable'
        try:
            assert computed_value == computed_value_sitem, \
                f"Expected page title {computed_value} but got {computed_value_sitem}"
        except AssertionError:
            print(f'Assertion Error occurred! for {computed_value}\n')

        print('Checking that FullName computed value as been created\n')
        computed_full_name = "//*[text()='FullName']"
        computed_full_name_sitem = self.locator_finder_by_xpath(computed_full_name).text
        time.sleep(1)
        full_name_value = 'FullName'
        try:
            assert full_name_value == computed_full_name_sitem, \
                f"Expected page title {computed_value} but got {computed_full_name_sitem}"
        except AssertionError:
            print(f'Assertion Error occurred! for {computed_value}\n')

        print('Checking that dateCreatedForIndexing computed value as been created\n')
        computed_index_value = "//*[text()='dateCreatedForIndexing']"
        computed_index_value_sitem = self.locator_finder_by_xpath(computed_index_value).text
        index_value = 'dateCreatedForIndexing'
        time.sleep(1)
        try:
            assert index_value == computed_index_value_sitem, \
                f"Expected page title {index_value} but got {computed_index_value_sitem}"
        except AssertionError:
            print(f'Assertion Error occurred! for {index_value}\n')

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
        delete_collection_sitem = self.locator_finder_by_xpath(self.delete_collection_id, expec_fail=expec_fail)
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
        """ select a collection """
        selector = """//div[contains(@class, 'tile')][@id='collection_%s']""" % collection_name
        self.locator_finder_by_xpath(selector).click()

    def delete_collection(self, collection_name, collection_locator, is_cluster):
        """This method will delete all the collection"""
        print(f"Deleting {collection_name} collection started \n")
        self.navbar_goto("collections")

        try:
            self.locator_finder_by_xpath(collection_locator).click()

            # we don't care about the cluster specific things:
            self.select_settings_tab(is_cluster)
            self.select_delete_collection()

            print(f"Deleting {collection_name} collection Completed \n")
            self.webdriver.refresh()
        except TimeoutException:
            print("TimeoutException occurred! \n")
            print("Info: Collection has already been deleted or never created. \n")
        except NoSuchElementException:
            print('Element not found, which might be happen due to force cleanup.')
        except Exception as ex:
            traceback.print_exc()
            raise Exception("Critical Error occurred and need manual inspection!! \n") from ex
        self.webdriver.refresh()

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
                print("FAIL: Unexpected error occurred!")

        except TimeoutException as ex:
            if test_name == "access":
                print("Collection creation failed, which is expected")
            if test_name == "read/write":
                raise Exception("FAIL: Unexpected error occurred!") from ex
