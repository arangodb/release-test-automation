import time

import pyautogui

from baseSelenium import BaseSelenium


class QueryPage(BaseSelenium):

    def __init__(self, driver):
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

    # importing collections for query
    def import_collections(self):
        print("Navigating to Collection page \n")
        # Selecting collections page
        collections = "collections"
        collections = \
            BaseSelenium.locator_finder_by_id(self, collections)
        collections.click()
        time.sleep(1)

        cmd1 = 'cmd /c "arangorestore --server.endpoint tcp://127.0.0.1:8529 --input-directory ' \
               'C:\\Users\\rearf\\Desktop\\collections\\IMDB_DUMP --server.username root --server.password "" ' \
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

        modalButton1 = 'modalButton1'
        modalButton1 = \
            BaseSelenium.locator_finder_by_id(self, modalButton1)
        modalButton1.click()

        self.driver.refresh()
        time.sleep(5)
        self.driver.back()
        time.sleep(1)

    # Selecting query page
    def selecting_query_page(self):
        query_page = self.selecting_query_page_id
        query_page = \
            BaseSelenium.locator_finder_by_id(self, query_page)
        query_page.click()
        time.sleep(1)

    def execute_query(self, query_name):
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

    # profiling query
    def profile_query(self):
        profile = self.profile_query_id
        profile = \
            BaseSelenium.locator_finder_by_id(self, profile)
        profile.click()
        time.sleep(2)

        super().scroll()

    # Downloading debug package
    def explain_query(self):
        explainQuery = self.explain_query_id
        explainQuery = \
            BaseSelenium.locator_finder_by_id(self, explainQuery)
        explainQuery.click()
        time.sleep(2)

    # Downloading debug package
    def debug_package_download(self):
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

    # Removing all query results
    def remove_query_result(self):
        remove_results = self.remove_all_results_id
        remove_results = \
            BaseSelenium.locator_finder_by_id(self, remove_results)
        remove_results.click()
        time.sleep(2)

    # Clearing current query area
    def clear_query_area(self):
        clear_query = self.query_execution_area
        clear_query = \
            BaseSelenium.locator_finder_by_xpath(self, clear_query)
        clear_query.click()

        pyautogui.keyDown('ctrl')
        pyautogui.press('a')
        pyautogui.keyUp('ctrl')
        pyautogui.press('del')
        time.sleep(2)

    # Selecting spot light function helper
    def spot_light_function(self, search):
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

    # Updating documents
    def update_documents(self):
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

        # clear the execution area
        self.clear_query_area()

    # executing query with bind parameters
    def bind_parameters_query(self):
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

    # importing new queries
    def import_queries(self, path):
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

        Del_btn = 'modalButton1'
        Del_btn = \
            BaseSelenium.locator_finder_by_id(self, Del_btn)
        Del_btn.click()
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

    # saving custom query and check slow query
    def custom_query(self):
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
        Del_btn = 'modalButton1'
        Del_btn = \
            BaseSelenium.locator_finder_by_id(self, Del_btn)
        Del_btn.click()
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

    # changing the number of output
    def number_of_results(self):
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
