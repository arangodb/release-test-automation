import time

from selenium_ui_test.pages.base_page import BasePage
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_ui_test.pages.navbar import NavigationBarPage

# can't circumvent long lines.. nAttr nLines
# pylint: disable=C0301 disable=R0902 disable=R0915 disable=R0914


class QueryPage(NavigationBarPage):
    """Class for Query page"""

    def __init__(self, driver):
        """Query page initialization"""
        super().__init__(driver)
        self.selecting_query_page_id = "queries"
        self.execute_query_btn_id = 'executeQuery'
        self.profile_query_id = 'profileQuery'
        self.explain_query_id = 'explainQuery'
        self.create_debug_package_id = 'debugQuery'
        self.remove_all_results_id = 'removeResults'
        self.query_spot_light_id = 'querySpotlight'
        self.save_current_query_id = 'saveCurrentQuery'
        self.new_query_name_id = 'new-query-name'
        self.select_query_size_id = 'querySize'
        self.json_to_table_span_it = 'switchTypes'
        self.collection_settings_id = "//*[@id='subNavigationBarPage']/ul[2]/li[4]/a"
        self.graph_page = 'graphs'
        self.select_create_graph_id = "createGraph"
        self.select_world_graph_id = "//*[@id='exampleGraphs']/table/tbody/tr[5]/td[2]/button"
        self.select_example_graph_btn_id = "tab-exampleGraphs"

        self.confirm_delete_graph_id = "modalButton0"
        self.drop_graph_collection = "dropGraphCollections"
        self.select_really_delete_btn_id = "modal-confirm-delete"

        self.select_k_shortest_path_id = "//*[@id='exampleGraphs']/table/tbody/tr[3]/td[2]/button"
        self.select_k_shortest_path_graphs_setting_btn_id = "kShortestPathsGraph_settings"
        self.select_k_shortest_path_graphs_setting_btn_id_check = "kShortestPathsGraph_settings"
        self.bind_param_table_id = '//*[@id="arangoBindParamTable"]'
        self.bind_param_input_id = self.bind_param_table_id + '/tbody/tr[%s]/td[2]/input'

    def import_collections(self, restore, testdata_path, is_cluster):
        """importing collections for query"""
        print("Navigating to Collection page \n")
        # Selecting collections page
        self.navbar_goto("collections")
        data_path = testdata_path / 'ui_data' / 'query_page' / 'IMDB_DUMP'
        print(data_path)
        ret = restore.run_restore_monitored(
            str(data_path.absolute()),
            ['--number-of-shards', '9', '--replication-factor', '2'],
            40)
        if not ret[0]:
            raise Exception("restoring failed: " + str(ret[1]))

        print('Creating a blank collection\n')
        create_collection = "createCollection"
        create_collection_sitem = \
            self.locator_finder_by_id(create_collection)
        create_collection_sitem.click()

        new_collection_name = 'new-collection-name'
        new_collection_name_sitem = self.locator_finder_by_id(new_collection_name)
        new_collection_name_sitem.click()
        new_collection_name_sitem.send_keys('Characters')
        if is_cluster:
            new_collections_shards = 'new-collection-shards'
            new_collections_shards_sitem = WebDriverWait(self.webdriver, 15).until(
                EC.element_to_be_clickable((By.ID, new_collections_shards)),
                message="failed to get shards input field")
            new_collections_shards_sitem.click()
            new_collections_shards_sitem.send_keys('9')

            new_replication_factor = 'new-replication-factor'
            new_replication_factor_sitem = \
                BasePage.locator_finder_by_id(self, new_replication_factor)
            new_replication_factor_sitem.click()
            new_replication_factor_sitem.clear()
            new_replication_factor_sitem.click()
            new_replication_factor_sitem.send_keys('2')
        modal_button1_str = 'modalButton1'
        modal_button1_sitem = \
            WebDriverWait(self.webdriver, 15).until(
                EC.element_to_be_clickable((By.ID, modal_button1_str)),
                message="failed to wait for collection save button")
        modal_button1_sitem.click()
        # new_collection_name_sitem.send_keys(Keys.ENTER)

        self.webdriver.refresh()
        time.sleep(5)
        self.webdriver.back()
        time.sleep(1)

    def enter_query(self, query_string):
        """ type a query into the editor line by line """
        self.select_query_execution_area()
        self.clear_all_text(self.query_execution_area)
        for line in query_string.split('\n'):
            if len(line) > 0: # skip empty lines in heredocuments
                self.send_key_action(line)
                self.send_key_action(Keys.ENTER)

    def selecting_query_page(self):
        """Selecting query page"""
        self.navbar_goto("queries")

    def execute_insert_query(self):
        """This method will run an insert query"""

        query = '''
for i IN 1..10000
    INSERT {
       "name": "Ned",
"surname": "Stark",
"alive": true,
"age": 41,
"traits": ["A","H","C","N","P"]
} INTO Characters
'''
        self.enter_query(query)
        self.query_execution_btn()
        self.scroll(1)

    def execute_read_query(self):
        """This method will run a read query"""
        self.enter_query('''
FOR c IN imdb_vertices
    LIMIT 500
RETURN c
''')

        # selecting execute query button
        self.query_execution_btn()

        self.scroll(1)


    def profile_query(self):
        """profiling query"""
        profile = self.profile_query_id
        profile = \
            BasePage.locator_finder_by_id(self, profile)
        profile.click()
        time.sleep(2)

        self.scroll()

    def explain_query(self):
        """Explaining query"""
        explain_query = self.explain_query_id
        explain_query = \
            BasePage.locator_finder_by_id(self, explain_query)
        explain_query.click()
        time.sleep(2)

    def debug_package_download(self):
        """Downloading debug package"""
        if self.webdriver.name == "chrome":  # this will check browser name
            print("Download has been disabled for the Chrome browser \n")
        else:
            debug = self.create_debug_package_id
            debug = \
                BasePage.locator_finder_by_id(self, debug)
            debug.click()
            time.sleep(2)
            debug_btn = 'modalButton1'
            debug_btn = \
                BasePage.locator_finder_by_id(self, debug_btn)
            debug_btn.click()
            time.sleep(2)
            # self.clear_download_bar()

    def remove_query_result(self):
        """Removing all query results"""
        remove_results = self.remove_all_results_id
        remove_results = \
            BasePage.locator_finder_by_id(self, remove_results)
        remove_results.click()
        time.sleep(2)

    def clear_query_area(self):
        """Clearing current query area"""
        self.clear_all_text(self.query_execution_area)
        time.sleep(2)

    def spot_light_function(self, search):
        """ trigger the spotlight function """
        spot_light = self.query_spot_light_id
        spot_light = \
            BasePage.locator_finder_by_id(self, spot_light)
        spot_light.click()
        time.sleep(2)

        # searching for COUNT attribute
        self.send_key_action(search)
        self.send_key_action(Keys.DOWN * 5)
        time.sleep(1)

        self.send_key_action(Keys.UP * 3)
        self.send_key_action(Keys.ENTER)
        time.sleep(2)

    def update_documents(self):
        """ update some documents """
        print("Navigating to Collection page \n")
        # Selecting collections page
        collections = "collections"
        collections = \
            BasePage.locator_finder_by_id(self, collections)
        collections.click()
        time.sleep(1)

        col_name = '//*[@id="collection_Characters"]/div/h5'
        col_name = \
            BasePage.locator_finder_by_xpath(self, col_name)
        col_name.click()
        time.sleep(1)

        # get key text from the first row
        row_id = "//div[@id='docPureTable']/div[2]/div[1]"
        row_id = \
            BasePage.locator_finder_by_xpath(self, row_id)
        row_id.click()
        time.sleep(1)

        doc_key = 'document-key'
        doc_key = \
            BasePage.locator_finder_by_id(self, doc_key)
        key = doc_key.text
        time.sleep(2)

        self.selecting_query_page()

        time.sleep(1)
        self.enter_query('''
UPDATE "{key}"
    WITH {alive: false}
IN Characters''')

        # selecting execute query button
        execute_sitem =  self.locator_finder_by_id(
            self.execute_query_btn_id)
        execute_sitem.click()

        time.sleep(3)

        self.scroll()

        self.clear_query_area()

        print("Checking update query execution \n")
        self.enter_query('''
for doc in Characters
    FILTER doc.alive == false
RETURN doc''')
        time.sleep(1)

        print("Executing Update query \n")
        self.query_execution_btn()

        self.scroll()

        if self.webdriver.name == "chrome":  # this will check browser name
            print("Download has been disabled for the Chrome browser \n")
        else:
            print('Downloading query results \n')
            # downloading query results
            download_query_results = 'downloadQueryResult'
            download_query_results = \
                BasePage.locator_finder_by_id(self, download_query_results)
            download_query_results.click()
            time.sleep(3)

            # self.clear_download_bar()

            print('Downloading query results as CSV format \n')
            # downloading CSV query results
            csv = 'downloadCsvResult'
            csv = \
                BasePage.locator_finder_by_id(self, csv)
            csv.click()
            time.sleep(3)
            # self.clear_download_bar()

            # clear the execution area
            self.clear_query_area()

    def bind_parameters_query(self):
        """executing query with bind parameters"""
        # selecting query execution area
        bind_alive = self.bind_param_input_id % '1'
        bind_name  = self.bind_param_input_id % '2'
        self.enter_query('''
FOR doc IN Characters
    FILTER doc.alive == @alive && doc.name == @name
    RETURN doc''')

        bindv_block_sitem = self.locator_finder_by_xpath(self.bind_param_table_id)
        while not bindv_block_sitem.is_displayed():
            time.sleep(1)

        # bindv_alive_sitem = bindv_block_sitem.find_element_by_name('alive')
        # while not bindv_alive_sitem.is_displayed():
        #     time.sleep(1)
        # bindv_alive_sitem.click()
        # bindv_alive_sitem.send_keys('false')
        # BTS-559 workaround - don't use table editor
        # bindv_name_sitem = bindv_block_sitem.find_element_by_name('name')
        # while not bindv_name_sitem.is_displayed():
        #     time.sleep(1)
        # bindv_name_sitem.click()
        # bindv_name_sitem.send_keys('Ned')
        bind_editor_button_sitem = self.locator_finder_by_id('switchTypes')
        bind_editor_button_sitem.click()
        self.select_bindvalue_json_area()
        self.clear_all_text(self.bindvalues_area)
        self.send_key_action('''{ "alive": true, "name": "Ned" }''')

        # execute query with bind parameters
        self.query_execution_btn()

        self.scroll()

        json = self.json_to_table_span_it
        table = self.json_to_table_span_it

        print('Changing execution format JSON format to Table format\n')
        json = \
            BasePage.locator_finder_by_id(self, json)
        json.click()
        time.sleep(3)

        print('Changing execution format Table format to JSON format\n')
        table = \
            BasePage.locator_finder_by_id(self, table)
        table.click()
        time.sleep(3)

        print('Switch output to JSON format \n')
        output_switch_json = 'json-switch'
        output_switch_json = \
            BasePage.locator_finder_by_id(self, output_switch_json)
        output_switch_json.click()
        time.sleep(3)

        print('Switch output to Table format \n')
        output_switch_table = 'table-switch'
        output_switch_table = \
            BasePage.locator_finder_by_id(self, output_switch_table)
        output_switch_table.click()
        time.sleep(3)

        # clear the execution area
        self.clear_query_area()

    def import_queries(self, path):
        """importing new queries"""
        toggle_query = 'toggleQueries1'
        toggle_query = \
            BasePage.locator_finder_by_id(self, toggle_query)
        toggle_query.click()
        time.sleep(1)

        print('Importing query started \n')
        # import query
        imp_query = 'importQuery'
        imp_query = \
            BasePage.locator_finder_by_id(self, imp_query)
        imp_query.click()
        time.sleep(1)

        imp_queries = 'importQueries'
        imp_queries = \
            BasePage.locator_finder_by_id(self, imp_queries)
        time.sleep(2)
        imp_queries.send_keys(path)
        time.sleep(2)

        # confirm importing queries
        confirm_query = 'confirmQueryImport'
        confirm_query = \
            BasePage.locator_finder_by_id(self, confirm_query)
        confirm_query.click()
        time.sleep(1)
        print('Importing query completed \n')

        print("Checking imported query \n")
        run_query = 'runQuery'
        run_query = \
            BasePage.locator_finder_by_id(self, run_query)
        run_query.click()
        time.sleep(3)

        if self.webdriver.name == "chrome":  # this will check browser name
            print("Download has been disabled for the Chrome browser \n")
        else:
            print('Exporting newly imported query\n')
            select_imp_query = '//*[@id="arangoMyQueriesTable"]/tbody/tr[1]/td[1]'
            select_imp_query = \
                BasePage.locator_finder_by_xpath(self, select_imp_query)
            select_imp_query.click()
            time.sleep(1)

            export_query = 'exportQuery'
            export_query = \
                BasePage.locator_finder_by_id(self, export_query)
            export_query.click()
            # self.clear_download_bar()
        time.sleep(5)

        print('Deleting imported query \n')
        query = '//*[@id="arangoMyQueriesTable"]/tbody/tr[1]/td[1]'
        query = \
            BasePage.locator_finder_by_xpath(self, query)
        query.click()
        time.sleep(1)

        delete_query = 'deleteQuery'
        delete_query = \
            BasePage.locator_finder_by_id(self, delete_query)
        delete_query.click()
        time.sleep(1)

        del_btn = 'modalButton1'
        del_btn = \
            BasePage.locator_finder_by_id(self, del_btn)
        del_btn.click()
        time.sleep(1)

        del_confirm_btn = 'modal-confirm-delete'
        del_confirm_btn = \
            BasePage.locator_finder_by_id(self, del_confirm_btn)
        del_confirm_btn.click()
        time.sleep(1)

        print('Return back to query execution area \n')
        self.click_submenu_entry("Editor")
        time.sleep(1)

    def custom_query(self):
        """saving custom query and check slow query"""
        print("Executing Custom query\n")
        self.enter_query('return sleep(10)')

        save_query_sitem = self.locator_finder_by_id(self.save_current_query_id)
        save_query_sitem.click()

        query_name_sitem = self.locator_finder_by_id(self.new_query_name_id)
        query_name_sitem.click()
        query_name_sitem.send_keys('Custom query')

        btn_sitem = self.locator_finder_by_id('modalButton1')
        btn_sitem.click()

        # cleaning current query area
        self.clear_query_area()

        # checking saved query
        saved_query_sitem = self.locator_finder_by_id('toggleQueries1')
        saved_query_sitem.click()

        print('Checking custom query in action \n')
        explain_query_sitem = self.locator_finder_by_id("explQuery")
        explain_query_sitem.click()
        time.sleep(2)

        print('Clearing query results\n')
        remove_sitem = self.locator_finder_by_id(self.remove_all_results_id)
        remove_sitem.click()
        time.sleep(2)

        print("Running query from saved query\n")
        run_query_sitem = self.locator_finder_by_id('runQuery')
        run_query_sitem.click()
        time.sleep(2)

        print('Copying query from saved query\n')
        copy_query_sitem = self.locator_finder_by_id('copyQuery')
        copy_query_sitem.click()
        time.sleep(2)

        self.clear_query_area()

        print('Checking running query tab\n')
        self.click_submenu_entry("Running Queries")
        time.sleep(2)

        print('Checking slow query history \n')
        self.click_submenu_entry("Slow Query History")
        time.sleep(5)

        print('Deleting slow query history \n')
        del_slow_query_history_sitem = self.locator_finder_by_id('deleteSlowQueryHistory')
        del_slow_query_history_sitem.click()
        time.sleep(1)

        del_btn_sitem = self.locator_finder_by_id('modalButton1')
        del_btn_sitem.click()
        time.sleep(2)

        confirm_del_btn_sitem = self.locator_finder_by_id('modal-confirm-delete')
        confirm_del_btn_sitem.click()
        time.sleep(2)

        self.webdriver.refresh()

        # return back to saved query
        saved_query_01_sitem = self.locator_finder_by_id('toggleQueries1')
        saved_query_01_sitem.click()
        time.sleep(2)

        print('Deleting Saved query\n')
        delete_query_sitem = self.locator_finder_by_id('deleteQuery')
        delete_query_sitem.click()
        time.sleep(1)
        del_btn_sitem = self.locator_finder_by_id('modalButton1')
        del_btn_sitem.click()
        time.sleep(1)

        del_confirm_btn_sitem = self.locator_finder_by_id('modal-confirm-delete')
        del_confirm_btn_sitem.click()
        time.sleep(1)

        toggle_queries_sitem = self.locator_finder_by_id('toggleQueries2')
        toggle_queries_sitem.click()
        time.sleep(1)
        print('Deleting Saved query completed\n')
        self.clear_query_area()

    def world_country_graph_query(self):
        """Graph query"""

        self.selecting_query_page()
        self.clear_all_text(self.query_execution_area)

        print('Executing sample graph query for worldCountry Graph \n')
        self.enter_query('''
FOR v, e, p IN 1..1
    ANY "worldVertices/continent-south-america"
GRAPH "worldCountry"
    RETURN {v, e, p}''')

        time.sleep(2)

        self.query_execution_btn()

        self.scroll()

        self.webdriver.refresh()


    def k_shortest_paths_graph_query(self):
        """K Shortest Paths Graph Query"""

        # navigating back to query tab
        self.selecting_query_page()

        self.clear_all_text(self.query_execution_area)

        print('Executing sample graph query for KShortestPaths Graph')
        self.enter_query('''
FOR path IN OUTBOUND K_SHORTEST_PATHS
    "places/Birmingham" TO "places/StAndrews"
GRAPH "kShortestPathsGraph"
LIMIT 4
    RETURN path''')

        time.sleep(2)

        self.query_execution_btn()
        time.sleep(3)

        self.scroll(1)
        time.sleep(8)

        print('Switch output to JSON format')
        output_switch_json = 'json-switch'
        output_switch_json = \
            BasePage.locator_finder_by_id(self, output_switch_json)
        output_switch_json.click()

        self.select_query_execution_area()

        self.scroll(1)
        time.sleep(3)

        print('Switch output to Graph')
        output_switch_graph = 'graph-switch'
        output_switch_graph = \
            BasePage.locator_finder_by_id(self, output_switch_graph)
        output_switch_graph.click()

        execution_area1 = self.query_execution_area
        execution_area1 = \
            BasePage.locator_finder_by_xpath(self, execution_area1)
        execution_area1.click()
        time.sleep(1)

        self.scroll(1)
        time.sleep(3)

        print('Observe current query on Graph viewer \n')
        graph_page_btn = 'copy2gV'
        graph_page_btn = \
            BasePage.locator_finder_by_id(self, graph_page_btn)
        graph_page_btn.click()
        time.sleep(5)

        print('Navigate back to query page\n')
        self.selecting_query_page()

        print('Clear query execution area \n')
        self.clear_all_text(self.query_execution_area)

        print('Executing one more KShortestPaths graph query \n')
        self.enter_query('''
FOR v, e IN OUTBOUND SHORTEST_PATH "places/Aberdeen" TO "places/London"
    GRAPH "kShortestPathsGraph"
    RETURN { place: v.label, travelTime: e.travelTime }''')
        time.sleep(2)

        self.query_execution_btn()
        self.scroll()
        self.webdriver.refresh()

    def city_graph(self):
        """Example City Graph"""
        self.selecting_query_page()

        self.enter_query('for u in germanCity return u')
        time.sleep(1)

        # execute query
        self.query_execution_btn()

        self.scroll()

        time.sleep(1)

        print('Switch output to JSON format')
        output_switch_json = 'json-switch'
        output_switch_json = \
            BasePage.locator_finder_by_id(self, output_switch_json)
        output_switch_json.click()

        self.select_query_execution_area()
        self.scroll(1)

        print('Switch output to Table format')
        output_switch_table = 'table-switch'
        output_switch_table = \
            BasePage.locator_finder_by_id(self, output_switch_table)
        output_switch_table.click()

        self.select_query_execution_area()
        self.scroll(1)
        self.webdriver.refresh()

    def number_of_results(self):
        """changing the number of output"""
        self.select_query_execution_area()

        print('Changing query results size 1000 to 100 \n')
        query_size = self.select_query_size_id
        BasePage.locator_finder_by_select(self, query_size, 0)
        time.sleep(1)

        self.select_query_execution_area()

        print('Execute sample query\n')
        self.enter_query('''
FOR c IN imdb_vertices
    LIMIT 500
RETURN c''')
        time.sleep(2)

        self.query_execution_btn()

        self.scroll()

        self.webdriver.refresh()

    def delete_collection(self, collection):
        """Deleting Collection using any collections locator id"""
        collection = \
            BasePage.locator_finder_by_xpath(self, collection)
        collection.click()
        settings = self.collection_settings_id
        self.click_submenu_entry("Settings")

        delete_collection_id = "//*[@id='modalButton0']"
        delete_collection_id = \
            BasePage.locator_finder_by_xpath(self, delete_collection_id)
        delete_collection_id.click()
        time.sleep(2)

        delete_collection_confirm_id = "//*[@id='modal-confirm-delete']"
        delete_collection_confirm_id = \
            BasePage.locator_finder_by_xpath(self, delete_collection_confirm_id)
        delete_collection_confirm_id.click()

    def delete_all_collections(self):
        """deleting all the collections"""
        collection_page = 'collections'
        collection_page = \
            BasePage.locator_finder_by_id(self, collection_page)
        collection_page.click()
        time.sleep(2)

        print('deleting Characters collections \n')
        characters = '//*[@id="collection_Characters"]/div/h5'
        self.delete_collection(characters)

        print('deleting imdb_edges collections \n')
        imdb_edges = '//*[@id="collection_imdb_edges"]/div/h5'
        self.delete_collection(imdb_edges)

        print('deleting imdb_vertices collections \n')
        imdb_edges = '//*[@id="collection_imdb_vertices"]/div/h5'
        self.delete_collection(imdb_edges)

    def delete_all_graph(self, graph_id):
        """deleting any graphs with given graph id"""
        print('Navigating back to graph page \n')
        graph = self.graph_page
        graph = \
            BasePage.locator_finder_by_id(self, graph)
        graph.click()
        time.sleep(2)

        graphs_setting_btn_id = \
            BasePage.locator_finder_by_id(self, graph_id)
        graphs_setting_btn_id.click()
        time.sleep(1)

        confirm = self.confirm_delete_graph_id
        confirm = \
            BasePage.locator_finder_by_id(self, confirm)
        confirm.click()
        time.sleep(1)

        drop = self.drop_graph_collection
        drop = \
            BasePage.locator_finder_by_id(self, drop)
        drop.click()
        time.sleep(1)

        really = self.select_really_delete_btn_id
        really = \
            BasePage.locator_finder_by_id(self, really)
        really.click()
        time.sleep(3)

        # navigate back to query page
        self.selecting_query_page()

        # selecting query execution area
        self.select_query_execution_area()

        # clearing all text from the execution area
        self.clear_all_text(self.query_execution_area)