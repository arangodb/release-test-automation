#!/usr/bin/env python3
""" query page object """
import time
import semver

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_ui_test.pages.navbar import NavigationBarPage

# can't circumvent long lines.. nAttr nLines
# pylint: disable=line-too-long disable=too-many-instance-attributes disable=too-many-statements disable=too-many-locals disable=too-many-public-methods


class QueryPage(NavigationBarPage):
    """Class for Query page"""

    def __init__(self, driver, cfg, video_start_time):
        """Query page initialization"""
        super().__init__(driver, cfg, video_start_time)
        self.selecting_query_page_id = "queries"
        self.execute_query_btn_id = "executeQuery"
        self.profile_query_id = "profileQuery"
        self.explain_query_id = "explainQuery"
        self.create_debug_package_id = "debugQuery"
        self.remove_all_results_id = "removeResults"
        self.query_spot_light_id = "querySpotlight"
        self.save_current_query_id = "saveCurrentQuery"
        self.new_query_name_id = "new-query-name"
        self.select_query_size_id = "querySize"
        # self.json_to_table_span_it = "switchTypes"
        self.collection_settings_id = "//*[@id='subNavigationBarPage']/ul[2]/li[4]/a"
        self.graph_page = "graphs"
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
        self.bind_param_input_id = self.bind_param_table_id + "/tbody/tr[%s]/td[2]/input"

    def import_collections(self, restore, testdata_path, is_cluster):
        """importing collections for query"""
        self.tprint("Navigating to Collection page \n")
        # Selecting collections page
        self.navbar_goto("collections")
        self.webdriver.refresh()
        data_path = testdata_path / "ui_data" / "query_page" / "IMDB_DUMP"
        self.tprint(data_path)
        ret = restore.run_restore_monitored(
            str(data_path.absolute()), ["--number-of-shards", "9", "--replication-factor", "2"], 40
        )
        if not ret[0]:
            raise Exception("restoring failed: " + str(ret[1]))

        self.tprint("Creating a blank collection\n")
        create_collection = "createCollection"
        create_collection_sitem = self.locator_finder_by_id(create_collection)
        create_collection_sitem.click()

        new_collection_name = "new-collection-name"
        new_collection_name_sitem = self.locator_finder_by_id(new_collection_name)
        new_collection_name_sitem.click()
        new_collection_name_sitem.send_keys("Characters")
        if is_cluster:
            new_collections_shards = "new-collection-shards"
            new_collections_shards_sitem = WebDriverWait(self.webdriver, 15).until(
                EC.element_to_be_clickable((By.ID, new_collections_shards)), message="failed to get shards input field"
            )
            new_collections_shards_sitem.click()
            new_collections_shards_sitem.send_keys("9")

            new_replication_factor = "new-replication-factor"
            new_replication_factor_sitem = self.locator_finder_by_id(new_replication_factor)
            new_replication_factor_sitem.click()
            new_replication_factor_sitem.clear()
            new_replication_factor_sitem.click()
            new_replication_factor_sitem.send_keys("2")
        modal_button1_str = "modalButton1"
        modal_button1_sitem = WebDriverWait(self.webdriver, 15).until(
            EC.element_to_be_clickable((By.ID, modal_button1_str)), message="failed to wait for collection save button"
        )
        modal_button1_sitem.click()
        # new_collection_name_sitem.send_keys(Keys.ENTER)

        self.webdriver.refresh()
        time.sleep(5)
        self.webdriver.back()
        time.sleep(1)

    def enter_query(self, query_string):
        """type a query into the editor line by line"""
        self.select_query_execution_area()
        self.clear_all_text(self.query_execution_area)
        for line in query_string.split("\n"):
            if len(line) > 0:  # skip empty lines in heredocuments
                self.send_key_action(line)
                self.send_key_action(Keys.ENTER)
        self.wait_for_ajax()

    def selecting_query_page(self):
        """Selecting query page"""
        self.navbar_goto("queries")
        self.webdriver.refresh()

    def execute_insert_query(self):
        """This method will run an insert query"""
        self.clear_query_area()

        query = """
for i IN 1..10000
    INSERT {
       "name": "Ned",
"surname": "Stark",
"alive": true,
"age": 41,
"traits": ["A","H","C","N","P"]
} INTO Characters
"""
        self.enter_query(query)
        self.query_execution_btn()
        self.scroll(1)

    def execute_read_query(self):
        """This method will run a read query"""
        self.enter_query(
            """
FOR c IN imdb_vertices
    LIMIT 500
RETURN c
"""
        )

        # selecting execute query button
        self.query_execution_btn()

        self.scroll(1)

    def profile_query(self):
        """profiling query"""
        self.wait_for_ajax()
        profile = self.profile_query_id
        profile = self.locator_finder_by_id(profile)
        profile.click()
        time.sleep(2)

        self.scroll()

    def explain_query(self):
        """Explaining query"""
        self.wait_for_ajax()
        self.webdriver.refresh()
        explain_query_sitem = self.locator_finder_by_id(self.explain_query_id)
        explain_query_sitem.click()
        time.sleep(2)

    def debug_package_download(self):
        """Downloading debug package"""
        if self.webdriver.name == "chrome":  # this will check browser name
            self.tprint("Download has been disabled for the Chrome browser \n")
        else:
            debug = self.create_debug_package_id
            debug = self.locator_finder_by_id(debug)
            debug.click()
            time.sleep(2)
            debug_btn = "modalButton1"
            debug_btn = self.locator_finder_by_id(debug_btn)
            debug_btn.click()
            time.sleep(2)
            # self.clear_download_bar()

    def remove_query_result(self):
        """Removing all query results"""
        remove_results = self.remove_all_results_id
        remove_results = self.locator_finder_by_id(remove_results)
        remove_results.click()
        time.sleep(2)

    def clear_query_area(self):
        """Clearing current query area"""
        self.clear_all_text(self.query_execution_area)
        time.sleep(2)

    def spot_light_function(self, search):
        """trigger the spotlight function"""
        spot_light = self.query_spot_light_id
        spot_light = self.locator_finder_by_id(spot_light)
        spot_light.click()
        time.sleep(2)

        # searching for COUNT attribute
        self.send_key_action(search)
        self.send_key_action(Keys.DOWN * 5)
        time.sleep(1)

        self.send_key_action(Keys.UP * 3)
        self.send_key_action(Keys.ENTER)
        time.sleep(2)

    def navigate_to_col_content_tab(self):
        """ this method will take to collection content tab"""
        content = "//div[@id='subNavigationBar']/ul[2]//a[.='Content']"
        content_sitem = self.locator_finder_by_xpath(content)
        content_sitem.click()
        time.sleep(1)

    def update_documents(self):
        """update some documents"""
        self.tprint("Navigating to Collection page \n")
        # Selecting collections page
        collections = "collections"
        collections = self.locator_finder_by_id(collections)
        collections.click()
        time.sleep(1)

        col_name = '//*[@id="collection_Characters"]/div/h5'
        col_name = self.locator_finder_by_xpath(col_name)
        col_name.click()
        time.sleep(1)
        
        self.navigate_to_col_content_tab()

        # get key text from the first row
        row_id = "//div[@id='docPureTable']/div[2]/div[1]"
        row_id = self.locator_finder_by_xpath(row_id)
        row_id.click()
        time.sleep(1)

        doc_key = "document-key"
        doc_key_sitem = self.locator_finder_by_id(doc_key)
        key = doc_key_sitem.text
        time.sleep(2)

        self.selecting_query_page()

        time.sleep(1)
        self.enter_query(
            """
UPDATE "{key}"
    WITH {{alive: false}}
IN Characters""".format(key=key)
        )

        # selecting execute query button
        execute_sitem = self.locator_finder_by_id(self.execute_query_btn_id)
        execute_sitem.click()

        time.sleep(3)

        self.scroll()

        self.clear_query_area()

        self.tprint("Checking update query execution \n")
        self.enter_query(
            """
for doc in Characters
    FILTER doc.alive == false
RETURN doc"""
        )
        time.sleep(1)

        self.tprint("Executing Update query \n")
        self.query_execution_btn()

        self.scroll()

        if self.webdriver.name == "chrome":  # this will check browser name
            self.tprint("Download has been disabled for the Chrome browser \n")
        else:
            self.tprint("Downloading query results \n")
            # downloading query results
            download_query_results = "downloadQueryResult"
            download_query_results = self.locator_finder_by_id(download_query_results)
            download_query_results.click()
            time.sleep(3)

            # self.clear_download_bar()

            self.tprint("Downloading query results as CSV format \n")
            # downloading CSV query results
            csv = "downloadCsvResult"
            csv = self.locator_finder_by_id(csv)
            csv.click()
            time.sleep(3)
            # self.clear_download_bar()

            # clear the execution area
            self.clear_query_area()

    def bind_parameters_query(self):
        """executing query with bind parameters"""
        # selecting query execution area
        # TODO: re-add or delete bind values
        # bind_alive = self.bind_param_input_id % "1"
        # bind_name = self.bind_param_input_id % "2"
        self.enter_query(
            """
FOR doc IN Characters
    FILTER doc.alive == @alive && doc.name == @name
    RETURN doc"""
        )

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
        bind_editor_button_sitem = self.locator_finder_by_id("switchTypes")
        bind_editor_button_sitem.click()
        self.select_bindvalue_json_area()
        self.clear_all_text(self.bindvalues_area)
        self.send_key_action("""{ "alive": true, "name": "Ned" }""")

        # execute query with bind parameters
        self.query_execution_btn()

        self.scroll()

        if self.current_package_version() >= semver.VersionInfo.parse("3.11.0"):
            self.tprint("Json/table toggle check is skipped for 3.11.0+")
        else:
            json = "//*[text()='JSON']"
            table = "//*[text()='Table']"

            self.tprint("Changing execution format JSON format to Table format\n")
            json = self.locator_finder_by_xpath(json)
            json.click()
            time.sleep(3)

            self.tprint("Changing execution format Table format to JSON format\n")
            table = self.locator_finder_by_xpath(table)
            table.click()
            time.sleep(3)

            self.tprint("Switch output to JSON format \n")
            output_switch_json = "json-switch"
            output_switch_json = self.locator_finder_by_id(output_switch_json)
            output_switch_json.click()
            time.sleep(3)

            self.tprint("Switch output to Table format \n")
            output_switch_table = "table-switch"
            output_switch_table = self.locator_finder_by_id(output_switch_table)
            output_switch_table.click()
            time.sleep(3)

        # clear the execution area
        self.clear_query_area()

    def import_queries(self, path):
        """importing new queries"""
        toggle_query = "toggleQueries1"
        toggle_query = self.locator_finder_by_id(toggle_query)
        toggle_query.click()
        time.sleep(1)

        self.tprint("Importing query started \n")
        # import query
        imp_query = "importQuery"
        imp_query = self.locator_finder_by_id(imp_query)
        imp_query.click()
        time.sleep(1)

        imp_queries = "importQueries"
        imp_queries = self.locator_finder_by_id(imp_queries)
        time.sleep(2)
        imp_queries.send_keys(path)
        time.sleep(2)

        # confirm importing queries
        confirm_query = "confirmQueryImport"
        confirm_query = self.locator_finder_by_id(confirm_query)
        confirm_query.click()
        time.sleep(1)
        self.tprint("Importing query completed \n")

        self.tprint("Checking imported query \n")
        run_query = "runQuery"
        run_query = self.locator_finder_by_id(run_query)
        run_query.click()
        time.sleep(3)

        if self.webdriver.name == "chrome":  # this will check browser name
            self.tprint("Download has been disabled for the Chrome browser \n")
        else:
            self.tprint("Exporting newly imported query\n")
            select_imp_query = '//*[@id="arangoMyQueriesTable"]/tbody/tr[1]/td[1]'
            select_imp_query = self.locator_finder_by_xpath(select_imp_query)
            select_imp_query.click()
            time.sleep(1)

            export_query = "exportQuery"
            export_query = self.locator_finder_by_id(export_query)
            export_query.click()
            # self.clear_download_bar()
        time.sleep(5)

        self.tprint("Deleting imported query \n")
        query = '//*[@id="arangoMyQueriesTable"]/tbody/tr[1]/td[1]'
        query = self.locator_finder_by_xpath(query)
        query.click()
        time.sleep(1)

        delete_query = "deleteQuery"
        delete_query = self.locator_finder_by_id(delete_query)
        delete_query.click()
        time.sleep(1)

        del_btn = "modalButton1"
        del_btn = self.locator_finder_by_id(del_btn)
        del_btn.click()
        time.sleep(1)

        del_confirm_btn = "modal-confirm-delete"
        del_confirm_btn = self.locator_finder_by_id(del_confirm_btn)
        del_confirm_btn.click()
        time.sleep(1)

        self.tprint("Return back to query execution area \n")
        self.click_submenu_entry("Editor")
        time.sleep(1)

    def custom_query(self):
        """saving custom query and check slow query"""
        self.tprint("Executing Custom query\n")
        self.enter_query("return sleep(10)")

        save_query_sitem = self.locator_finder_by_id(self.save_current_query_id)
        save_query_sitem.click()

        query_name_sitem = self.locator_finder_by_id(self.new_query_name_id)
        query_name_sitem.click()
        query_name_sitem.send_keys("Custom query")

        btn_sitem = self.locator_finder_by_id("modalButton1")
        btn_sitem.click()

        # cleaning current query area
        self.clear_query_area()

        # checking saved query
        saved_query_sitem = self.locator_finder_by_id("toggleQueries1")
        saved_query_sitem.click()

        self.tprint("Checking custom query in action \n")
        explain_query_sitem = self.locator_finder_by_id("explQuery")
        explain_query_sitem.click()
        time.sleep(2)

        self.tprint("Clearing query results\n")
        remove_sitem = self.locator_finder_by_id(self.remove_all_results_id)
        remove_sitem.click()
        time.sleep(2)

        self.tprint("Running query from saved query\n")
        run_query_sitem = self.locator_finder_by_id("runQuery")
        run_query_sitem.click()
        time.sleep(2)

        self.tprint("Copying query from saved query\n")
        copy_query_sitem = self.locator_finder_by_id("copyQuery")
        copy_query_sitem.click()
        time.sleep(2)

        self.clear_query_area()

        self.tprint("Checking running query tab\n")
        self.click_submenu_entry("Running Queries")
        time.sleep(2)

        self.tprint("Checking slow query history \n")
        self.click_submenu_entry("Slow Query History")
        time.sleep(5)

        self.tprint("Deleting slow query history \n")
        del_slow_query_history_sitem = self.locator_finder_by_id("deleteSlowQueryHistory")
        del_slow_query_history_sitem.click()
        time.sleep(1)

        del_btn_sitem = self.locator_finder_by_id("modalButton1")
        del_btn_sitem.click()
        time.sleep(2)

        confirm_del_btn_sitem = self.locator_finder_by_id("modal-confirm-delete")
        confirm_del_btn_sitem.click()
        time.sleep(2)

        self.webdriver.refresh()

        # return back to saved query
        saved_query_01_sitem = self.locator_finder_by_id("toggleQueries1")
        saved_query_01_sitem.click()
        time.sleep(2)

        self.tprint("Deleting Saved query\n")
        delete_query_sitem = self.locator_finder_by_id("deleteQuery")
        delete_query_sitem.click()
        time.sleep(1)
        del_btn_sitem = self.locator_finder_by_id("modalButton1")
        del_btn_sitem.click()
        time.sleep(1)

        del_confirm_btn_sitem = self.locator_finder_by_id("modal-confirm-delete")
        del_confirm_btn_sitem.click()
        time.sleep(1)

        toggle_queries_sitem = self.locator_finder_by_id("toggleQueries2")
        toggle_queries_sitem.click()
        time.sleep(1)
        self.tprint("Deleting Saved query completed\n")
        self.clear_query_area()

    def world_country_graph_query(self):
        """Graph query"""

        self.selecting_query_page()
        self.clear_all_text(self.query_execution_area)

        self.tprint("Executing sample graph query for worldCountry Graph \n")
        self.enter_query(
            """
        FOR v, e, p IN 1..1
            ANY "worldVertices/continent-south-america"
        GRAPH "worldCountry"
            RETURN {v, e, p}"""
        )

        time.sleep(2)

        self.query_execution_btn()

        self.scroll()

        self.webdriver.refresh()

    def k_shortest_paths_graph_query(self):
        """K Shortest Paths Graph Query"""

        # navigating back to query tab
        self.selecting_query_page()

        self.clear_all_text(self.query_execution_area)

        self.tprint("Executing sample graph query for KShortestPaths Graph")
        self.enter_query(
            """
            FOR path IN OUTBOUND K_SHORTEST_PATHS
                "places/Birmingham" TO "places/StAndrews"
            GRAPH "kShortestPathsGraph"
            LIMIT 4
                RETURN path"""
        )

        time.sleep(2)

        self.query_execution_btn()
        time.sleep(3)

        self.scroll(1)
        time.sleep(8)

        self.tprint("Switch output to JSON format")
        output_switch_json = "json-switch"
        output_switch_json = self.locator_finder_by_id(output_switch_json)
        output_switch_json.click()

        self.select_query_execution_area()

        self.scroll(1)
        time.sleep(3)

        self.tprint("Switch output to Graph")
        output_switch_graph = "graph-switch"
        output_switch_graph = self.locator_finder_by_id(output_switch_graph)
        output_switch_graph.click()

        execution_area1 = self.query_execution_area
        execution_area1 = self.locator_finder_by_xpath(execution_area1)
        execution_area1.click()
        time.sleep(1)

        self.scroll(1)
        time.sleep(3)

        self.tprint("Observe current query on Graph viewer \n")
        graph_page_btn = "copy2gV"
        graph_page_btn = self.locator_finder_by_id(graph_page_btn)
        graph_page_btn.click()
        time.sleep(5)

        self.tprint("Navigate back to query page\n")
        self.selecting_query_page()

        self.tprint("Clear query execution area \n")
        self.clear_all_text(self.query_execution_area)

        self.tprint("Executing one more KShortestPaths graph query \n")
        self.enter_query(
            """
            FOR v, e IN OUTBOUND SHORTEST_PATH "places/Aberdeen" TO "places/London"
                GRAPH "kShortestPathsGraph"
                RETURN { place: v.label, travelTime: e.travelTime }"""
        )
        time.sleep(2)

        self.query_execution_btn()
        self.scroll()
        self.webdriver.refresh()

    def city_graph(self):
        """Example City Graph"""
        self.selecting_query_page()

        self.enter_query("for u in germanCity return u")
        time.sleep(1)

        # execute query
        self.query_execution_btn()

        self.scroll()

        time.sleep(1)

        self.tprint("Switch output to JSON format")
        output_switch_json = "json-switch"
        output_switch_json = self.locator_finder_by_id(output_switch_json)
        output_switch_json.click()

        self.select_query_execution_area()
        self.scroll(1)

        self.tprint("Switch output to Table format")
        output_switch_table = "table-switch"
        output_switch_table = self.locator_finder_by_id(output_switch_table)
        output_switch_table.click()

        self.select_query_execution_area()
        self.scroll(1)
        self.webdriver.refresh()

    def number_of_results(self):
        """changing the number of output"""
        self.select_query_execution_area()

        self.tprint("Changing query results size 1000 to 100 \n")
        query_size = self.select_query_size_id
        self.locator_finder_by_select(query_size, 0)
        time.sleep(1)

        self.select_query_execution_area()

        self.tprint("Execute sample query\n")
        self.enter_query(
            """
            FOR c IN imdb_vertices
                LIMIT 500
            RETURN c"""
        )
        time.sleep(2)

        self.query_execution_btn()

        self.scroll()

        self.webdriver.refresh()

    def delete_collection(self, collection):
        """Deleting Collection using any collections locator id"""
        collection = self.locator_finder_by_xpath(collection)
        collection.click()
        # TODO: delete? settings = self.collection_settings_id
        self.click_submenu_entry("Settings")

        delete_collection_id = "//*[@id='modalButton0']"
        delete_collection_id = self.locator_finder_by_xpath(delete_collection_id)
        delete_collection_id.click()
        time.sleep(2)

        delete_collection_confirm_id = "//*[@id='modal-confirm-delete']"
        delete_collection_confirm_id = self.locator_finder_by_xpath(delete_collection_confirm_id)
        delete_collection_confirm_id.click()

    def delete_all_collections(self):
        """deleting all the collections"""
        collection_page = "collections"
        collection_page = self.locator_finder_by_id(collection_page)
        collection_page.click()
        time.sleep(2)

        self.tprint("deleting Characters collections \n")
        characters = '//*[@id="collection_Characters"]/div/h5'
        self.delete_collection(characters)

        self.tprint("deleting imdb_edges collections \n")
        imdb_edges = '//*[@id="collection_imdb_edges"]/div/h5'
        self.delete_collection(imdb_edges)

        self.tprint("deleting imdb_vertices collections \n")
        imdb_edges = '//*[@id="collection_imdb_vertices"]/div/h5'
        self.delete_collection(imdb_edges)

    def delete_all_graph(self, graph_id):
        """deleting any graphs with given graph id"""
        self.tprint("Navigating back to graph page \n")
        graph = self.graph_page
        graph = self.locator_finder_by_id(graph)
        graph.click()
        time.sleep(2)

        graphs_setting_btn_id = self.locator_finder_by_id(graph_id)
        graphs_setting_btn_id.click()
        time.sleep(1)

        confirm = self.confirm_delete_graph_id
        confirm = self.locator_finder_by_id(confirm)
        confirm.click()
        time.sleep(1)

        drop = self.drop_graph_collection
        drop = self.locator_finder_by_id(drop)
        drop.click()
        time.sleep(1)

        really = self.select_really_delete_btn_id
        really = self.locator_finder_by_id(really)
        really.click()
        time.sleep(3)

        # navigate back to query page
        self.selecting_query_page()

        # selecting query execution area
        self.select_query_execution_area()

        # clearing all text from the execution area
        self.clear_all_text(self.query_execution_area)

    def delete_saved_query(self):
        """This method will delete all the saved query"""
        delete = '//i[@class="fa fa-minus-circle"]'
        delete_sitem = self.locator_finder_by_xpath(delete)
        delete_sitem.click()
        time.sleep(1)

        delete_confirm = 'modalButton1'
        delete_confirm_sitem = self.locator_finder_by_id(delete_confirm)
        delete_confirm_sitem.click()
        time.sleep(1)

        delete_final = 'modal-confirm-delete'
        delete_final_sitem = self.locator_finder_by_id(delete_final)
        delete_final_sitem.click()
        time.sleep(1)

    def saved_query_settings(self):
        """this method will check saved query sorting setting"""
        settings = 'sortOptionsToggle'
        settings_sitem = self.locator_finder_by_id(settings)
        settings_sitem.click()
        time.sleep(1)

        sort_by_date_created = "sortDateAdded"
        sort_by_date_created_sitem = self.locator_finder_by_id(sort_by_date_created)
        sort_by_date_created_sitem.click()
        time.sleep(1)

        sort_by_date_modified = "sortDateModified"
        sort_by_date_modified_sitem = self.locator_finder_by_id(sort_by_date_modified)
        sort_by_date_modified_sitem.click()
        time.sleep(1)

        query_sort_order = "querySortOrder"
        query_sort_order_sitem = self.locator_finder_by_id(query_sort_order)
        query_sort_order_sitem.click()
        time.sleep(1)

    def toggle_query_btn(self):
        """This method will toggle the saved query button"""
        toggle_query = 'toggleQueries1'
        toggle_query = self.locator_finder_by_id(toggle_query)
        toggle_query.click()
        time.sleep(1)
    
    def save_query(self, query_name):
        """his method will check saved query featured that introduced on 3.11.x"""
        if self.version_is_newer_than("3.11.99"):
            save_query = "(//button[normalize-space()='Save as'])[1]"
            save_query_sitem = self.locator_finder_by_xpath(save_query)
            save_query_sitem.click()
            time.sleep(1)

            saved_query_btn = "newQueryName"
            saved_query_btn_sitem = self.locator_finder_by_id(saved_query_btn)
            saved_query_btn_sitem.click()
            saved_query_btn_sitem.send_keys(query_name)
            time.sleep(1)

            save_new_query_btn = "(//button[normalize-space()='Save'])[1]"
            self.locator_finder_by_xpath(save_new_query_btn).click()
            time.sleep(1)

        else:
            save_query = self.save_current_query_id
            save_query = self.locator_finder_by_id(save_query)
            save_query.click()
            time.sleep(1)

            saved_query_btn = "(//input[@id='new-query-name'])[1]"
            saved_query_btn_sitem = self.locator_finder_by_xpath(saved_query_btn)
            saved_query_btn_sitem.click()
            saved_query_btn_sitem.send_keys(query_name)
            time.sleep(1)

            save_new_query_btn = "modalButton1"
            self.locator_finder_by_id(save_new_query_btn).click()
            time.sleep(1)

    def search_inside_saved_query(self, query_name):
        """This method will search saved query by given string"""
        self.tprint("Searching through saved query\n")
        search = "querySearchInput"
        saved_query_btn_sitem = self.locator_finder_by_id(search)
        saved_query_btn_sitem.click()
        saved_query_btn_sitem.clear()
        saved_query_btn_sitem.send_keys(query_name)
        time.sleep(1)

        self.tprint("Checking that found the exact query\n")
        find = f"//*[text()='{query_name}']"
        find_sitem = self.locator_finder_by_xpath(find).text
        assert query_name == find_sitem, f"Expected page title {query_name} but got {find_sitem}"
        saved_query_btn_sitem.clear()

    def saved_query_check(self):
        """This method will check saved query"""
        self.tprint("Saved query check started\n")
        self.selecting_query_page()

        self.select_query_execution_area()

        self.tprint("start 1st query for saving \n")
        self.send_key_action("FOR i IN 1..1000")
        self.send_key_action(Keys.ENTER)
        self.send_key_action(Keys.TAB)
        self.send_key_action('INSERT {name: CONCAT("test", i),')
        self.send_key_action(Keys.ENTER)
        self.send_key_action("status: 1 + (i % 5)} IN myCollection")
        self.save_query("insertQuery")

        self.tprint("start 2nd query for saving \n")
        self.select_query_execution_area()
        if self.current_package_version() < semver.VersionInfo.parse("3.11.100"):
            self.clear_query_area()
        # start 2nd query for saving
        self.send_key_action("FOR i IN 1..1000")
        self.send_key_action(Keys.ENTER)
        self.send_key_action(Keys.TAB)
        self.send_key_action('INSERT { name: CONCAT("test", i) } IN myCollection')
        self.save_query("concatQuery")

        self.tprint("start 3rd query for saving \n")
        self.select_query_execution_area()
        if self.current_package_version() < semver.VersionInfo.parse("3.11.100"):
            # clear the execution area
            self.clear_query_area()
        # start 3rd query for saving
        self.send_key_action("FOR doc IN myCollection")
        self.send_key_action(Keys.ENTER)
        self.send_key_action(Keys.TAB)
        self.send_key_action("SORT RAND()")
        self.send_key_action(Keys.ENTER)
        self.send_key_action(Keys.TAB)
        self.send_key_action("LIMIT 10 RETURN doc")
        self.save_query("zSortquery")

        if self.current_package_version() < semver.VersionInfo.parse("3.11.100"):
            # TODO for 3.12.x
            self.toggle_query_btn()
            self.search_inside_saved_query("zSortquery")
            self.search_inside_saved_query("insertQuery")
            self.search_inside_saved_query("concatQuery")

            self.saved_query_settings()

            self.tprint("Deleting all the saved query\n")
            for _ in range(3):
                self.delete_saved_query()

        self.tprint("Return back to query page \n")
        self.selecting_query_page()
