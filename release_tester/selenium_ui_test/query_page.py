#!/usr/bin/env python
"""
test the QUERY tab in the UI
"""

import time

import pyautogui

from selenium_ui_test.base_selenium import BaseSelenium

# can't circumvent long lines.. nAttr nLines
# pylint: disable=C0301 disable=R0902 disable=R0915 disable=R0914

class QueryPage(BaseSelenium):
    """Class for Query page"""

    def __init__(self, driver):
        """Query page initialization"""
        super().__init__()
        self.driver = driver
        self.selecting_query_page_id = "queries"
        self.query_execution_area = '//*[@id="aqlEditor"]'
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
        self.collection_settings_id = "//*[@id='subNavigationBar']/ul[2]/li[4]/a"
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

    def import_collections(self):
        """importing collections for query"""
        print("Navigating to Collection page \n")
        # Selecting collections page
        collections = "collections"
        collections = \
            BaseSelenium.locator_finder_by_id(self, collections)
        collections.click()
        time.sleep(1)

        cmd1 = 'cmd /c "arangorestore --server.endpoint tcp://127.0.0.1:8529 --input-directory ' \
               'release-test-automation\\test_data\\ui_data\\query_page\\IMDB_DUMP --server.username root ' \
               '--server.password "" ' \
               '--number-of-shards 9 --replication-factor 2"'
        super().command(cmd1)
        time.sleep(1)

        print('Creating a blank collection\n')
        create_collection = "createCollection"
        create_collection = \
            BaseSelenium.locator_finder_by_id(self, create_collection)
        create_collection.click()

        new_collection_name = 'new-collection-name'
        new_collection_name = \
            BaseSelenium.locator_finder_by_id(self, new_collection_name)
        new_collection_name.click()
        pyautogui.typewrite('Characters')

        new_collections_shards = 'new-collection-shards'
        new_collections_shards = \
            BaseSelenium.locator_finder_by_id(self, new_collections_shards)
        new_collections_shards.click()
        pyautogui.typewrite('9')

        new_replication_factor = 'new-replication-factor'
        new_replication_factor = \
            BaseSelenium.locator_finder_by_id(self, new_replication_factor)
        new_replication_factor.click()
        new_replication_factor.clear()
        new_replication_factor.click()
        pyautogui.typewrite('2')

        modal_button1 = 'modalButton1'
        modal_button1 = \
            BaseSelenium.locator_finder_by_id(self, modal_button1)
        modal_button1.click()

        self.driver.refresh()
        time.sleep(5)
        self.driver.back()
        time.sleep(1)

    def selecting_query_page(self):
        """Selecting query page"""
        query_page = self.selecting_query_page_id
        query_page = \
            BaseSelenium.locator_finder_by_id(self, query_page)
        query_page.click()
        time.sleep(1)

    def execute_query(self, query_name):
        """Executing query with given query string"""
        query = self.query_execution_area
        query = \
            BaseSelenium.locator_finder_by_xpath(self, query)
        query.click()

        super().query(query_name)
        time.sleep(2)

        # selecting execute query button
        execute = self.execute_query_btn_id
        execute = \
            BaseSelenium.locator_finder_by_id(self, execute)
        execute.click()

        time.sleep(3)

    def profile_query(self):
        """profiling query"""
        profile = self.profile_query_id
        profile = \
            BaseSelenium.locator_finder_by_id(self, profile)
        profile.click()
        time.sleep(2)

        super().scroll()

    def explain_query(self):
        """Downloading debug package"""
        explain_query = self.explain_query_id
        explain_query = \
            BaseSelenium.locator_finder_by_id(self, explain_query)
        explain_query.click()
        time.sleep(2)

    def debug_package_download(self):
        """Downloading debug package"""
        debug = self.create_debug_package_id
        debug = \
            BaseSelenium.locator_finder_by_id(self, debug)
        debug.click()
        time.sleep(2)
        debug_btn = 'modalButton1'
        debug_btn = \
            BaseSelenium.locator_finder_by_id(self, debug_btn)
        debug_btn.click()
        time.sleep(2)

    def remove_query_result(self):
        """Removing all query results"""
        remove_results = self.remove_all_results_id
        remove_results = \
            BaseSelenium.locator_finder_by_id(self, remove_results)
        remove_results.click()
        time.sleep(2)

    def clear_query_area(self):
        """Clearing current query area"""
        clear_query = self.query_execution_area
        clear_query = \
            BaseSelenium.locator_finder_by_xpath(self, clear_query)
        clear_query.click()

        super().clear_all_text()
        time.sleep(2)

    def spot_light_function(self, search):
        """Selecting spot light function helper"""
        spot_light = self.query_spot_light_id
        spot_light = \
            BaseSelenium.locator_finder_by_id(self, spot_light)
        spot_light.click()
        time.sleep(2)

        # searching for COUNT attribute
        pyautogui.typewrite(search)
        pyautogui.press('down', presses=5, interval=.5)
        time.sleep(1)
        pyautogui.press('up', presses=3, interval=.5)
        pyautogui.press('enter')
        time.sleep(2)

        self.clear_query_area()

    def update_documents(self):
        """Updating documents"""
        print("Navigating to Collection page \n")
        # Selecting collections page
        collections = "collections"
        collections = \
            BaseSelenium.locator_finder_by_id(self, collections)
        collections.click()
        time.sleep(1)

        col_name = '//*[@id="collection_Characters"]/div/h5'
        col_name = \
            BaseSelenium.locator_finder_by_xpath(self, col_name)
        col_name.click()
        time.sleep(1)

        # get key text from the first row
        row_id = "//div[@id='docPureTable']/div[2]/div[1]"
        row_id = \
            BaseSelenium.locator_finder_by_xpath(self, row_id)
        row_id.click()
        time.sleep(1)

        doc_key = 'document-key'
        doc_key = \
            BaseSelenium.locator_finder_by_id(self, doc_key)
        key = doc_key.text
        time.sleep(2)

        # selecting query page
        query_page = self.selecting_query_page_id
        query_page = \
            BaseSelenium.locator_finder_by_id(self, query_page)
        query_page.click()

        time.sleep(1)

        query = self.query_execution_area
        query = \
            BaseSelenium.locator_finder_by_xpath(self, query)
        query.click()

        key_updated = f"UPDATE \"{key}\""

        self.clear_query_area()
        time.sleep(1)

        query_def = key_updated + "\n\tWITH { alive: false }\nIN Characters"
        pyautogui.typewrite(query_def)

        # selecting execute query button
        execute = self.execute_query_btn_id
        execute = \
            BaseSelenium.locator_finder_by_id(self, execute)
        execute.click()

        time.sleep(3)

        super().scroll()

        self.clear_query_area()

        print("Checking update query execution \n")
        self.execute_query('for doc in Characters\n\tFILTER doc.alive == false\n\tRETURN doc')
        time.sleep(2)

        super().scroll()

        print('Downloading query results \n')
        # downloading query results
        download_query_results = 'downloadQueryResult'
        download_query_results = \
            BaseSelenium.locator_finder_by_id(self, download_query_results)
        download_query_results.click()
        time.sleep(3)
        super().clear_download_bar()

        print('Downloading query results as CSV format \n')
        # downloading CSV query results
        csv = 'downloadCsvResult'
        csv = \
            BaseSelenium.locator_finder_by_id(self, csv)
        csv.click()
        time.sleep(3)
        super().clear_download_bar()

        # clear the execution area
        self.clear_query_area()

    def bind_parameters_query(self):
        """executing query with bind parameters"""
        # selecting query execution area
        query_area = self.query_execution_area
        query_area = \
            BaseSelenium.locator_finder_by_xpath(self, query_area)
        query_area.click()

        # writing the query with bing parameters
        bind_query = 'FOR doc IN Characters\n\tFILTER doc.alive == @alive && doc.name == @name\n\tRETURN doc'
        bind_alive = '//*[@id="arangoBindParamTable"]/tbody/tr[1]/td[2]/input'
        bind_name = '//*[@id="arangoBindParamTable"]/tbody/tr[2]/td[2]/input'

        # writing the query with bind parameters
        self.query(bind_query)
        time.sleep(2)

        bind_query = \
            BaseSelenium.locator_finder_by_xpath(self, bind_alive)
        bind_query.click()
        pyautogui.typewrite('false')

        bind_alive = \
            BaseSelenium.locator_finder_by_xpath(self, bind_name)
        bind_alive.click()
        pyautogui.typewrite('Ned')

        # execute query with bind parameters
        execute = self.execute_query_btn_id
        execute = \
            BaseSelenium.locator_finder_by_id(self, execute)
        execute.click()
        time.sleep(5)

        super().scroll()

        json = self.json_to_table_span_it
        table = self.json_to_table_span_it

        print('Changing execution format JSON format to Table format\n')
        json = \
            BaseSelenium.locator_finder_by_id(self, json)
        json.click()
        time.sleep(3)

        print('Changing execution format Table format to JSON format\n')
        table = \
            BaseSelenium.locator_finder_by_id(self, table)
        table.click()
        time.sleep(3)

        print('Switch output to JSON format \n')
        output_switch_json = 'json-switch'
        output_switch_json = \
            BaseSelenium.locator_finder_by_id(self, output_switch_json)
        output_switch_json.click()
        time.sleep(3)

        print('Switch output to Table format \n')
        output_switch_table = 'table-switch'
        output_switch_table = \
            BaseSelenium.locator_finder_by_id(self, output_switch_table)
        output_switch_table.click()
        time.sleep(3)

        # clear the execution area
        self.clear_query_area()

    def import_queries(self, path):
        """importing new queries"""
        toggle_query = 'toggleQueries1'
        toggle_query = \
            BaseSelenium.locator_finder_by_id(self, toggle_query)
        toggle_query.click()
        time.sleep(1)

        print('Importing query started \n')
        # import query
        imp_query = 'importQuery'
        imp_query = \
            BaseSelenium.locator_finder_by_id(self, imp_query)
        imp_query.click()
        time.sleep(1)

        imp_queries = 'importQueries'
        imp_queries = \
            BaseSelenium.locator_finder_by_id(self, imp_queries)
        time.sleep(2)
        imp_queries.send_keys(path)
        time.sleep(2)

        # confirm importing queries
        confirm_query = 'confirmQueryImport'
        confirm_query = \
            BaseSelenium.locator_finder_by_id(self, confirm_query)
        confirm_query.click()
        time.sleep(1)
        print('Importing query completed \n')

        print("Checking imported query \n")
        run_query = 'runQuery'
        run_query = \
            BaseSelenium.locator_finder_by_id(self, run_query)
        run_query.click()
        time.sleep(3)

        print('Exporting newly imported query\n')
        select_imp_query = '//*[@id="arangoMyQueriesTable"]/tbody/tr[1]/td[1]'
        select_imp_query = \
            BaseSelenium.locator_finder_by_xpath(self, select_imp_query)
        select_imp_query.click()
        time.sleep(1)

        export_query = 'exportQuery'
        export_query = \
            BaseSelenium.locator_finder_by_id(self, export_query)
        export_query.click()
        time.sleep(3)

        super().clear_download_bar()

        time.sleep(5)

        print('Deleting imported query \n')
        query = '//*[@id="arangoMyQueriesTable"]/tbody/tr[1]/td[1]'
        query = \
            BaseSelenium.locator_finder_by_xpath(self, query)
        query.click()
        time.sleep(1)

        delete_query = 'deleteQuery'
        delete_query = \
            BaseSelenium.locator_finder_by_id(self, delete_query)
        delete_query.click()
        time.sleep(1)

        del_btn = 'modalButton1'
        del_btn = \
            BaseSelenium.locator_finder_by_id(self, del_btn)
        del_btn.click()
        time.sleep(1)

        del_confirm_btn = 'modal-confirm-delete'
        del_confirm_btn = \
            BaseSelenium.locator_finder_by_id(self, del_confirm_btn)
        del_confirm_btn.click()
        time.sleep(1)

        print('Return back to query execution area \n')
        editor_btn = '//*[@id="subNavigationBar"]/ul[2]/li[1]'
        editor_btn = \
            BaseSelenium.locator_finder_by_xpath(self, editor_btn)
        editor_btn.click()
        time.sleep(1)

    def custom_query(self):
        """saving custom query and check slow query"""
        self.clear_query_area()

        print("Executing Custom query\n")
        pyautogui.typewrite('return sleep(10)')

        save_query = self.save_current_query_id
        save_query = \
            BaseSelenium.locator_finder_by_id(self, save_query)
        save_query.click()

        query_name = self.new_query_name_id
        query_name = \
            BaseSelenium.locator_finder_by_id(self, query_name)
        query_name.click()
        pyautogui.typewrite('Custom query')

        btn = 'modalButton1'
        btn = \
            BaseSelenium.locator_finder_by_id(self, btn)
        btn.click()

        # cleaning current query area
        self.clear_query_area()

        # checking saved query
        saved_query = 'toggleQueries1'
        saved_query = \
            BaseSelenium.locator_finder_by_id(self, saved_query)
        saved_query.click()

        print('Checking custom query in action \n')
        explain_query = "explQuery"
        explain_query = \
            BaseSelenium.locator_finder_by_id(self, explain_query)
        explain_query.click()
        time.sleep(2)

        print('Clearing query results\n')
        remove = self.remove_all_results_id
        remove = \
            BaseSelenium.locator_finder_by_id(self, remove)
        remove.click()
        time.sleep(2)

        print("Running query from saved query\n")
        run_query = 'runQuery'
        run_query = \
            BaseSelenium.locator_finder_by_id(self, run_query)
        run_query.click()
        time.sleep(2)

        print('Copying query from saved query\n')
        copy_query = 'copyQuery'
        copy_query = \
            BaseSelenium.locator_finder_by_id(self, copy_query)
        copy_query.click()
        time.sleep(2)

        self.clear_query_area()

        print('Checking running query tab\n')
        slow_query = '//*[@id="subNavigationBar"]/ul[2]/li[2]/a'
        slow_query = \
            BaseSelenium.locator_finder_by_xpath(self, slow_query)
        slow_query.click()
        time.sleep(2)

        print('Checking slow query history \n')
        slow_query_history = '//*[@id="subNavigationBar"]/ul[2]/li[3]/a'
        slow_query_history = \
            BaseSelenium.locator_finder_by_xpath(self, slow_query_history)
        slow_query_history.click()
        time.sleep(5)

        print('Deleting slow query history \n')
        del_slow_query_history = 'deleteSlowQueryHistory'
        del_slow_query_history = \
            BaseSelenium.locator_finder_by_id(self, del_slow_query_history)
        del_slow_query_history.click()
        time.sleep(1)

        del_btn = 'modalButton1'
        del_btn = \
            BaseSelenium.locator_finder_by_id(self, del_btn)
        del_btn.click()
        time.sleep(2)

        confirm_del_btn = 'modal-confirm-delete'
        confirm_del_btn = \
            BaseSelenium.locator_finder_by_id(self, confirm_del_btn)
        confirm_del_btn.click()
        time.sleep(2)

        self.driver.refresh()

        # return back to saved query
        saved_query_01 = 'toggleQueries1'
        saved_query_01 = \
            BaseSelenium.locator_finder_by_id(self, saved_query_01)
        saved_query_01.click()
        time.sleep(2)

        print('Deleting Saved query\n')
        delete_query = 'deleteQuery'
        delete_query = \
            BaseSelenium.locator_finder_by_id(self, delete_query)
        delete_query.click()
        time.sleep(1)
        del_btn = 'modalButton1'
        del_btn = \
            BaseSelenium.locator_finder_by_id(self, del_btn)
        del_btn.click()
        time.sleep(1)

        del_confirm_btn = 'modal-confirm-delete'
        del_confirm_btn = \
            BaseSelenium.locator_finder_by_id(self, del_confirm_btn)
        del_confirm_btn.click()
        time.sleep(1)

        toggle_queries = 'toggleQueries2'
        toggle_queries = \
            BaseSelenium.locator_finder_by_id(self, toggle_queries)
        toggle_queries.click()
        time.sleep(1)
        print('Deleting Saved query completed\n')
        self.clear_query_area()

    def world_country_graph_query(self):
        """Graph query"""
        print('Creating worldCountry example graph \n')
        graph = self.graph_page
        graph = \
            BaseSelenium.locator_finder_by_id(self, graph)
        graph.click()
        time.sleep(2)

        select_graph = self.select_create_graph_id
        select_graph = \
            BaseSelenium.locator_finder_by_id(self, select_graph)
        select_graph.click()
        time.sleep(1)

        # Selecting example graph button
        example = self.select_example_graph_btn_id
        example = \
            BaseSelenium.locator_finder_by_id(self, example)
        example.click()
        time.sleep(1)

        # select worldCountry graph
        self.select_world_graph_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.select_world_graph_id)
        self.select_world_graph_id.click()
        time.sleep(4)

        # navigating back to query tab
        query = self.selecting_query_page_id
        query = \
            BaseSelenium.locator_finder_by_id(self, query)
        query.click()
        time.sleep(1)

        query_execution = self.query_execution_area
        query_execution = \
            BaseSelenium.locator_finder_by_xpath(self, query_execution)
        query_execution.click()
        time.sleep(1)

        # clear the execution area
        self.clear_query_area()

        print('Executing sample graph query for worldCountry Graph \n')
        query_name = 'FOR v, e, p IN 1..1\n\tANY "worldVertices/continent-south-america"\nGRAPH ' \
                     '"worldCountry"\nRETURN {v, e, p}'
        super().query(query_name)
        time.sleep(2)

        execute = self.execute_query_btn_id
        execute = \
            BaseSelenium.locator_finder_by_id(self, execute)
        execute.click()
        time.sleep(3)

        super().scroll()

        print('Deleting worldCountry graph \n')
        graph_id = "worldCountry_settings"
        self.delete_all_graph(graph_id)
        self.driver.refresh()

    def k_shortest_paths_graph_query(self):
        """K Shortest Paths Graph Query"""
        print('Creating KShortestPaths example graph \n')
        graph = self.graph_page
        graph = \
            BaseSelenium.locator_finder_by_id(self, graph)
        graph.click()
        time.sleep(2)

        select_graph = self.select_create_graph_id
        select_graph = \
            BaseSelenium.locator_finder_by_id(self, select_graph)
        select_graph.click()
        time.sleep(1)

        # Selecting example graph button
        graph_example_id = self.select_example_graph_btn_id
        graph_example_id = \
            BaseSelenium.locator_finder_by_id(self, graph_example_id)
        graph_example_id.click()
        time.sleep(1)

        # selecting kshortestpaths graph from example graph
        self.select_k_shortest_path_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.select_k_shortest_path_id)
        self.select_k_shortest_path_id.click()
        time.sleep(1)

        # navigating back to query tab
        query = self.selecting_query_page_id
        query = \
            BaseSelenium.locator_finder_by_id(self, query)
        query.click()
        time.sleep(1)

        query_execution = self.query_execution_area
        query_execution = \
            BaseSelenium.locator_finder_by_xpath(self, query_execution)
        query_execution.click()
        time.sleep(1)

        super().clear_all_text()

        print('Executing sample graph query for KShortestPaths Graph')
        query_name = 'FOR path IN OUTBOUND K_SHORTEST_PATHS\n\t"places/Birmingham" TO "places/StAndrews"\nGRAPH ' \
                     '"kShortestPathsGraph"\nLIMIT 4\nRETURN path '
        super().query(query_name)
        time.sleep(2)

        execute = self.execute_query_btn_id
        execute = \
            BaseSelenium.locator_finder_by_id(self, execute)
        execute.click()
        time.sleep(6)

        super().scroll(1)
        time.sleep(8)

        print('Switch output to JSON format')
        output_switch_json = 'json-switch'
        output_switch_json = \
            BaseSelenium.locator_finder_by_id(self, output_switch_json)
        output_switch_json.click()

        execution_area = self.query_execution_area
        execution_area = \
            BaseSelenium.locator_finder_by_xpath(self, execution_area)
        execution_area.click()
        time.sleep(1)

        super().scroll(1)
        time.sleep(3)

        print('Switch output to Graph')
        output_switch_graph = 'graph-switch'
        output_switch_graph = \
            BaseSelenium.locator_finder_by_id(self, output_switch_graph)
        output_switch_graph.click()

        execution_area1 = self.query_execution_area
        execution_area1 = \
            BaseSelenium.locator_finder_by_xpath(self, execution_area1)
        execution_area1.click()
        time.sleep(1)

        super().scroll(1)
        time.sleep(3)

        print('Observe current query on Graph viewer \n')
        graph_page_btn = 'copy2gV'
        graph_page_btn = \
            BaseSelenium.locator_finder_by_id(self, graph_page_btn)
        graph_page_btn.click()
        time.sleep(5)

        print('Navigate back to query page\n')
        query_page = self.selecting_query_page_id
        query_page = \
            BaseSelenium.locator_finder_by_id(self, query_page)
        query_page.click()
        time.sleep(2)

        # selecting query execution area
        query01 = self.query_execution_area
        query01 = \
            BaseSelenium.locator_finder_by_xpath(self, query01)
        query01.click()

        print('Clear query execution area \n')
        super().clear_all_text()

        print('Executing one more KShortestPaths graph query \n')
        query_example = 'FOR v, e IN OUTBOUND SHORTEST_PATH "places/Aberdeen" TO "places/London"\n\tGRAPH ' \
                        '"kShortestPathsGraph"\nRETURN { place: v.label, travelTime: e.travelTime }'
        super().query(query_example)
        time.sleep(2)

        execute2 = self.execute_query_btn_id
        execute2 = \
            BaseSelenium.locator_finder_by_id(self, execute2)
        execute2.click()
        time.sleep(2)

        super().scroll()

        print('Deleting KShortestPath graph \n')
        graph_id = "kShortestPathsGraph_settings"
        self.delete_all_graph(graph_id)
        self.driver.refresh()

    def city_graph(self):
        """Example City Graph"""
        print('Creating example City Graph \n')
        graph = self.graph_page
        graph = \
            BaseSelenium.locator_finder_by_id(self, graph)
        graph.click()
        time.sleep(2)

        select_graph = self.select_create_graph_id
        select_graph = \
            BaseSelenium.locator_finder_by_id(self, select_graph)
        select_graph.click()
        time.sleep(1)

        # Selecting example graph button
        graph_example_id = self.select_example_graph_btn_id
        graph_example_id = \
            BaseSelenium.locator_finder_by_id(self, graph_example_id)
        graph_example_id.click()
        time.sleep(1)

        # selecting City Graph from example
        route_planner = '//*[@id="exampleGraphs"]/table/tbody/tr[7]/td[2]/button'
        route_planner = \
            BaseSelenium.locator_finder_by_xpath(self, route_planner)
        route_planner.click()
        time.sleep(4)

        # navigating back to query tab
        query = self.selecting_query_page_id
        query = \
            BaseSelenium.locator_finder_by_id(self, query)
        query.click()
        time.sleep(1)

        query_execution = self.query_execution_area
        query_execution = \
            BaseSelenium.locator_finder_by_xpath(self, query_execution)
        query_execution.click()
        time.sleep(1)

        super().clear_all_text()

        map_query = 'for u in germanCity return u'
        self.query(map_query)
        time.sleep(1)

        # execute query
        execute = self.execute_query_btn_id
        execute = \
            BaseSelenium.locator_finder_by_id(self, execute)
        execute.click()
        time.sleep(3)

        super().scroll()

        time.sleep(1)

        print('Switch output to JSON format')
        output_switch_json = 'json-switch'
        output_switch_json = \
            BaseSelenium.locator_finder_by_id(self, output_switch_json)
        output_switch_json.click()

        query01 = self.query_execution_area
        query01 = \
            BaseSelenium.locator_finder_by_xpath(self, query01)
        query01.click()
        super().scroll(1)

        print('Switch output to Table format')
        output_switch_table = 'table-switch'
        output_switch_table = \
            BaseSelenium.locator_finder_by_id(self, output_switch_table)
        output_switch_table.click()

        query02 = self.query_execution_area
        query02 = \
            BaseSelenium.locator_finder_by_xpath(self, query02)
        query02.click()
        super().scroll(1)

        print('Deleting City graph \n')
        graph_id = "routeplanner_settings"
        self.delete_all_graph(graph_id)
        self.driver.refresh()

    def number_of_results(self):
        """changing the number of output"""
        query = self.query_execution_area
        query = \
            BaseSelenium.locator_finder_by_xpath(self, query)
        query.click()
        time.sleep(1)

        print('Changing query results size 1000 to 100 \n')
        query_size = self.select_query_size_id
        BaseSelenium.locator_finder_by_select(self, query_size, 0)
        time.sleep(1)

        query_01 = self.query_execution_area
        query_01 = \
            BaseSelenium.locator_finder_by_xpath(self, query_01)
        query_01.click()
        time.sleep(1)

        print('Execute sample query\n')
        self.query('FOR c IN imdb_vertices\n\tLIMIT 500\nRETURN c')
        time.sleep(2)

        execute = self.execute_query_btn_id
        execute = \
            BaseSelenium.locator_finder_by_id(self, execute)
        execute.click()
        time.sleep(1)

        super().scroll()

        self.driver.refresh()

    def delete_collection(self, collection):
        """Deleting Collection using any collections locator id"""
        collection = \
            BaseSelenium.locator_finder_by_xpath(self, collection)
        collection.click()
        settings = self.collection_settings_id
        settings = \
            BaseSelenium.locator_finder_by_xpath(self, settings)
        settings.click()

        delete_collection_id = "//*[@id='modalButton0']"
        delete_collection_id = \
            BaseSelenium.locator_finder_by_xpath(self, delete_collection_id)
        delete_collection_id.click()
        time.sleep(2)

        delete_collection_confirm_id = "//*[@id='modal-confirm-delete']"
        delete_collection_confirm_id = \
            BaseSelenium.locator_finder_by_xpath(self, delete_collection_confirm_id)
        delete_collection_confirm_id.click()

    def delete_all_collections(self):
        """deleting all the collections"""
        collection_page = 'collections'
        collection_page = \
            BaseSelenium.locator_finder_by_id(self, collection_page)
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
            BaseSelenium.locator_finder_by_id(self, graph)
        graph.click()
        time.sleep(2)

        graphs_setting_btn_id = \
            BaseSelenium.locator_finder_by_id(self, graph_id)
        graphs_setting_btn_id.click()
        time.sleep(1)

        confirm = self.confirm_delete_graph_id
        confirm = \
            BaseSelenium.locator_finder_by_id(self, confirm)
        confirm.click()
        time.sleep(1)

        drop = self.drop_graph_collection
        drop = \
            BaseSelenium.locator_finder_by_id(self, drop)
        drop.click()
        time.sleep(1)

        really = self.select_really_delete_btn_id
        really = \
            BaseSelenium.locator_finder_by_id(self, really)
        really.click()
        time.sleep(3)

        # navigate back to query page
        query_page = self.selecting_query_page_id
        query_page = \
            BaseSelenium.locator_finder_by_id(self, query_page)
        query_page.click()
        time.sleep(3)

        # selecting query execution area
        query = self.query_execution_area
        query = \
            BaseSelenium.locator_finder_by_xpath(self, query)
        query.click()

        # clearing all text from the execution area
        super().clear_all_text()
