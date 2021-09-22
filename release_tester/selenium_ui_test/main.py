#!/usr/bin/env python
"""
main entrance point for the UI tests
"""
#import time

import traceback
from selenium_ui_test.pages.dashboard_page import DashboardPage
from selenium_ui_test.pages.login_page import LoginPage
from selenium_ui_test.pages.user_page import UserPage
from selenium_ui_test.pages.views_page import ViewsPage
from selenium_ui_test.pages.collection_page import CollectionPage
from selenium_ui_test.pages.graph_page import GraphPage, GraphExample, get_graph_name
from selenium_ui_test.pages.query_page import QueryPage
from selenium_ui_test.pages.support_page import SupportPage
from selenium_ui_test.pages.databasePage import DatabasePage
from selenium_ui_test.pages.analyzersPage import AnalyzerPage

# can't circumvent long lines.. nAttr nLines
# pylint: disable=C0301 disable=R0902 disable=R0915
from selenium_ui_test.models import IndexType

from selenium_ui_test.models import RtaUiTestResult


class BaseTest():
    """base class for UI tests"""
    def __init__(self, root_passvoid, url, selenium_driver):
        """initial web driver setup"""
        self.driver = selenium_driver
        self.root_passvoid = root_passvoid
        self.url = url
        self.test_results = []

    def testcase(title):
        def decorator(func):
            def wrapper(self, *args, **kwargs):
                name = None
                success = None
                message = None
                tb = None
                if not callable(title):
                    name = title
                elif title.__doc__:
                    name = title.__doc__
                else:
                    name = title.__name__
                try:
                    print("Running test case \"%s\"..." % name)
                    func(self, *args, **kwargs)
                    success = True
                    print("Test case \"%s\" passed!" % name)
                except Exception as e:
                    success = False
                    print("Test failed!")
                    message = str(e)
                    tb = "".join(traceback.TracebackException.from_exception(e).format())
                    print("Message: %s" % message)
                    print("Traceback: %s" % tb)
                test_result = RtaUiTestResult(name, success, message, tb)
                self.test_results.append(test_result)
            return wrapper
        if callable(title):
            return decorator(title)
        else:
            return decorator


    @testcase
    def test_login(self):
        """testing login page"""
        print("Starting ", self.driver.title, "\n")
        login = LoginPage(self.driver)
        login.login('root', self.root_passvoid)
        login.logout_button()


    @testcase
    def test_dashboard(self, is_enterprise, is_cluster):
        """testing dashboard page"""
        print("---------Checking Dashboard started--------- \n")
        #login = LoginPage(self.driver)
        #login.login('root', self.root_passvoid)
        # creating object for dashboard
        dash = DashboardPage(self.driver, is_enterprise)
        dash.navbar_goto('cluster' if is_cluster else 'dashboard')
        dash.check_server_package_name()
        dash.check_current_package_version()
        dash.check_current_username()
        dash.check_current_db()
        dash.check_db_status()
        # only 3.6 & 3.7 only support mmfiles... dash.check_db_engine()
        if not is_cluster:
            dash.check_db_uptime()
            # TODO: version dependend? cluster?
            dash.check_responsiveness_for_dashboard()
            print("\nSwitch to System Resource tab\n")
            dash.check_system_resource()
            print("Switch to Metrics tab\n")
            dash.check_system_metrics()
        dash.navbar_goto('support')
        print("Opening Twitter link \n")
        dash.click_twitter_link()
        print("Opening Slack link \n")
        dash.click_slack_link()
        print("Opening Stackoverflow link \n")
        dash.click_stackoverflow_link()
        print("Opening Google group link \n")
        dash.click_google_group_link()
        dash.click_google_group_link()
        #login.logout_button()
        print("---------Checking Dashboard Completed--------- \n")


    @testcase
    def test_collection(self, testdata_path, is_cluster):
        """testing collection page"""
        print("---------Checking Collection Begin--------- \n")
        #login = LoginPage(self.driver)
        #login.login('root', self.root_passvoid)
        col = CollectionPage(self.driver)  # creating obj for Collection
        col1 = CollectionPage(self.driver)
        col2 = CollectionPage(self.driver)
        col3 = CollectionPage(self.driver)

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
        self.driver.refresh()
        print("Searching using keyword 'Edge'\n")
        col1.checking_search_options("Edge")
        self.driver.refresh()
        print("Searching using keyword 'test'\n")
        col2.checking_search_options("Test")
        self.driver.refresh()

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
        #print("Displaying status unloaded collection\n")
        #col.select_status_unloaded()
        #col1.select_status_unloaded()
        self.driver.refresh()
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
        col1.select_choose_file_btn(str(testdata_path / 'ui_data' / 'edges.json'))
        col1.select_confirm_upload_btn()
        self.driver.refresh()  # in order to clear the screen before fetching data
        print("Uploading " + col1.getting_total_row_count() + " to the collection Completed\n")
        print("Selecting size of the displayed\n")

        self.driver.back()

        col.select_collection("TestDoc")
        print("Uploading file to the collection started\n")
        col.select_upload_btn()
        print("Uploading json file\n")
        col.select_choose_file_btn(str(testdata_path / 'ui_data' / 'names_100.json'))
        col.select_confirm_upload_btn()
        self.driver.refresh()  # in order to clear the screen before fetching data
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
        col.move_doc_textbox('Test')
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
        col.create_new_index_btn()

        print("Creating Geo Index Started\n")
        col.select_index_type(IndexType.GEO.value)
        print("filling up all necessary info for geo index\n")
        col.creating_geo_index()
        print("Creating new geo index\n")
        col.select_create_index_btn()
        print("Creating Geo Index completed\n")

        print("Creating Persistent Index Started\n")
        col1.create_new_index_btn()
        col1.select_index_type(IndexType.PERSISTENT.value)
        print("filling up all necessary info for  persistent index\n")
        col1.creating_persistent_index()
        print("Creating new persistent index\n")
        col1.select_create_index_btn()
        print("Creating Persistent Index Completed\n")

        print("Creating Fulltext Index Started\n")
        col2.create_new_index_btn()
        col2.select_index_type(IndexType.FULLTEXT.value)
        col2.creating_fulltext_index()
        col2.select_create_index_btn()
        print("Creating Fulltext Index Completed\n")

        print("Creating TTL Index Started\n")
        col3.create_new_index_btn()
        col3.select_index_type(IndexType.TTL.value)
        col3.creating_ttl_index()
        col3.select_create_index_btn()
        print("Creating TTL Index Completed\n")

        print("Deleting all index started\n")
        col.delete_all_index()
        col1.delete_all_index()
        col2.delete_all_index()
        col3.delete_all_index()
        print("Deleting all index completed\n")

        print("Select Info tab\n")
        col.select_info_tab()
        print("Selecting Schema Tab\n")
        # col.select_schema_tab()

        print("Select Settings tab\n")
        col.select_settings_tab(is_cluster)
        self.driver.refresh()
        # some old bullshit
        #print("Loading and Unloading collection\n")
        #col.select_settings_unload_btn()
        #col1.select_settings_unload_btn()
        self.driver.refresh()
        print("Truncate collection\n")
        col.select_truncate_btn()
        self.driver.refresh()
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
        #login.logout_button()
        #del login
        print("---------Checking Collection Completed--------- \n")


    @testcase
    def test_database(self):
        """testing database page"""
        print("---------DataBase Page Test Begin--------- \n")
        # login = LoginPage(self.driver)
        # login.login('root', '')

        user = UserPage(self.driver)
        user.user_tab()
        user.add_new_user('tester')
        user.add_new_user('tester01')

        db = DatabasePage(self.driver)
        db.create_new_db('Sharded', 0)  # 0 = sharded DB
        db.create_new_db('OneShard', 1)  # 1 = one shard DB

        db.test_database_expected_error()  # testing expected error condition for database creation

        print('Checking sorting databases to ascending and descending \n')
        db.sorting_db()

        print('Checking search database functionality \n')
        db.searching_db('Sharded')
        db.searching_db('OneShard')

        db.Deleting_database('Sharded')
        db.Deleting_database('OneShard')

        # login.logout_button()
        del user
        del db
        print("---------DataBase Page Test Completed--------- \n")


    @testcase
    def test_analyzers(self):
        print("---------Analyzers Page Test Begin--------- \n")
        # login = LoginPage(self.driver)
        # login.login('root', '')
        analyzers = AnalyzerPage(self.driver)
        analyzers.select_analyzers_page()
        analyzers.select_help_filter_btn()

        print('Showing in-built Analyzers list \n')
        analyzers.select_built_in_analyzers_open()

        print('Checking in-built identity analyzer \n')
        analyzers.select_analyzer_to_check(analyzers.identity_analyzer, analyzers.identity_analyzer_switch_view,
                                           analyzers.close_identity_btn)
        print('Checking in-built text_de analyzer \n')
        analyzers.select_analyzer_to_check(analyzers.text_de, analyzers.text_de_switch_view,
                                           analyzers.close_text_de_btn)
        print('Checking in-built text_en analyzer \n')
        analyzers.select_analyzer_to_check(analyzers.text_en, analyzers.text_en_switch_view,
                                           analyzers.close_text_en_btn)
        print('Checking in-built text_es analyzer \n')
        analyzers.select_analyzer_to_check(analyzers.text_es, analyzers.text_es_switch_view,
                                           analyzers.close_text_es_btn)
        print('Checking in-built text_fi analyzer \n')
        analyzers.select_analyzer_to_check(analyzers.text_fi, analyzers.text_fi_switch_view,
                                           analyzers.close_text_fi_btn)
        print('Checking in-built text_fr analyzer \n')
        analyzers.select_analyzer_to_check(analyzers.text_fr, analyzers.text_fr_switch_view,
                                           analyzers.close_text_fr_btn)
        print('Checking in-built text_it analyzer \n')
        analyzers.select_analyzer_to_check(analyzers.text_it, analyzers.text_it_switch_view,
                                           analyzers.close_text_it_btn)
        print('Checking in-built text_nl analyzer \n')
        analyzers.select_analyzer_to_check(analyzers.text_nl, analyzers.text_nl_switch_view,
                                           analyzers.close_text_nl_btn)
        print('Checking in-built text_no analyzer \n')
        analyzers.select_analyzer_to_check(analyzers.text_no, analyzers.text_no_switch_view,
                                           analyzers.close_text_no_btn)
        print('Checking in-built text_pt analyzer \n')
        analyzers.select_analyzer_to_check(analyzers.text_pt, analyzers.text_pt_switch_view,
                                           analyzers.close_text_pt_btn)
        print('Checking in-built text_ru analyzer \n')
        analyzers.select_analyzer_to_check(analyzers.text_ru, analyzers.text_ru_switch_view,
                                           analyzers.close_text_ru_btn)
        print('Checking in-built text_sv analyzer \n')
        analyzers.select_analyzer_to_check(analyzers.text_sv, analyzers.text_sv_switch_view,
                                           analyzers.close_text_sv_btn)
        print('Checking in-built text_zh analyzer \n')
        analyzers.select_analyzer_to_check(analyzers.text_zh, analyzers.text_zh_switch_view,
                                           analyzers.close_text_zh_btn)

        print('Hiding in-built Analyzers list \n')
        analyzers.select_built_in_analyzers_close()

        print('Adding Identity analyzer \n')
        analyzers.add_new_analyzer('My_Identity_Analyzer', 0)

        print('Adding Delimiter analyzer \n')
        analyzers.add_new_analyzer('My_Delimiter_Analyzer', 1)

        print('Adding Stem analyzer \n')
        analyzers.add_new_analyzer('My_Stem_Analyzer', 2)

        print('Adding Norm analyzer \n')
        analyzers.add_new_analyzer('My_Norm_Analyzer', 3)

        print('Adding N-Gram analyzer \n')
        analyzers.add_new_analyzer('My_N-Gram_Analyzer', 4)

        print('Adding Text analyzer \n')
        analyzers.add_new_analyzer('My_Text_Analyzer', 5)

        # login.logout_button()
        # del login
        del analyzers
        print("---------Analyzers Page Test Completed--------- \n")


    @testcase
    def test_views(self, is_cluster):
        """testing Views page"""
        print("---------Checking Views Begin--------- \n")
        #login = LoginPage(self.driver)
        #login.login('root', self.root_passvoid)
        views = ViewsPage(self.driver)  # creating obj for viewPage
        views1 = ViewsPage(self.driver)  # creating 2nd obj for viewPage to do counter part of the testing

        print("Selecting Views tab\n")
        views.select_views_tab()
        print("Creating first views\n")
        views.create_new_views()
        views.naming_new_view("firstView")
        views.select_create_btn()
        print("Creating first views completed\n")

        print("Creating second views\n")
        views1.create_new_views()
        views1.naming_new_view("secondView")
        views1.select_create_btn()
        print("Creating second views completed\n")

        views.select_views_settings()
        print("Sorting views to descending\n")
        views.select_sorting_views()

        print("Sorting views to ascending\n")
        views1.select_sorting_views()

        print("search views option testing\n")
        views1.search_views("se")
        views.search_views("fi")

        print("Selecting first Views \n")
        views.select_first_view()
        print("Selecting collapse button \n")
        views.select_collapse_btn()
        print("Selecting expand button \n")
        views.select_expand_btn()
        print("Selecting editor mode \n")
        views.select_editor_mode_btn()
        print("Switch editor mode to Code \n")
        views.switch_to_code_editor_mode()
        print("Switch editor mode to Compact mode Code \n")
        views.compact_json_data()

        print("Selecting editor mode \n")
        views1.select_editor_mode_btn()
        print("Switch editor mode to Tree \n")
        views1.switch_to_tree_editor_mode()

        print("Clicking on ArangoSearch documentation link \n")
        views.click_arangosearch_documentation_link()
        print("Selecting search option\n")
        views.select_inside_search("i")
        print("Traversing all results up and down \n")
        views.search_result_traverse_down()
        views.search_result_traverse_up()
        views1.select_inside_search("")
        # ###print("Changing views consolidationPolicy id to 55555555 \n")
        # ###views1.change_consolidation_policy(55555555)
        if not is_cluster:
            print("Rename firstViews to thirdViews started \n")
            views.clicking_rename_views_btn()
            views.rename_views_name("thirdView")
            views.rename_views_name_confirm()
            print("Rename the current Views completed \n")
            self.driver.back()
            print("Deleting views started \n")
            views.select_renamed_view()
        else:
            print("Deleting views started \n")
            views.select_views_tab()
            views.select_first_view()
        views.delete_views_btn()
        views.delete_views_confirm_btn()
        views.final_delete_confirmation()

        views1.select_second_view()
        views1.delete_views_btn()
        views1.delete_views_confirm_btn()
        views1.final_delete_confirmation()
        print("Deleting views completed\n")
        #login.logout_button()
        #del login
        del views
        del views1
        print("---------Checking Views completed--------- \n")


    @testcase
    def test_graph(self, cfg, importer, test_data_dir):
        """testing graph page"""
        print("---------Checking Graphs started--------- \n")
        #login = LoginPage(self.driver)
        #login.login('root', self.root_passvoid)

        # creating multiple graph obj
        #print('z'*80)
        this_graph = GraphPage(self.driver)
        print("Manual Graph creation started \n")

        this_graph.select_graph_page()
        #print("Creating '%s' Graph"%get_graph_name(GraphExample.MANUAL_KNOWS))
        #this_graph.create_graph(GraphExample.MANUAL_KNOWS, importer, test_data_dir)
        #print("Manual Graph creation completed \n")
        #this_graph.delete_graph(GraphExample.MANUAL_KNOWS)
        #self.driver.refresh()
        #
        #if cfg.enterprise:
        #    print("Adding Satellite Graph started \n")
        #    this_graph.create_graph(GraphExample.MANUAL_SATELITE_GRAPH, importer, test_data_dir)
        #    print("Adding Satellite Graph started \n")
        #
        #    print("Adding Smart Graph started \n")
        #    this_graph.create_graph(GraphExample.MANUAL_SMART_GRAHP, importer, test_data_dir)
        #    print("Adding Smart Graph completed \n")
        #
        #    print("Adding Disjoint Smart Graph started \n")
        #    this_graph.create_graph(GraphExample.MANUAL_DISJOINT_SMART_GRAHP, importer, test_data_dir)
        #    print("Adding Disjoint Smart Graph completed \n")

        print("Example Graphs creation started\n")
        for graph in GraphExample:
            #if graph == GraphExample.MANUAL_KNOWS:
            #    break
            this_graph.navbar_goto('graphs')
            print(graph)
            print("Creating '%s' Graph"%get_graph_name(graph))
            this_graph.create_graph(graph, importer, test_data_dir)
            this_graph.check_required_collections(graph)

        this_graph.select_graph_page()

        print("Example Graphs creation Completed\n")

        print("Sorting all graphs as descending\n")
        this_graph.select_sort_descend()

        print("Selecting Knows Graph for inspection\n")
        this_graph.inspect_knows_graph()
        # print("Selecting Graphs settings menu\n")
        #this_graph.graph_setting()

        print("Deleting created Graphs started\n")
        for graph in GraphExample:
            #if graph == GraphExample.MANUAL_KNOWS:
            #    break
            this_graph.navbar_goto('graphs')
            this_graph.delete_graph(graph)
        print("Deleting created Graphs Completed\n")
        #login.logout_button()
        #del login
        print("---------Checking Graphs completed--------- \n")


    @testcase
    def test_user(self, cfg, root_passvoid):
        """testing user page"""
        print("---------User Test Begin--------- \n")
        login = LoginPage(self.driver)
        # login.login('root', self.root_passvoid)
        self.driver.refresh()
        user = UserPage(self.driver)
        print("New user creation begins \n")
        user.user_tab()
        user.add_new_user('tester')

        print("Allow user Read Only access only to the _system DB test started \n")
        user.selecting_user_tester()
        user.selecting_permission_tab()
        print("Changing new user DB permission \n")
        user.changing_db_permission_read_only()
        user.selecting_general_tab()
        user.saving_user_cfg()
        print("Changing new user DB permission completed. \n")
        login.logout_button()
        print("Re-Login begins with new user\n")
        login.login_webif(cfg, 'tester', 'tester')
        print("Re-Login begins with new user completed\n")

        print("trying to create collection")
        user.create_sample_collection('access')
        print("Allow user Read Only access only to the current DB test completed \n")

        print("Allow user Read/Write access to the _system DB test started \n")
        print('Return back to user tab \n')

        # logout from the current user to get back to root
        login.logout_button()
        # login back with root user
        login.login_webif(cfg, 'root', root_passvoid)

        user.user_tab()
        user.selecting_user_tester()
        user.selecting_permission_tab()
        user.changing_db_permission_read_write()
        user.selecting_general_tab()
        user.saving_user_cfg()
        login.logout_button()
        print("Re-Login begins with new user\n")
        login.login_webif(cfg, 'tester', 'tester')
        print("Re-Login begins with new user completed\n")
        print("trying to create collection")
        user.create_sample_collection('read/write')
        print("Allow user Read/Write access to the _system DB test Completed \n")

        # logout from the current user to get back to root
        login.logout_button()
        login.login_webif(cfg, 'root', root_passvoid)

        del user
        self.driver.refresh()
        user = UserPage(self.driver)
        user.user_tab()
        user.selecting_new_user()
        print("Deleting created user begins\n")
        user.delete_user_btn()
        user.confirm_delete_btn()
        print("Deleting created user completed \n")
        print("---------User Test Completed---------\n")


    @testcase
    def test_query(self, cfg, is_cluster, restore, importer, test_data_dir):
        """testing query page"""
        print("---------Query Test Begin--------- \n")
        #login = LoginPage(self.driver)
        #login.login('root', self.root_passvoid)

        # creating multiple query obj
        query = QueryPage(self.driver)
        query01 = QueryPage(self.driver)
        this_graph = GraphPage(self.driver)

        print("Importing IMDB collections \n")
        query.import_collections(restore, test_data_dir, is_cluster)

        print("Selecting Query page for basic CRUD operation \n")
        query.selecting_query_page()

        print("Executing insert query \n")
        query.execute_insert_query()

        print("Profiling current query \n")
        query.profile_query()
        print("Explaining current query \n")
        query.explain_query()
        print("Debug packaged downloading for the current query \n")
        query.debug_package_download()
        print("Removing all query results \n")
        query.remove_query_result()

        # TODO: print("Executing spot light functionality \n")
        #query.spot_light_function('COUNT')  # can be used for search different keyword

        print('Executing read query\n')
        query01.execute_read_query()

        print('Updating documents\n')
        query.update_documents()
        print('Executing query with bind parameters \n')
        query.bind_parameters_query()

        print("Executing example graph query \n")
        graph = GraphExample.WORLD
        query.navbar_goto('graphs')
        print("Creating '%s' Graph"%get_graph_name(graph))
        this_graph.create_graph(graph, importer, test_data_dir)
        this_graph.check_required_collections(graph)
        query.world_country_graph_query()
        query.navbar_goto('graphs')
        this_graph.delete_graph(graph)
        self.driver.refresh()

        graph = GraphExample.K_SHORTEST_PATH
        query.navbar_goto('graphs')
        print("Creating '%s' Graph"%get_graph_name(graph))
        this_graph.create_graph(graph, importer, test_data_dir)
        this_graph.check_required_collections(graph)
        query.k_shortest_paths_graph_query()
        query.navbar_goto('graphs')
        this_graph.delete_graph(graph)
        self.driver.refresh()

        graph = GraphExample.CITY
        this_graph.navbar_goto('graphs')
        print("Creating '%s' Graph"%get_graph_name(graph))
        this_graph.create_graph(graph, importer, test_data_dir)
        this_graph.check_required_collections(graph)
        print('Executing City Graph query \n')
        query.city_graph()
        query.navbar_goto('graphs')
        this_graph.delete_graph(graph)

        this_graph.navbar_goto('queries')
        self.driver.refresh()

        print('Importing new queries \n')
        query.import_queries(str(test_data_dir / 'ui_data' / 'query_page' / 'imported_query.json'))
        print("Saving Current query as custom query\n")
        query.custom_query()
        print('Changing the number of results from 1000 to 100\n')
        query.number_of_results()

        print('Deleting collections begins \n')
        query.delete_all_collections()
        print('Deleting collections completed \n')

        # logging out from the current user
        #login.logout_button()
        #del login
        del query
        del query01
        print("---------Checking Query completed--------- \n")


    @testcase
    def test_support(self):
        """testing support page"""
        print("---------Checking Support page started--------- \n")
        #login = LoginPage(self.driver)
        #login.login('root', self.root_passvoid)

        # creating multiple support page obj
        support = SupportPage(self.driver)

        print('Selecting Support Page \n')
        support.select_support_page()

        print('Selecting documentation tab \n')
        support.select_documentation_support()
        print('Checking all arangodb manual link\n')
        support.manual_link()
        print('Checking all AQL Query Language link\n')
        support.aql_query_language_link()
        print('Checking all Fox Framework link \n')
        support.fox_framework_link()
        print('Checking all Drivers and Integration links\n')
        support.driver_and_integration_link()
        print('Checking Community Support tab \n')
        support.community_support_link()
        print('Checking Rest API tab \n')
        support.rest_api()

        # logging out from the current user
        #login.logout_button()
        #del login
        del support
        print("---------Checking Support page completed--------- \n")


#ui = Test()  # creating obj for the UI test
# ui.test_login()  # testing Login functionality
#ui.test_dashboard()  # testing Dashboard functionality
# ui.test_collection()  # testing Collection tab
# ui.test_analyzers()  # testing analyzers page
# ui.test_views()  # testing User functionality
# ui.test_query()  # testing query functionality **needs cluster deployment
# ui.test_graph()  # testing graph functionality **needs cluster deployment
# ui.test_support()
# ui.test_database()  # testing database page
# ui.test_user()  # testing User functionality
#ui.teardown()  # close the driver and quit

