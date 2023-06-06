#!/usr/bin/env python3
""" collection testsuite """
import semver
import traceback
from selenium_ui_test.test_suites.base_selenium_test_suite import BaseSeleniumTestSuite
from test_suites_core.base_test_suite import testcase


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

        self.exception = False
        self.error = None

        try:
            col.create_new_collections('computedValueCol', 0, self.is_cluster)
            col.create_new_collections('TestDoc', 0, self.is_cluster)
            col.create_new_collections('TestEdge', 1, self.is_cluster)
            col.create_new_collections('Test', 0, self.is_cluster)
            col.create_new_collections('ComputedValueCol', 0, self.is_cluster)

            if col.current_package_version() >= semver.VersionInfo.parse("3.9.100"):
                col.test_computed_values()
            
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
            self.webdriver.refresh()
            col.select_edge_collection_upload()
            col.navigate_to_col_content_tab()
            print("Uploading file to the collection started\n")
            col.select_upload_btn()
            print("Uploading json file\n")
            col.select_choose_file_btn(str(self.test_data_dir / "ui_data" / "edges.json"))
            col.select_confirm_upload_btn()
            self.webdriver.refresh()
            print("Uploading " + col.getting_total_row_count() + " documents to the collection Completed\n")
            print("Selecting size of the displayed\n")

            self.webdriver.back()

            col.select_collection("TestDoc")
            col.navigate_to_col_content_tab()
            print("Uploading file to the collection started\n")
            col.select_upload_btn()
            print("Uploading json file\n")
            col.select_choose_file_btn(str(self.test_data_dir / "ui_data" / "names_100.json"))
            col.select_confirm_upload_btn()
            self.webdriver.refresh()
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
            
            if version >= semver.VersionInfo.parse("3.11.0"):
                col.create_index('Persistent')
                col.create_index('Geo')
                col.create_index('Fulltext')
                col.create_index('TTL')
                col.create_index('Inverted Index')
                col.create_index('ZKD')
            else:
                print("Cluster status: ", self.is_cluster)
                col.create_new_index("Persistent", 1, self.is_cluster)
                col.create_new_index("Geo", 2, self.is_cluster)
                col.create_new_index("Fulltext", 3, self.is_cluster)
                col.create_new_index("TTL", 4, self.is_cluster)
                
                if version >= semver.VersionInfo.parse("3.9.0"):
                    if version > semver.VersionInfo.parse("3.9.99"):
                        col.create_new_index('ZKD', 5, self.is_cluster, True)
                    else:
                        col.create_new_index('ZKD', 5, self.is_cluster)

                    print("Deleting all index started\n")
                    for i in range(4):
                        col.delete_all_index(True)
                    print("Deleting all index completed\n")
                else:
                    print("Deleting all index started\n")
                    collection = "collections"
                    collection_sitem = self.locator_finder_by_id(collection)
                    collection_sitem.click()

                    col.select_collection("TestDoc")
                    col.select_index_menu()
                    col.delete_index(2)
                    col.delete_index(3)
                    col.delete_index(4)
                    col.delete_index(5)
                    col.delete_index(7)
                    print("Deleting all index completed\n")

            print("Select Info tab\n")
            col.select_info_tab()
            # print("Selecting Schema Tab\n")
            # col.select_schema_tab()

            print("Select Settings tab\n")
            col.select_settings_tab(self.is_cluster, True)
            # some old bullshit
            # print("Loading and Unloading collection\n")
            # col.select_settings_unload_btn()
            # col.select_settings_unload_btn()
            self.webdriver.refresh()
            print("Truncate collection\n")
            col.select_truncate_btn()
            self.webdriver.refresh()
            print("---------Checking Collection Completed--------- \n")
        
        except BaseException:
            print('x' * 45, "\nINFO: Error Occurred! Force cleanup started\n", 'x' * 45)
            self.exception = True   # mark the exception as true
            self.error = traceback.format_exc()
        
        finally:
            # these will clearup the resources even in failed test case scenario
            print("Collection deletion started \n")
            col.delete_collection("TestDoc", col.select_doc_collection_id, self.is_cluster)          
            col.delete_collection("TestDocRenamed", col.select_renamed_doc_collection_id, self.is_cluster)
            col.delete_collection("TestEdge", col.select_edge_collection_id, self.is_cluster)
            col.delete_collection("Test", col.select_test_doc_collection_id, self.is_cluster)
            col.delete_collection("ComputedValueCol", col.select_computedValueCol_id, self.is_cluster)
            print("Deleting Collection completed\n")

            if self.exception:
                raise Exception(self.error)
            del col
