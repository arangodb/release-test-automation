from selenium_ui_test.test_suites.base_test_suite import BaseTestSuite, testcase
from selenium_ui_test.models import IndexType
from selenium_ui_test.pages.collection_page import CollectionPage


class CollectionsTestSuite(BaseTestSuite):
    @testcase
    def test_collection(self):
        """testing collection page"""
        print("---------Checking Collection Begin--------- \n")
        # login = LoginPage(self.webdriver)
        # login.login('root', self.root_passvoid)
        col = CollectionPage(self.webdriver)  # creating obj for Collection
        col1 = CollectionPage(self.webdriver)
        col2 = CollectionPage(self.webdriver)
        col3 = CollectionPage(self.webdriver)

        print("Selecting collection tab\n")
        col.select_collection_page()

        print("Creating new collection started \n")
        col.select_create_collection()
        print("Creating Document collection \n")
        col.select_new_collection_name("TestDoc")
        print("Creating Document type collection started \n")
        col.select_collection_type(0)  # 0 for Doc type document
        col.select_advance_option()
        print("Choosing wait type to YES \n")
        col.wait_for_sync(1)
        col.create_new_collection_btn()
        print("Creating Document type collection completed \n")

        print("Creating Edge type collection\n")
        col1.select_create_collection()
        col1.select_new_collection_name("TestEdge")
        col1.select_collection_type(1)  # 1 for Edge type document
        col1.select_advance_option()
        print("Choosing wait type to YES \n")
        col1.wait_for_sync(1)
        col1.create_new_collection_btn()
        print("Creating new Edge collection completed \n")

        print("Creating new collection started \n")
        col2.select_create_collection()
        print("Creating Document collection \n")
        col2.select_new_collection_name("Test")
        print("Creating Document type collection started \n")
        col2.select_collection_type(0)  # 0 for Doc type document
        col2.select_advance_option()
        print("Choosing wait type to YES \n")
        col2.wait_for_sync(1)
        col2.create_new_collection_btn()
        print("Creating Document type collection completed \n")

        print("checking Search options\n")
        print("Searching using keyword 'Doc'\n")
        col.checking_search_options("Doc")
        self.webdriver.refresh()
        print("Searching using keyword 'Edge'\n")
        col1.checking_search_options("Edge")
        self.webdriver.refresh()
        print("Searching using keyword 'test'\n")
        col2.checking_search_options("Test")
        self.webdriver.refresh()

        print("Selecting Settings\n")
        col.select_collection_settings()
        print("Displaying system's collection\n")
        col.display_system_collection()
        col1.display_system_collection()  # Doing the reverse part
        print("Displaying Document type collection\n")
        col.display_document_collection()
        col1.display_document_collection()
        print("Displaying Edge type collection\n")
        col.display_edge_collection()
        col1.display_edge_collection()
        print("Displaying status loaded collection\n")
        col.select_status_loaded()
        col1.select_status_loaded()
        # todo: some old bullshit.
        # print("Displaying status unloaded collection\n")
        # col.select_status_unloaded()
        # col1.select_status_unloaded()
        self.webdriver.refresh()
        print("Sorting collections by type\n")
        col.select_collection_settings()
        col.sort_by_type()
        print("Sorting collections by descending\n")
        col.sort_descending()
        col1.sort_descending()
        print("Sorting collections by name\n")
        col.sort_by_name()

        col1.select_edge_collection_upload()
        print("Uploading file to the collection started\n")
        col1.select_upload_btn()
        print("Uploading json file\n")
        col1.select_choose_file_btn(str(self.test_data_dir / "ui_data" / "edges.json"))
        col1.select_confirm_upload_btn()
        self.webdriver.refresh()  # in order to clear the screen before fetching data
        print("Uploading " + col1.getting_total_row_count() + " to the collection Completed\n")
        print("Selecting size of the displayed\n")

        self.webdriver.back()

        col.select_collection("TestDoc")
        print("Uploading file to the collection started\n")
        col.select_upload_btn()
        print("Uploading json file\n")
        col.select_choose_file_btn(str(self.test_data_dir / "ui_data" / "names_100.json"))
        col.select_confirm_upload_btn()
        self.webdriver.refresh()  # in order to clear the screen before fetching data
        print("Uploading " + col.getting_total_row_count() + " to the collection Completed\n")
        print("Selecting size of the displayed\n")

        # print("Downloading Documents as JSON file\n")
        # col.download_doc_as_json()

        print("Filter collection by '_id'\n")
        col.filter_documents(3)
        col1.filter_documents(1)
        col.display_document_size(2)  # choosing 50 results to display
        print("Traverse back and forth search result page 1 and 2\n")
        col.traverse_search_pages()
        print("Selecting hand selection button\n")
        col.select_hand_pointer()
        print("Select Multiple item using hand pointer\n")
        col.select_multiple_item()
        col.move_btn()
        print("Multiple data moving into test collection\n")
        col.move_doc_textbox("Test")
        col.move_confirm_btn()

        print("Deleting multiple data started\n")
        col1.select_multiple_item()
        col.select_collection_delete_btn()
        col.collection_delete_confirm_btn()
        col.collection_really_dlt_btn()
        print("Deleting multiple data completed\n")

        print("Selecting Index menu\n")
        col.select_index_menu()

        print("Create new index\n")
        # col.create_new_index_btn()

        # print("Creating Geo Index Started\n")
        # col.select_index_type(IndexType.GEO.value)
        # print("filling up all necessary info for geo index\n")
        # col.creating_geo_index()
        # print("Creating new geo index\n")
        # col.select_create_index_btn()
        # print("Creating Geo Index completed\n")

        # print("Creating Persistent Index Started\n")
        # col1.create_new_index_btn()
        # col1.select_index_type(IndexType.PERSISTENT.value)
        # print("filling up all necessary info for  persistent index\n")
        # col1.creating_persistent_index()
        # print("Creating new persistent index\n")
        # col1.select_create_index_btn()
        # print("Creating Persistent Index Completed\n")

        # print("Creating Fulltext Index Started\n")
        # col2.create_new_index_btn()
        # col2.select_index_type(IndexType.FULLTEXT.value)
        # col2.creating_fulltext_index()
        # col2.select_create_index_btn()
        # print("Creating Fulltext Index Completed\n")

        # print("Creating TTL Index Started\n")
        # col3.create_new_index_btn()
        # col3.select_index_type(IndexType.TTL.value)
        # col3.creating_ttl_index()
        # col3.select_create_index_btn()
        # print("Creating TTL Index Completed\n")

        # print("Deleting all index started\n")
        # col.delete_all_index()
        # col1.delete_all_index()
        # col2.delete_all_index()
        # col3.delete_all_index()
        # print("Deleting all index completed\n")

        version = self.current_package_version(self)
        col.create_new_index("Persistent", 1)
        col.create_new_index("Geo", 2)
        col.create_new_index("Fulltext", 3)
        col.create_new_index("TTL", 4)
        if version == 3.9:
            col.create_new_index("ZKD", 5)
            print("Deleting all index started\n")
            for i in range(4):
                col.delete_all_index()
            print("Deleting all index completed\n")
        else:
            print("Deleting all index started\n")
            for i in range(3):
                col.delete_all_index()
            print("Deleting all index completed\n")

        print("Select Info tab\n")
        col.select_info_tab()
        print("Selecting Schema Tab\n")
        # col.select_schema_tab()

        print("Select Settings tab\n")
        col.select_settings_tab(self.is_cluster)
        self.webdriver.refresh()
        # some old bullshit
        # print("Loading and Unloading collection\n")
        # col.select_settings_unload_btn()
        # col1.select_settings_unload_btn()
        self.webdriver.refresh()
        print("Truncate collection\n")
        col.select_truncate_btn()
        self.webdriver.refresh()
        print("Deleting Collection started\n")
        col.delete_collection()
        #
        print("Selecting TestEdge Collection for deleting\n")
        col2.select_edge_collection()
        col2.delete_collection()

        print("Selecting Test Collection for deleting\n")
        col3.select_test_doc_collection()
        col3.delete_collection()
        print("Deleting Collection completed\n")

        del col
        del col1
        del col2
        del col3
        # login.logout_button()
        # del login
        print("---------Checking Collection Completed--------- \n")
