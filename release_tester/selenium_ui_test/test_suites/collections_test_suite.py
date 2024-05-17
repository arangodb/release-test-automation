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
        self.tprint("---------Checking Collection Begin--------- \n")
        # login = LoginPage(self.webdriver, self.cfg, self.video_start_time)
        # login.login('root', self.root_passvoid)
        col = CollectionPage(self.webdriver, self.cfg, self.video_start_time)  # creating obj for Collection
        assert col.current_user() == "ROOT", "current user is root?"
        assert col.current_database() == "_SYSTEM", "current database is _system?"

        self.exception = False
        self.error = None

        try:
            col.create_new_collections('TestDoc', 0, self.is_cluster)
            col.create_new_collections('TestEdge', 0, self.is_cluster)
            col.create_new_collections('Test', 0, self.is_cluster)
            col.create_new_collections('ComputedValueCol', 0, self.is_cluster)

            if col.version_is_newer_than("3.9.99"):
                col.test_computed_values()

            self.tprint("checking Search options\n")
            if col.version_is_newer_than("3.11.99"):
                col.checking_search_options()
            else:
                self.tprint("Searching using keyword 'Doc'\n")
                col.checking_search_options("Doc")
                self.webdriver.refresh()
                self.tprint("Searching using keyword 'Edge'\n")
                col.checking_search_options("Edge")
                self.webdriver.refresh()
                self.tprint("Searching using keyword 'test'\n")
                col.checking_search_options("Test")
                self.webdriver.refresh()

            # basic collection page feature check for
            if col.version_is_newer_than("3.9.99"):
                col.select_collection_page()
                if col.version_is_newer_than("3.11.99"):
                    self.tprint("basic feature will be added later on!")
                else:
                    self.tprint("Selecting Settings\n")
                    col.select_collection_settings()
                    self.tprint("Displaying system's collection\n")
                    col.display_system_collection()
                    col.display_system_collection()  # Doing the reverse part
                    self.tprint("Displaying Document type collection\n")
                    col.display_document_collection()
                    col.display_document_collection()
                    self.tprint("Displaying Edge type collection\n")
                    col.display_edge_collection()
                    col.display_edge_collection()
                    self.tprint("Displaying status loaded collection\n")
                    col.select_status_loaded()
                    col.select_status_loaded()
                    # todo: some old bullshit.
                    # self.tprint("Displaying status unloaded collection\n")
                    # col.select_status_unloaded()
                    # col.select_status_unloaded()
                    self.webdriver.refresh()
                    self.tprint("Sorting collections by type\n")
                    col.select_collection_settings()
                    col.sort_by_type()
                    self.tprint("Sorting collections by descending\n")
                    col.sort_descending()
                    col.sort_descending()
                    self.tprint("Sorting collections by name\n")
                    col.sort_by_name()
                    self.webdriver.refresh()
                    col.select_edge_collection_upload()
                    col.navigate_to_col_content_tab()
                    self.tprint("Uploading file to the collection started\n")
                    col.select_upload_btn()
                    self.tprint("Uploading json file\n")
                    col.select_choose_file_btn(str(self.ui_data_dir / "ui_data" / "edges.json"))
                    col.select_confirm_upload_btn()
                    self.webdriver.refresh()
                    self.tprint("Uploading " + col.getting_total_row_count() + " documents to the collection Completed\n")
                    self.tprint("Selecting size of the displayed\n")

                    col.select_collection_page()

                    col.select_collection("TestDoc")
                    col.navigate_to_col_content_tab()
                    self.tprint("Uploading file to the collection started\n")
                    col.select_upload_btn()
                    self.tprint("Uploading json file\n")
                    col.select_choose_file_btn(str(self.ui_data_dir / "ui_data" / "names_100.json"))
                    col.select_confirm_upload_btn()
                    self.webdriver.refresh()
                    self.tprint("Uploading " + col.getting_total_row_count() + " documents to the collection Completed\n")
                    self.tprint("Selecting size of the displayed\n")

                    # self.tprint("Downloading Documents as JSON file\n")
                    # col.download_doc_as_json()

                    self.tprint("Filter collection by '_id'\n")
                    col.filter_documents(3)
                    col.filter_documents(1)
                    col.display_document_size(2)  # choosing 50 results to display
                    self.tprint("Traverse back and forth search result page 1 and 2\n")
                    col.traverse_search_pages()
                    self.tprint("Selecting hand selection button\n")
                    col.select_hand_pointer()
                    self.tprint("Select Multiple item using hand pointer\n")
                    col.select_multiple_item()
                    col.move_btn()
                    self.tprint("Multiple data moving into test collection\n")
                    col.move_doc_textbox("Test")
                    col.move_confirm_btn()

                    self.tprint("Deleting multiple data started\n")
                    col.select_multiple_item()
                    col.select_collection_delete_btn()
                    col.collection_delete_confirm_btn()
                    col.collection_really_dlt_btn()
                    self.tprint("Deleting multiple data completed\n")

                col.select_collection_page()
                col.select_doc_collection()
                self.tprint("Selecting Index menu\n")
                col.select_index_menu()

                self.tprint("Create new index\n")
                version = col.current_package_version()

                if col.version_is_newer_than("3.11.0"):
                    col.create_index('Persistent')
                    col.create_index('Geo')
                    col.create_index('Fulltext')
                    col.create_index('TTL')
                    col.create_index('Inverted Index')
                    if version >= semver.VersionInfo.parse("3.11.99"):
                        col.create_index('MDI')
                else:
                    self.tprint(f"Cluster status: {self.is_cluster}")
                    col.create_new_index("Persistent", 1, self.is_cluster)
                    col.create_new_index("Geo", 2, self.is_cluster)
                    col.create_new_index("Fulltext", 3, self.is_cluster)
                    col.create_new_index("TTL", 4, self.is_cluster)

                if col.version_is_older_than("3.10.99"):
                    if col.version_is_newer_than("3.9.99"):
                        col.create_new_index('ZKD', 5, self.is_cluster, True)
                    else:
                        col.create_new_index('ZKD', 5, self.is_cluster)

                    self.tprint("Deleting all index started for < v3.11.x\n")
                    for i in range(4):
                        col.delete_index_311(True)
                    self.tprint("Deleting all index completed\n")
                else:
                    self.tprint("Deleting all index started for > v3.11.x\n")
                    col.select_collection_page()
                    # col.select_collection("TestDoc")
                    col.select_doc_collection()
                    col.select_index_menu()
                    for index in range(4):
                        col.delete_index_312(index)
                    self.tprint("Deleting all index completed\n")

                if col.version_is_newer_than("3.11.99"):
                    self.tprint("basic feature will be added later on!")
                else:
                    self.tprint("Select Info tab\n")
                    col.select_info_tab()
                    # self.tprint("Selecting Schema Tab\n")
                    # col.select_schema_tab()

                    self.tprint("Select Settings tab\n")
                    col.select_settings_tab(self.is_cluster, True)
                    self.webdriver.refresh()
                    self.tprint("Truncate collection\n")
                    col.select_truncate_btn()
                    self.webdriver.refresh()
            self.tprint("---------Checking Collection Completed--------- \n")

        except BaseException:
            self.tprint(f"{'x' * 45}\nINFO: Error Occurred! Force cleanup started\n{ 'x' * 45}")
            self.exception = True   # mark the exception as true
            self.error = traceback.format_exc()

        finally:
            # these will clearup the resources even in failed test case scenario
            self.tprint("Collection deletion started \n")
            col.delete_collection("TestDoc", col.select_doc_collection_id, self.is_cluster)          
            col.delete_collection("TestDocRenamed", col.select_renamed_doc_collection_id, self.is_cluster)
            col.delete_collection("TestEdge", col.select_edge_collection_id, self.is_cluster)
            col.delete_collection("Test", col.select_test_doc_collection_id, self.is_cluster)
            col.delete_collection("ComputedValueCol", col.select_computedValueCol_id, self.is_cluster)
            self.tprint("Deleting Collection completed\n")

            if self.exception:
                raise Exception(self.error)
            del col
