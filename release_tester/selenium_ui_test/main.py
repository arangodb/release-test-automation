from base_selenium import BaseSelenium
from dashboard_page import DashboardPage
from login_page import LoginPage
from user_page import UserPage
from views_page import ViewsPage
from collection_page import CollectionPage
from graph_page import GraphPage
from query_page import QueryPage
from support_page import SupportPage


class Test(BaseSelenium):
    """initial base class setup"""
    BaseSelenium.set_up_class()

    def __init__(self):
        """initial web driver setup"""
        super().__init__()

    @staticmethod
    def teardown():
        """tear down class and quit driver instance"""
        BaseSelenium.tear_down()

    def test_login(self):
        """testing login page"""
        print("Starting ", self.driver.title, "\n")
        self.login = LoginPage(self.driver)
        self.login.login('root', '')
        self.login.logout_button()
        del self.login

    def test_dashboard(self):
        """testing dashboard page"""
        print("---------Checking Dashboard started--------- \n")
        self.login = LoginPage(self.driver)
        self.login.login('root', '')
        # creating object for dashboard
        self.dash = DashboardPage(self.driver)
        self.dash.check_server_package_name()
        self.dash.check_current_package_version()
        self.dash.check_current_username()
        self.dash.check_current_db()
        self.dash.check_db_status()
        self.dash.check_db_engine()
        self.dash.check_db_uptime()
        # fixme (not supported v3.7.7)
        print("\nSwitch to System Resource tab\n")
        self.dash.check_system_resource()
        print("Switch to Metrics tab\n")
        self.dash.check_system_metrics()
        print("scrolling the current page \n")
        self.dash.scroll()
        print("Downloading Metrics as JSON file \n")
        self.dash.metrics_download()
        self.dash.select_reload_btn()
        print("Opening Twitter link \n")
        self.dash.click_twitter_link()
        print("Opening Slack link \n")
        self.dash.click_slack_link()
        print("Opening Stackoverflow link \n")
        self.dash.click_stackoverflow_link()
        print("Opening Google group link \n")
        self.dash.click_google_group_link()
        self.login.logout_button()
        del self.login
        print("---------Checking Dashboard Completed--------- \n")

    def test_collection(self):
        """testing collection page"""
        print("---------Checking Collection Begin--------- \n")
        self.login = LoginPage(self.driver)
        self.login.login('root', '')
        self.col = CollectionPage(self.driver)  # creating obj for Collection
        self.col1 = CollectionPage(self.driver)
        self.col2 = CollectionPage(self.driver)
        self.col3 = CollectionPage(self.driver)

        print("Selecting collection tab\n")
        self.col.select_collection_page()

        print("Creating new collection started \n")
        self.col.select_create_collection()
        print("Creating Document collection \n")
        self.col.select_new_collection_name("TestDoc")
        print("Creating Document type collection started \n")
        self.col.select_collection_type(0)  # 0 for Doc type document
        self.col.select_advance_option()
        print("Choosing wait type to YES \n")
        self.col.wait_for_sync(1)
        self.col.create_new_collection_btn()
        print("Creating Document type collection completed \n")

        print("Creating Edge type collection\n")
        self.col1.select_create_collection()
        self.col1.select_new_collection_name("TestEdge")
        self.col1.select_collection_type(1)  # 1 for Edge type document
        self.col1.select_advance_option()
        print("Choosing wait type to YES \n")
        self.col1.wait_for_sync(1)
        self.col1.create_new_collection_btn()
        print("Creating new Edge collection completed \n")

        print("Creating new collection started \n")
        self.col2.select_create_collection()
        print("Creating Document collection \n")
        self.col2.select_new_collection_name("Test")
        print("Creating Document type collection started \n")
        self.col2.select_collection_type(0)  # 0 for Doc type document
        self.col2.select_advance_option()
        print("Choosing wait type to YES \n")
        self.col2.wait_for_sync(1)
        self.col2.create_new_collection_btn()
        print("Creating Document type collection completed \n")

        print("checking Search options\n")
        print("Searching using keyword 'Doc'\n")
        self.col.checking_search_options("Doc")
        self.driver.refresh()
        print("Searching using keyword 'Edge'\n")
        self.col1.checking_search_options("Edge")
        self.driver.refresh()
        print("Searching using keyword 'test'\n")
        self.col2.checking_search_options("Test")
        self.driver.refresh()

        print("Selecting Settings\n")
        self.col.select_collection_settings()
        print("Displaying system's collection\n")
        self.col.display_system_collection()
        self.col1.display_system_collection()  # Doing the reverse part
        print("Displaying Document type collection\n")
        self.col.display_document_collection()
        self.col1.display_document_collection()
        print("Displaying Edge type collection\n")
        self.col.display_edge_collection()
        self.col1.display_edge_collection()
        print("Displaying status loaded collection\n")
        self.col.select_status_loaded()
        self.col1.select_status_loaded()
        print("Displaying status unloaded collection\n")
        self.col.select_status_unloaded()
        self.col1.select_status_unloaded()
        print("Sorting collections by type\n")
        self.col.sort_by_type()
        print("Sorting collections by descending\n")
        self.col.sort_descending()
        self.col1.sort_descending()
        print("Sorting collections by name\n")
        self.col.sort_by_name()

        self.col1.select_edge_collection_upload()
        print("Uploading file to the collection started\n")
        self.col1.select_upload_btn()
        print("Uploading json file\n")
        self.col1.select_choose_file_btn('release-test-automation\\test_data\\ui_data\\edges.json')
        self.col1.select_confirm_upload_btn()
        self.driver.refresh()  # in order to clear the screen before fetching data
        print("Uploading " + self.col1.getting_total_row_count() + " to the collection Completed\n")
        print("Selecting size of the displayed\n")

        self.driver.back()

        self.col.select_doc_collection()
        print("Uploading file to the collection started\n")
        self.col.select_upload_btn()
        print("Uploading json file\n")
        self.col.select_choose_file_btn('release-test-automation\\test_data\\ui_data\\edges.json\\names_100.json')
        self.col.select_confirm_upload_btn()
        self.driver.refresh()  # in order to clear the screen before fetching data
        print("Uploading " + self.col.getting_total_row_count() + " to the collection Completed\n")
        print("Selecting size of the displayed\n")

        # print("Downloading Documents as JSON file\n")
        # self.col.download_doc_as_json()

        print("Filter collection by '_id'\n")
        self.col.filter_documents(3)
        self.col1.filter_documents(1)
        self.col.display_document_size(2)  # choosing 50 results to display
        print("Traverse back and forth search result page 1 and 2\n")
        self.col.traverse_search_pages()
        print("Selecting hand selection button\n")
        self.col.select_hand_pointer()
        print("Select Multiple item using hand pointer\n")
        self.col.select_multiple_item()
        self.col.move_btn()
        print("Multiple data moving into test collection\n")
        self.col.move_doc_textbox('Test')
        self.col.move_confirm_btn()

        print("Deleting multiple data started\n")
        self.col1.select_multiple_item()
        self.col.select_collection_delete_btn()
        self.col.collection_delete_confirm_btn()
        self.col.collection_really_dlt_btn()
        print("Deleting multiple data completed\n")

        print("Selecting Index menu\n")
        self.col.select_index_menu()
        print("Create new index\n")
        self.col.create_new_index_btn()

        print("Creating Geo Index Started\n")
        self.col.select_index_type(1)
        print("filling up all necessary info for geo index\n")
        self.col.creating_geo_index()
        print("Creating new geo index\n")
        self.col.select_create_index_btn()
        print("Creating Geo Index completed\n")

        print("Creating Persistent Index Started\n")
        self.col1.create_new_index_btn()
        self.col1.select_index_type(2)
        print("filling up all necessary info for  persistent index\n")
        self.col1.creating_persistent_index()
        print("Creating new persistent index\n")
        self.col1.select_create_index_btn()
        print("Creating Persistent Index Completed\n")

        print("Creating Fulltext Index Started\n")
        self.col2.create_new_index_btn()
        self.col2.select_index_type(3)
        self.col2.creating_fulltext_index()
        self.col2.select_create_index_btn()
        print("Creating Fulltext Index Completed\n")

        print("Creating TTL Index Started\n")
        self.col3.create_new_index_btn()
        self.col3.select_index_type(4)
        self.col3.creating_ttl_index()
        self.col3.select_create_index_btn()
        print("Creating TTL Index Completed\n")

        print("Deleting all index started\n")
        self.col.delete_all_index()
        self.col1.delete_all_index()
        self.col2.delete_all_index()
        self.col3.delete_all_index()
        print("Deleting all index completed\n")

        print("Select Info tab\n")
        self.col.select_info_tab()
        print("Selecting Schema Tab\n")
        # self.col.select_schema_tab()

        print("Select Settings tab\n")
        self.col.select_settings_tab()
        self.driver.refresh()
        print("Loading and Unloading collection\n")
        self.col.select_settings_unload_btn()
        self.col1.select_settings_unload_btn()
        self.driver.refresh()
        print("Truncate collection\n")
        self.col.select_truncate_btn()
        self.driver.refresh()
        print("Deleting Collection started\n")
        self.col.delete_collection()
        #
        print("Selecting TestEdge Collection for deleting\n")
        self.col2.select_edge_collection()
        self.col2.delete_collection()

        print("Selecting Test Collection for deleting\n")
        self.col3.select_test_doc_collection()
        self.col3.delete_collection()
        print("Deleting Collection completed\n")

        del self.col
        del self.col1
        del self.col2
        del self.col3
        self.login.logout_button()
        del self.login
        print("---------Checking Collection Completed--------- \n")

    def test_views(self):
        """testing Views page"""
        print("---------Checking Views Begin--------- \n")
        self.login = LoginPage(self.driver)
        self.login.login('root', '')
        self.views = ViewsPage(self.driver)  # creating obj for viewPage
        self.views1 = ViewsPage(self.driver)  # creating 2nd obj for viewPage to do counter part of the testing

        print("Selecting Views tab\n")
        self.views.select_views_tab()
        print("Creating first views\n")
        self.views.create_new_views()
        self.views.naming_new_view("firstView")
        self.views.select_create_btn()
        print("Creating first views completed\n")

        print("Creating second views\n")
        self.views1.create_new_views()
        self.views1.naming_new_view("secondView")
        self.views1.select_create_btn()
        print("Creating second views completed\n")

        self.views.select_views_settings()
        print("Sorting views to descending\n")
        self.views.select_sorting_views()

        print("Sorting views to ascending\n")
        self.views1.select_sorting_views()

        print("search views option testing\n")
        self.views1.search_views("se")
        self.views.search_views("fi")

        print("Selecting first Views \n")
        self.views.select_first_view()
        print("Selecting collapse button \n")
        self.views.select_collapse_btn()
        print("Selecting expand button \n")
        self.views.select_expand_btn()
        print("Selecting editor mode \n")
        self.views.select_editor_mode_btn()
        print("Switch editor mode to Code \n")
        self.views.switch_to_code_editor_mode()
        print("Switch editor mode to Compact mode Code \n")
        self.views.compact_json_data()

        print("Selecting editor mode \n")
        self.views1.select_editor_mode_btn()
        print("Switch editor mode to Tree \n")
        self.views1.switch_to_tree_editor_mode()

        print("Clicking on ArangoSearch documentation link \n")
        self.views.click_arangosearch_documentation_link()
        print("Selecting search option\n")
        self.views.select_inside_search("i")
        print("Traversing all results up and down \n")
        self.views.search_result_traverse_down()
        self.views.search_result_traverse_up()
        self.views1.select_inside_search("")
        # ###print("Changing views consolidationPolicy id to 55555555 \n")
        # ###self.views1.change_consolidation_policy(55555555)
        print("Rename firstViews to thirdViews started \n")
        self.views.clicking_rename_views_btn()
        self.views.rename_views_name("thirdView")
        self.views.rename_views_name_confirm()
        print("Rename the current Views completed \n")
        self.driver.back()
        print("Deleting views started \n")
        self.views.select_renamed_view()
        self.views.delete_views_btn()
        self.views.delete_views_confirm_btn()
        self.views.final_delete_confirmation()

        self.views1.select_second_view()
        self.views1.delete_views_btn()
        self.views1.delete_views_confirm_btn()
        self.views1.final_delete_confirmation()
        print("Deleting views completed\n")
        self.login.logout_button()
        del self.login
        del self.views
        del self.views1
        print("---------Checking Views completed--------- \n")

    def test_graph(self):
        """testing graph page"""
        print("---------Checking Graphs started--------- \n")
        self.login = LoginPage(self.driver)
        self.login.login('root', '')

        # creating multiple graph obj
        self.graph = GraphPage(self.driver)
        self.graph1 = GraphPage(self.driver)
        self.graph2 = GraphPage(self.driver)
        self.graph3 = GraphPage(self.driver)
        self.graph4 = GraphPage(self.driver)
        self.graph5 = GraphPage(self.driver)
        self.graph6 = GraphPage(self.driver)
        self.graph7 = GraphPage(self.driver)
        self.graph8 = GraphPage(self.driver)
        self.graph9 = GraphPage(self.driver)
        self.graph01 = GraphPage(self.driver)

        print("Manual Graph creation started \n")
        self.graph.create_manual_graph()
        self.graph.select_graph_page()
        self.graph.adding_knows_manual_graph()
        print("Manual Graph creation completed \n")
        self.graph.delete_graph(9)
        self.driver.refresh()

        print("Adding Satellite Graph started \n")
        self.graph9.select_graph_page()
        self.graph9.adding_satellite_graph()
        print("Adding Satellite Graph started \n")

        print("Adding Smart Graph started \n")
        self.graph01.adding_smart_graph()
        print("Adding Smart Graph completed \n")

        print("Adding Disjoint Smart Graph started \n")
        self.graph01.adding_smart_graph(True)
        print("Adding Disjoint Smart Graph completed \n")

        print("Example Graphs creation started\n")
        print("Creating Knows Graph\n")
        self.graph1.select_create_graph(1)
        self.driver.refresh()
        print("Checking required collections created for Knows Graph\n")
        self.graph1.checking_collection_creation(1)
        print("Searching for 'knows' and 'persons' collections\n")
        self.graph1.check_required_collection(1)

        print("Creating Traversal Graph\n")
        self.graph2.select_create_graph(2)
        self.driver.refresh()
        print("Checking required collections created for Traversal Graph\n")
        self.graph2.checking_collection_creation(2)
        print("Searching for 'circles' and 'edges' collections\n")
        self.graph2.check_required_collection(2)

        print("Creating K Shortest Path Graph\n")
        self.graph3.select_create_graph(3)
        self.driver.refresh()
        print("Checking required collections created for K Shortest Path Graph\n")
        self.graph3.checking_collection_creation(3)
        print("Searching for 'connections' and 'places' collections\n")
        self.graph3.check_required_collection(3)

        print("Creating Mps Graph\n")
        self.graph4.select_create_graph(4)
        self.driver.refresh()
        print("Checking required collections created for Mps Graph\n")
        self.graph4.checking_collection_creation(4)
        print("Searching for 'mps_edges' and 'mps_verts' collections\n")
        self.graph4.check_required_collection(4)

        print("Creating World Graph\n")
        self.graph5.select_create_graph(5)
        self.driver.refresh()
        print("Checking required collections created for World Graph\n")
        self.graph5.checking_collection_creation(5)
        print("Searching for 'worldEdges' and 'worldvertices' collections\n")
        self.graph5.check_required_collection(5)

        print("Creating Social Graph\n")
        self.graph6.select_create_graph(6)
        self.driver.refresh()
        print("Checking required collections created for Social Graph\n")
        self.graph6.checking_collection_creation(6)
        print("Searching for 'female' , 'male' and 'relation' collections\n")
        self.graph6.check_required_collection(6)

        print("Creating City Graph\n")
        self.graph7.select_create_graph(7)
        self.driver.refresh()
        print("Checking required collections created for City Graph\n")
        self.graph7.checking_collection_creation(7)
        print("Searching for 'frenchCity' , 'frenchHighway' 'germanCity', 'germanHighway' & 'internationalHighway'\n")
        self.graph7.check_required_collection(7)
        print("Example Graphs creation Completed\n")

        print("Sorting all graphs as descending\n")
        self.graph.select_sort_descend()

        print("Selecting Knows Graph for inspection\n")
        self.graph.inspect_knows_graph()
        print("Selecting Graphs settings menu\n")
        self.graph.graph_setting()

        print("Deleting created Graphs started\n")
        self.graph1.delete_graph(1)
        self.graph2.delete_graph(2)
        self.graph3.delete_graph(3)
        self.graph4.delete_graph(4)
        self.graph5.delete_graph(5)
        self.graph6.delete_graph(6)
        self.graph7.delete_graph(7)

        # print("Deleting created Graphs Completed\n")
        del self.graph
        del self.graph1
        del self.graph2
        del self.graph3
        del self.graph4
        del self.graph5
        del self.graph6
        del self.graph7
        del self.graph8
        del self.graph9
        del self.graph01
        self.login.logout_button()
        del self.login
        print("---------Checking Graphs completed--------- \n")

    def test_user(self):
        """testing user page"""
        print("---------User Test Begin--------- \n")
        self.login = LoginPage(self.driver)
        self.login.login('root', '')
        self.user = UserPage(self.driver)
        print("New user creation begins \n")
        self.user.new_user_tab()
        self.user.add_new_user()
        self.user.new_user_name('tester')
        self.user.naming_new_user('tester')
        self.user.new_user_password('tester')
        self.user.creating_new_user()
        print("New user creation completed \n")
        self.user.selecting_new_user()
        self.user.selecting_permission()
        print("Changing new user DB permission \n")
        self.user.changing_db_permission()
        self.driver.back()
        self.user.saving_user_cfg()
        print("Changing new user DB permission completed. \n")
        self.login.logout_button()

        # creating login page object to reuse it's methods for login with newly created user
        print("Re-Login begins with new user\n")
        self.login = LoginPage(self.driver)
        self.login.login('tester', 'tester')
        print("Re-Login begins with new user completed\n")

        # logout from the current user to get back to root
        self.login.logout_button()
        del self.login
        # login back with root user
        self.login = LoginPage(self.driver)
        self.login.login('root', '')
        # fixme Deleting old user object
        del self.user
        self.user = UserPage(self.driver)
        self.user.new_user_tab()
        self.user.selecting_new_user()
        print("Deleting created user begins\n")
        self.user.delete_user_btn()
        self.user.confirm_delete_btn()
        print("Deleting created user completed \n")
        self.login.logout_button()
        # fixme Deleting old user object
        del self.login
        print("---------User Test Completed---------\n")

    def test_query(self):
        """testing query page"""
        print("---------Query Test Begin--------- \n")
        self.login = LoginPage(self.driver)
        self.login.login('root', '')

        # creating multiple query obj
        self.query = QueryPage(self.driver)
        self.query01 = QueryPage(self.driver)

        print("Importing IMDB collections \n")
        self.query.import_collections()

        print("Selecting Query page for basic CRUD operation \n")
        self.query.selecting_query_page()

        print("Executing insert query \n")
        self.query.execute_query('for i IN 1..10000\n INSERT {\n \t "name": "Ned",\n "surname": "Stark",'
                                 '\n"alive": true,\n"age": 41,"traits":["A","H","C","N","P"]\n} INTO '
                                 'Characters')
        print("Profiling current query \n")
        self.query.profile_query()
        print("Explaining current query \n")
        self.query.explain_query()
        # print("Debug packaged downloading for the current query \n")
        # self.query.debug_package_download()
        print("Removing all query results \n")
        self.query.remove_query_result()
        print("Clearing query execution area \n")
        self.query.clear_query_area()

        print("Executing spot light functionality \n")
        self.query.spot_light_function('COUNT')  # can be used for search different keyword
        print('Executing read query\n')
        self.query01.execute_query('FOR c IN imdb_vertices\n\tLIMIT 500\nRETURN c')
        print('Updating documents\n')
        self.query.update_documents()
        print('Executing query with bind parameters \n')
        self.query.bind_parameters_query()

        print("Executing example graph query \n")
        self.query.world_country_graph_query()

        print('Executing K_Shortest_Paths Graph query \n')
        self.query.k_shortest_paths_graph_query()

        print('Executing City Graph query \n')
        self.query.city_graph()

        print('Importing new queries \n')
        self.query.import_queries('release-test-automation\\test_data\\ui_data\\query_page\\imported_query.json')
        print("Saving Current query as custom query\n")
        self.query.custom_query()
        print('Changing the number of results from 1000 to 100\n')
        self.query.number_of_results()

        print('Deleting collections begins \n')
        self.query.delete_all_collections()
        print('Deleting collections completed \n')

        # logging out from the current user
        self.login.logout_button()
        del self.login
        del self.query
        del self.query01
        print("---------Checking Query completed--------- \n")

    def test_support(self):
        """testing support page"""
        print("---------Checking Support page started--------- \n")
        self.login = LoginPage(self.driver)
        self.login.login('root', '')

        # creating multiple support page obj
        self.support = SupportPage(self.driver)

        print('Selecting Support Page \n')
        self.support.select_support_page()

        print('Selecting documentation tab \n')
        self.support.select_documentation_support()
        print('Checking all arangodb manual link\n')
        self.support.manual_link()
        print('Checking all AQL Query Language link\n')
        self.support.aql_query_language_link()
        print('Checking all Fox Framework link \n')
        self.support.fox_framework_link()
        print('Checking all Drivers and Integration links\n')
        self.support.driver_and_integration_link()
        print('Checking Community Support tab \n')
        self.support.community_support_link()
        print('Checking Rest API tab \n')
        self.support.rest_api()

        # logging out from the current user
        self.login.logout_button()
        del self.login
        del self.support
        print("---------Checking Support page completed--------- \n")


ui = Test()  # creating obj for the UI test
# ui.test_login()  # testing Login functionality
ui.test_dashboard()  # testing Dashboard functionality
# ui.test_collection()  # testing Collection tab
# ui.test_views()  # testing User functionality
# ui.test_query()  # testing query functionality **needs cluster deployment
# ui.test_graph()  # testing graph functionality **needs cluster deployment
# ui.test_support()
# ui.test_user()  # testing User functionality
ui.teardown()  # close the driver and quit
