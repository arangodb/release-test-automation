#!/usr/bin/env python3
""" collection testsuite """
import semver
from selenium_ui_test.test_suites.base_selenium_test_suite import BaseSeleniumTestSuite
from selenium_ui_test.test_suites.base_test_suite import testcase


# from selenium_ui_test.models import IndexType
from selenium_ui_test.pages.collection_page import CollectionPage


class CollectionsTestSuite(BaseSeleniumTestSuite):
    """collection tab suite"""
    # pylint: disable=too-many-statements
    @testcase
    def test_collection(self):
        """testing collection page"""
        print("---------Checking Collection Begin--------- \n")
        # login = LoginPage(self.webdriver, self.cfg)
        # login.login('root', self.root_passvoid)
        col = CollectionPage(self.webdriver, self.cfg)  # creating obj for Collection
        assert col.current_user() == "ROOT", "current user is root?"
        assert col.current_database() == "_SYSTEM", "current database is _system?"

        print("Selecting collection tab\n")
        col.select_collection_page()

        print("Creating new collection started \n")
        col.select_create_collection()
        print("Creating Document collection \n")
        col.select_new_collection_name("TestDoc")
        print("Creating Document type collection started \n")
        col.select_collection_type(0)  # 0 for Doc type document

        if self.is_cluster:
            print("Selecting number of shards for the current collection \n")
            col.select_number_of_shards(9)  # it takes number of shards as an argument

            print("Selecting replication factor for the current collection \n")
            col.select_replication_factor(3)  # it takes number of replication factor as an argument

        col.select_advance_option()
        print("Choosing wait type to YES \n")
        col.wait_for_sync(1)
        col.create_new_collection_btn()
        print("Creating Document type collection completed \n")

        print("Creating Edge type collection\n")
        col.select_create_collection()
        col.select_new_collection_name("TestEdge")
        col.select_collection_type(1)  # 1 for Edge type document

        if self.is_cluster:
            print("Selecting number of shards for the current collection \n")
            col.select_number_of_shards(9)  # it takes number of shards as an argument

            print("Selecting replication factor for the current collection \n")
            col.select_replication_factor(3)  # it takes number of replication factor as an argument

        col.select_advance_option()
        print("Choosing wait type to YES \n")
        col.wait_for_sync(1)
        col.create_new_collection_btn()
        print("Creating new Edge collection completed \n")

        print("Creating new collection started \n")
        col.select_create_collection()
        print("Creating Document collection \n")
        col.select_new_collection_name("Test")
        print("Creating Document type collection started \n")
        col.select_collection_type(0)  # 0 for Doc type document

        if self.is_cluster:
            print("Selecting number of shards for the current collection \n")
            col.select_number_of_shards(9)  # it takes number of shards as an argument

            print("Selecting replication factor for the current collection \n")
            col.select_replication_factor(3)  # it takes number of replication factor as an argument

        col.select_advance_option()
        print("Choosing wait type to YES \n")
        col.wait_for_sync(1)
        col.create_new_collection_btn()
        print("Creating Document type collection completed \n")

        print("checking Search options\n")
        print("Searching using keyword 'Doc'\n")
        col.checking_search_options("Doc")
        self.webdriver.refresh()
        print("Searching using keyword 'Edge'\n")
        col.checking_search_options("Edge")
        self.webdriver.refresh()
        print("Searching using keyword 'test'\n")
        col.checking_search_options("Test")
        self.webdriver.refresh()

        print("Selecting Settings\n")
        col.select_collection_settings()
        print("Displaying system's collection\n")
        col.display_system_collection()
        col.display_system_collection()  # Doing the reverse part
        print("Displaying Document type collection\n")
        col.display_document_collection()
        col.display_document_collection()
        print("Displaying Edge type collection\n")
        col.display_edge_collection()
        col.display_edge_collection()
        print("Displaying status loaded collection\n")
        col.select_status_loaded()
        col.select_status_loaded()
        # todo: some old bullshit.
        # print("Displaying status unloaded collection\n")
        # col.select_status_unloaded()
        # col.select_status_unloaded()
        self.webdriver.refresh()
        print("Sorting collections by type\n")
        col.select_collection_settings()
        col.sort_by_type()
        print("Sorting collections by descending\n")
        col.sort_descending()
        col.sort_descending()
        print("Sorting collections by name\n")
        col.sort_by_name()

        col.select_edge_collection_upload()
        print("Uploading file to the collection started\n")
        col.select_upload_btn()
        print("Uploading json file\n")
        col.select_choose_file_btn(str(self.test_data_dir / "ui_data" / "edges.json"))
        col.select_confirm_upload_btn()
        self.webdriver.refresh()  # in order to clear the screen before fetching data
        print("Uploading " + col.getting_total_row_count() + " documents to the collection Completed\n")
        print("Selecting size of the displayed\n")

        self.webdriver.back()

        col.select_collection("TestDoc")
        print("Uploading file to the collection started\n")
        col.select_upload_btn()
        print("Uploading json file\n")
        col.select_choose_file_btn(str(self.test_data_dir / "ui_data" / "names_100.json"))
        col.select_confirm_upload_btn()
        self.webdriver.refresh()  # in order to clear the screen before fetching data
        print("Uploading " + col.getting_total_row_count() + " documents to the collection Completed\n")
        print("Selecting size of the displayed\n")

        # print("Downloading Documents as JSON file\n")
        # col.download_doc_as_json()

        print("Filter collection by '_id'\n")
        col.filter_documents(3)
        col.filter_documents(1)
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
        col.select_multiple_item()
        col.select_collection_delete_btn()
        col.collection_delete_confirm_btn()
        col.collection_really_dlt_btn()
        print("Deleting multiple data completed\n")

        print("Selecting Index menu\n")
        col.select_index_menu()

        print("Create new index\n")

        version = col.current_package_version()
        print(version, "\n")
        print("Cluster status: ", self.is_cluster)
        col.create_new_index("Persistent", 1, self.is_cluster)
        col.create_new_index("Geo", 2, self.is_cluster)
        col.create_new_index("Fulltext", 3, self.is_cluster)
        col.create_new_index("TTL", 4, self.is_cluster)
        if version >= semver.VersionInfo.parse("3.9.0"):
            col.create_new_index("ZKD", 5, self.is_cluster)
            print("Deleting all index started\n")
            for _ in range(4):
                col.delete_all_index()
            print("Deleting all index completed\n")
        else:
            print("Deleting all index started\n")
            for _ in range(3):
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
        # col.select_settings_unload_btn()
        self.webdriver.refresh()
        print("Truncate collection\n")
        col.select_truncate_btn()
        self.webdriver.refresh()
        # print("Deleting Collection started\n")
        # col.delete_collection()
        # #
        # print("Selecting TestEdge Collection for deleting\n")
        # col.select_edge_collection()
        # col.delete_collection()

        # print("Selecting Test Collection for deleting\n")
        # col.select_test_doc_collection()
        # col.delete_collection()
        # print("Deleting Collection completed\n")

        # these will clearup the resources even in failed test case scenario
        if self.is_cluster:
            col.delete_collection("TestDoc", col.select_doc_collection_id)
        else:
            col.delete_collection("TestDocRenamed", col.select_renamed_doc_collection_id)
        col.delete_collection("TestEdge", col.select_edge_collection_id)
        col.delete_collection("Test", col.select_test_doc_collection_id)

        del col
        # login.logout_button()
        # del login
        print("---------Checking Collection Completed--------- \n")
