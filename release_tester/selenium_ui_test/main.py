#!/usr/bin/env python
"""
main entrance point for the UI tests
"""

from selenium_ui_test.base_selenium import BaseSelenium
from selenium_ui_test.dashboard_page import DashboardPage
from selenium_ui_test.login_page import LoginPage
from selenium_ui_test.user_page import UserPage
from selenium_ui_test.views_page import ViewsPage
from selenium_ui_test.collection_page import CollectionPage
from selenium_ui_test.graph_page import GraphPage
from selenium_ui_test.query_page import QueryPage
from selenium_ui_test.support_page import SupportPage

# can't circumvent long lines.. nAttr nLines
# pylint: disable=C0301 disable=R0902 disable=R0915

class Test(BaseSelenium):
    """initial base class setup"""
    BaseSelenium.set_up_class()

    def __init__(self, root_passvoid, url, selenium_driver):
        """initial web driver setup"""
        self.driver = selenium_driver
        self.root_passvoid = root_passvoid
        self.url = url
        super().__init__()

    @staticmethod
    def teardown():
        """tear down class and quit driver instance"""
        BaseSelenium.tear_down()

    def test_login(self):
        """testing login page"""
        print("Starting ", self.driver.title, "\n")
        login = LoginPage(self.driver)
        login.login('root', self.root_passvoid)
        login.logout_button()

    def test_dashboard(self):
        """testing dashboard page"""
        print("---------Checking Dashboard started--------- \n")
        login = LoginPage(self.driver)
        login.login('root', self.root_passvoid)
        # creating object for dashboard
        dash = DashboardPage(self.driver)
        dash.check_server_package_name()
        dash.check_current_package_version()
        dash.check_current_username()
        dash.check_current_db()
        dash.check_db_status()
        dash.check_db_engine()
        dash.check_db_uptime()
        # fixme (not supported v3.7.7)
        print("\nSwitch to System Resource tab\n")
        dash.check_system_resource()
        print("Switch to Metrics tab\n")
        dash.check_system_metrics()
        print("scrolling the current page \n")
        dash.scroll()
        print("Downloading Metrics as JSON file \n")
        dash.metrics_download()
        dash.select_reload_btn()
        print("Opening Twitter link \n")
        dash.click_twitter_link()
        print("Opening Slack link \n")
        dash.click_slack_link()
        print("Opening Stackoverflow link \n")
        dash.click_stackoverflow_link()
        print("Opening Google group link \n")
        dash.click_google_group_link()
        login.logout_button()
        print("---------Checking Dashboard Completed--------- \n")

    def test_collection(self):
        """testing collection page"""
        print("---------Checking Collection Begin--------- \n")
        login = LoginPage(self.driver)
        login.login('root', self.root_passvoid)
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
        print("Displaying status unloaded collection\n")
        col.select_status_unloaded()
        col1.select_status_unloaded()
        print("Sorting collections by type\n")
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
        col1.select_choose_file_btn('release-test-automation\\test_data\\ui_data\\edges.json')
        col1.select_confirm_upload_btn()
        self.driver.refresh()  # in order to clear the screen before fetching data
        print("Uploading " + col1.getting_total_row_count() + " to the collection Completed\n")
        print("Selecting size of the displayed\n")

        self.driver.back()

        col.select_doc_collection()
        print("Uploading file to the collection started\n")
        col.select_upload_btn()
        print("Uploading json file\n")
        col.select_choose_file_btn('release-test-automation\\test_data\\ui_data\\edges.json\\names_100.json')
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
        col.select_index_type(1)
        print("filling up all necessary info for geo index\n")
        col.creating_geo_index()
        print("Creating new geo index\n")
        col.select_create_index_btn()
        print("Creating Geo Index completed\n")

        print("Creating Persistent Index Started\n")
        col1.create_new_index_btn()
        col1.select_index_type(2)
        print("filling up all necessary info for  persistent index\n")
        col1.creating_persistent_index()
        print("Creating new persistent index\n")
        col1.select_create_index_btn()
        print("Creating Persistent Index Completed\n")

        print("Creating Fulltext Index Started\n")
        col2.create_new_index_btn()
        col2.select_index_type(3)
        col2.creating_fulltext_index()
        col2.select_create_index_btn()
        print("Creating Fulltext Index Completed\n")

        print("Creating TTL Index Started\n")
        col3.create_new_index_btn()
        col3.select_index_type(4)
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
        col.select_settings_tab()
        self.driver.refresh()
        print("Loading and Unloading collection\n")
        col.select_settings_unload_btn()
        col1.select_settings_unload_btn()
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
        login.logout_button()
        del login
        print("---------Checking Collection Completed--------- \n")

    def test_views(self):
        """testing Views page"""
        print("---------Checking Views Begin--------- \n")
        login = LoginPage(self.driver)
        login.login('root', self.root_passvoid)
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
        print("Rename firstViews to thirdViews started \n")
        views.clicking_rename_views_btn()
        views.rename_views_name("thirdView")
        views.rename_views_name_confirm()
        print("Rename the current Views completed \n")
        self.driver.back()
        print("Deleting views started \n")
        views.select_renamed_view()
        views.delete_views_btn()
        views.delete_views_confirm_btn()
        views.final_delete_confirmation()

        views1.select_second_view()
        views1.delete_views_btn()
        views1.delete_views_confirm_btn()
        views1.final_delete_confirmation()
        print("Deleting views completed\n")
        login.logout_button()
        del login
        del views
        del views1
        print("---------Checking Views completed--------- \n")

    def test_graph(self, importer, test_data_dir):
        """testing graph page"""
        print("---------Checking Graphs started--------- \n")
        login = LoginPage(self.driver)
        login.login('root', self.root_passvoid)

        # creating multiple graph obj
        graph = GraphPage(self.driver)
        graph1 = GraphPage(self.driver)
        graph2 = GraphPage(self.driver)
        graph3 = GraphPage(self.driver)
        graph4 = GraphPage(self.driver)
        graph5 = GraphPage(self.driver)
        graph6 = GraphPage(self.driver)
        graph7 = GraphPage(self.driver)
        graph8 = GraphPage(self.driver)
        graph9 = GraphPage(self.driver)
        graph01 = GraphPage(self.driver)

        print("Manual Graph creation started \n")
        graph.create_manual_graph()
        graph.select_graph_page()
        graph.adding_knows_manual_graph()
        print("Manual Graph creation completed \n")
        graph.delete_graph(9)
        self.driver.refresh()

        print("Adding Satellite Graph started \n")
        graph9.select_graph_page()
        graph9.adding_satellite_graph(importer, test_data_dir)
        print("Adding Satellite Graph started \n")

        print("Adding Smart Graph started \n")
        graph01.adding_smart_graph(importer, test_data_dir)
        print("Adding Smart Graph completed \n")

        print("Adding Disjoint Smart Graph started \n")
        graph01.adding_smart_graph(importer, test_data_dir, True)
        print("Adding Disjoint Smart Graph completed \n")

        print("Example Graphs creation started\n")
        print("Creating Knows Graph\n")
        graph1.select_create_graph(1)
        self.driver.refresh()
        print("Checking required collections created for Knows Graph\n")
        graph1.checking_collection_creation(1)
        print("Searching for 'knows' and 'persons' collections\n")
        graph1.check_required_collection(1)

        print("Creating Traversal Graph\n")
        graph2.select_create_graph(2)
        self.driver.refresh()
        print("Checking required collections created for Traversal Graph\n")
        graph2.checking_collection_creation(2)
        print("Searching for 'circles' and 'edges' collections\n")
        graph2.check_required_collection(2)

        print("Creating K Shortest Path Graph\n")
        graph3.select_create_graph(3)
        self.driver.refresh()
        print("Checking required collections created for K Shortest Path Graph\n")
        graph3.checking_collection_creation(3)
        print("Searching for 'connections' and 'places' collections\n")
        graph3.check_required_collection(3)

        print("Creating Mps Graph\n")
        graph4.select_create_graph(4)
        self.driver.refresh()
        print("Checking required collections created for Mps Graph\n")
        graph4.checking_collection_creation(4)
        print("Searching for 'mps_edges' and 'mps_verts' collections\n")
        graph4.check_required_collection(4)

        print("Creating World Graph\n")
        graph5.select_create_graph(5)
        self.driver.refresh()
        print("Checking required collections created for World Graph\n")
        graph5.checking_collection_creation(5)
        print("Searching for 'worldEdges' and 'worldvertices' collections\n")
        graph5.check_required_collection(5)

        print("Creating Social Graph\n")
        graph6.select_create_graph(6)
        self.driver.refresh()
        print("Checking required collections created for Social Graph\n")
        graph6.checking_collection_creation(6)
        print("Searching for 'female' , 'male' and 'relation' collections\n")
        graph6.check_required_collection(6)

        print("Creating City Graph\n")
        graph7.select_create_graph(7)
        self.driver.refresh()
        print("Checking required collections created for City Graph\n")
        graph7.checking_collection_creation(7)
        print("Searching for 'frenchCity' , 'frenchHighway' 'germanCity', 'germanHighway' & 'internationalHighway'\n")
        graph7.check_required_collection(7)
        print("Example Graphs creation Completed\n")

        print("Sorting all graphs as descending\n")
        graph.select_sort_descend()

        print("Selecting Knows Graph for inspection\n")
        graph.inspect_knows_graph()
        print("Selecting Graphs settings menu\n")
        graph.graph_setting()

        print("Deleting created Graphs started\n")
        graph1.delete_graph(1)
        graph2.delete_graph(2)
        graph3.delete_graph(3)
        graph4.delete_graph(4)
        graph5.delete_graph(5)
        graph6.delete_graph(6)
        graph7.delete_graph(7)

        # print("Deleting created Graphs Completed\n")
        del graph
        del graph1
        del graph2
        del graph3
        del graph4
        del graph5
        del graph6
        del graph7
        del graph8
        del graph9
        del graph01
        login.logout_button()
        del login
        print("---------Checking Graphs completed--------- \n")

    def test_user(self):
        """testing user page"""
        print("---------User Test Begin--------- \n")
        login = LoginPage(self.driver)
        login.login('root', self.root_passvoid)
        user = UserPage(self.driver)
        print("New user creation begins \n")
        user.new_user_tab()
        user.add_new_user()
        user.new_user_name('tester')
        user.naming_new_user('tester')
        user.new_user_password('tester')
        user.creating_new_user()
        print("New user creation completed \n")
        user.selecting_new_user()
        user.selecting_permission()
        print("Changing new user DB permission \n")
        user.changing_db_permission()
        self.driver.back()
        user.saving_user_cfg()
        print("Changing new user DB permission completed. \n")
        login.logout_button()

        # creating login page object to reuse it's methods for login with newly created user
        print("Re-Login begins with new user\n")
        login = LoginPage(self.driver)
        login.login('tester', 'tester')
        print("Re-Login begins with new user completed\n")

        # logout from the current user to get back to root
        login.logout_button()
        del login
        # login back with root user
        login = LoginPage(self.driver)
        login.login('root', self.root_passvoid)
        # fixme Deleting old user object
        del user
        user = UserPage(self.driver)
        user.new_user_tab()
        user.selecting_new_user()
        print("Deleting created user begins\n")
        user.delete_user_btn()
        user.confirm_delete_btn()
        print("Deleting created user completed \n")
        login.logout_button()
        # fixme Deleting old user object
        del login
        print("---------User Test Completed---------\n")

    def test_query(self):
        """testing query page"""
        print("---------Query Test Begin--------- \n")
        login = LoginPage(self.driver)
        login.login('root', self.root_passvoid)

        # creating multiple query obj
        query = QueryPage(self.driver)
        query01 = QueryPage(self.driver)

        print("Importing IMDB collections \n")
        query.import_collections()

        print("Selecting Query page for basic CRUD operation \n")
        query.selecting_query_page()

        print("Executing insert query \n")
        query.execute_query('for i IN 1..10000\n INSERT {\n \t "name": "Ned",\n "surname": "Stark",'
                                 '\n"alive": true,\n"age": 41,"traits":["A","H","C","N","P"]\n} INTO '
                                 'Characters')
        print("Profiling current query \n")
        query.profile_query()
        print("Explaining current query \n")
        query.explain_query()
        # print("Debug packaged downloading for the current query \n")
        # query.debug_package_download()
        print("Removing all query results \n")
        query.remove_query_result()
        print("Clearing query execution area \n")
        query.clear_query_area()

        print("Executing spot light functionality \n")
        query.spot_light_function('COUNT')  # can be used for search different keyword
        print('Executing read query\n')
        query01.execute_query('FOR c IN imdb_vertices\n\tLIMIT 500\nRETURN c')
        print('Updating documents\n')
        query.update_documents()
        print('Executing query with bind parameters \n')
        query.bind_parameters_query()

        print("Executing example graph query \n")
        query.world_country_graph_query()

        print('Executing K_Shortest_Paths Graph query \n')
        query.k_shortest_paths_graph_query()

        print('Executing City Graph query \n')
        query.city_graph()

        print('Importing new queries \n')
        query.import_queries('release-test-automation\\test_data\\ui_data\\query_page\\imported_query.json')
        print("Saving Current query as custom query\n")
        query.custom_query()
        print('Changing the number of results from 1000 to 100\n')
        query.number_of_results()

        print('Deleting collections begins \n')
        query.delete_all_collections()
        print('Deleting collections completed \n')

        # logging out from the current user
        login.logout_button()
        del login
        del query
        del query01
        print("---------Checking Query completed--------- \n")

    def test_support(self):
        """testing support page"""
        print("---------Checking Support page started--------- \n")
        login = LoginPage(self.driver)
        login.login('root', self.root_passvoid)

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
        login.logout_button()
        del login
        del support
        print("---------Checking Support page completed--------- \n")


#ui = Test()  # creating obj for the UI test
# ui.test_login()  # testing Login functionality
#ui.test_dashboard()  # testing Dashboard functionality
# ui.test_collection()  # testing Collection tab
# ui.test_views()  # testing User functionality
# ui.test_query()  # testing query functionality **needs cluster deployment
# ui.test_graph()  # testing graph functionality **needs cluster deployment
# ui.test_support()
# ui.test_user()  # testing User functionality
#ui.teardown()  # close the driver and quit
