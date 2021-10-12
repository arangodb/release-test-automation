import time
from enum import IntEnum
from selenium_ui_test.pages.base_page import Keys
from selenium_ui_test.pages.navbar import NavigationBarPage

# can't circumvent long lines.. nAttr nLines
# pylint: disable=C0301 disable=C0302 disable=R0902 disable=R0915 disable=R0914


class GraphExample(IntEnum):
    """identify example and manual graphs to be managed herein"""

    KNOWS = 1
    TRAVERSAL = 2
    K_SHORTEST_PATH = 3
    MAPS = 4
    WORLD = 5
    SOCIAL = 6
    CITY = 7
    MANUAL_KNOWS = 8
    # MANUAL_SATELITE_GRAPH = 9
    # MANUAL_SMART_GRAHP = 10
    # MANUAL_DISJOINT_SMART_GRAHP = 11
    # TODO: 3.8 and newer only: CONNECTED = 12


class VCol:
    """maps a vertex collection to a graph"""

    def __init__(self, name):
        self.name = name
        self.ctype = "v"


class ECol:
    """maps an edge collection to a graph"""

    def __init__(self, name):
        self.name = name
        self.ctype = "e"


class GraphCreateSet:
    """this has all we need to know to create an example graph"""

    def __init__(self, clear_name, btn_id, collections, handler=None):
        self.clear_name = clear_name
        self.btn_id = btn_id
        self.handler = handler
        self.collections = collections


GRAPH_SETS = []


def get_graph_name(graph: GraphExample):
    """resolves the enum to a printeable string"""
    return GRAPH_SETS[graph].clear_name


class GraphPage(NavigationBarPage):
    """class for Graph page"""

    def __init__(self, driver):
        """Graph page initialization"""
        super().__init__(driver)
        self.select_graph_page_id = "graphs"
        self.select_create_graph_id = "createGraph"
        self.select_example_graph_btn_id = "tab-exampleGraphs"
        self.select_ex_graph_format = "//*[@id='exampleGraphs']/table/tbody/tr[%d]/td[2]/button"

        self.confirm_delete_graph_id = "modalButton0"
        self.delete_with_collection_id = "dropGraphCollections"
        self.select_really_delete_btn_id = "modal-confirm-delete"

        self.select_collection_page_id = "collections"
        self.select_graph_cancel_btn_id = "modalButton3"

        self.select_search_id = "searchInput"

        self.knows_graph_id = "knows_graph_tile"
        self.select_share_id = "//*[@id='loadFullGraph']/span/i"
        self.select_load_full_graph_id = "modalButton1"
        self.select_camera_download_icon = "//*[@id='downloadPNG']/span/i"
        self.select_full_screen_btn_id = "//*[@id='graph-fullscreen-btn']/span/i"

        self.configure_graph_settings_id = "settingsMenu"
        self.select_graph_layout_option_id = "g_layout"
        self.select_renderer_id = "g_renderer"
        self.select_depth_id = "//*[@id='g_depth']"
        self.select_limit_id = "//*[@id='g_limit']"
        self.add_collection_name_id = "g_nodeLabelByCollection"
        self.select_color_collection_id = "g_nodeColorByCollection"
        self.select_size_by_edges_id = "g_nodeSizeByEdges"
        self.select_add_edge_col_name_id = "g_edgeLabelByCollection"
        self.select_color_node_by_edge_id = "g_edgeColorByCollection"
        self.select_edge_type_id = "g_edgeType"
        self.select_restore_settings_id = "/html//button[@id='restoreGraphSettings']"
        self.select_tooltips_id = "//*[@id='graphSettingsView']/div/div[2]/div[1]/div[5]/i"

        self.select_sort_settings_id = "graphManagementToggle"
        self.select_sort_descend_id = "//*[@id='graphManagementDropdown']/ul/li[2]/a/label/i"
        self.select_resume_layout_btn_id = "//*[@id='toggleForce']/i"

        self.create_new_collection_id = "createCollection"
        self.new_collection_name_id = "new-collection-name"
        self.save_collection_btn_id = "//*[@id='modalButton1']"
        self.select_upload_btn_id = "/html//a[@id='importCollection']"
        self.select_choose_file_btn_id = "/html//input[@id='importDocuments']"
        self.select_confirm_upload_btn_id = "confirmDocImport"

        self.select_new_graph_name_id = "createNewGraphName"

    def create_manual_graph(self, importer, test_data_dir):
        """creating graph manually"""
        collection_page = self.locator_finder_by_id(self.select_collection_page_id)
        collection_page.click()

        # first collection for the knows_graph_manual begins
        col1 = self.create_new_collection_id
        col1_name = self.new_collection_name_id
        col1_save = self.save_collection_btn_id
        col1_select = "//*[@id='collection_manual_edge']/div/h5"
        col1_edge_id = "new-collection-type"
        col1_upload = self.select_upload_btn_id
        col1_file = self.select_choose_file_btn_id
        col1_import = self.select_confirm_upload_btn_id
        path1 = test_data_dir / "ui_data" / "graph_page" / "knows" / "manual_edge.json"

        print("Creating manual_edge collections for knows_graph_manual Graph\n")
        col1 = self.locator_finder_by_id(col1)
        col1.click()

        col1_name = self.locator_finder_by_id(col1_name)
        col1_name.click()
        col1_name.send_keys("manual_edge")

        self.locator_finder_by_select(col1_edge_id, 1)

        col1_save = self.locator_finder_by_xpath(col1_save)
        col1_save.click()

        col1_select = self.locator_finder_by_xpath(col1_select)
        col1_select.click()

        # selecting collection upload btn
        col1_upload = self.locator_finder_by_xpath(col1_upload)
        col1_upload.click()
        time.sleep(3)

        # This method will upload the file with the file path given
        col1_file = self.locator_finder_by_xpath(col1_file)
        time.sleep(2)
        col1_file.send_keys(str(path1.absolute()))

        print("Importing manual_edge.json to the collection\n")
        col1_import = self.locator_finder_by_id(col1_import)
        col1_import.click()
        time.sleep(2)
        print("Importing manual_edge.json to the collection completed\n")

        self.webdriver.back()

        # second collection for the knows_graph_manual begins
        col2 = self.create_new_collection_id
        col2_name = self.new_collection_name_id
        col2_save = self.save_collection_btn_id
        col2_select = "//*[@id='collection_manual_vertices']/div/h5"
        col2_upload = self.select_upload_btn_id
        col2_file = self.select_choose_file_btn_id
        col2_import = self.select_confirm_upload_btn_id
        path2 = test_data_dir / "ui_data" / "graph_page" / "knows" / "manual_vertices.json"

        print("Creating manual_vertices collections for knows_graph_manual Graph\n")
        col2 = self.locator_finder_by_id(col2)
        col2.click()

        col2_name = self.locator_finder_by_id(col2_name)
        col2_name.click()
        col2_name.send_keys("manual_vertices")

        col2_save = self.locator_finder_by_xpath(col2_save)
        col2_save.click()

        col2_select = self.locator_finder_by_xpath(col2_select)
        col2_select.click()

        # selecting collection upload btn
        col2_upload = self.locator_finder_by_xpath(col2_upload)
        col2_upload.click()
        time.sleep(3)

        # This method will upload the file with the file path given
        col2_file = self.locator_finder_by_xpath(col2_file)
        time.sleep(2)
        col2_file.send_keys(str(path2.absolute()))

        print("Importing manual_vertices.json to the collection\n")
        col2_import = self.locator_finder_by_id(col2_import)
        col2_import.click()
        time.sleep(3)
        print("Importing manual_vertices.json to the collection completed\n")
        self.select_graph_page()
        self.create_knows_manual_graph()

    def select_graph_page(self):
        """selecting Graph tab"""
        select_graph_page_sitem = self.locator_finder_by_id(self.select_graph_page_id)
        select_graph_page_sitem.click()

    def create_knows_manual_graph(self):
        """adding knows_graph_manual graph"""
        select_graph_sitem = self.locator_finder_by_id(self.select_create_graph_id)
        select_graph_sitem.click()

        # list of id's for manual graph
        new_graph = self.select_new_graph_name_id
        edge_definition = "row_newEdgeDefinitions0"
        from_collection = "s2id_fromCollections0"
        to_collection = "s2id_toCollections0"
        create_btn_id = "modalButton1"
        knows_graph_id = '//*[@id="knows_graph_manual_tile"]/div/h5'

        new_graph_sitem = self.locator_finder_by_id(new_graph)
        new_graph_sitem.click()
        new_graph_sitem.clear()
        new_graph_sitem.send_keys("knows_graph_manual")

        # selecting edge definition from auto suggestion
        edge_definition_sitem = self.locator_finder_by_id(edge_definition)
        self.choose_item_from_a_dropdown_menu(edge_definition_sitem, "manual_edge")

        # selecting from collection from auto suggestion
        from_collection_sitem = self.locator_finder_by_id(from_collection)
        from_collection_sitem.click()
        super().send_key_action(Keys.ENTER)

        time.sleep(1)

        # selecting to collection from auto suggestion
        to_collection_sitem = self.locator_finder_by_id(to_collection)
        to_collection_sitem.click()
        super().send_key_action(Keys.ENTER)

        time.sleep(1)

        # selecting create graph btn
        create_btn_sitem = self.locator_finder_by_id(create_btn_id)
        create_btn_sitem.click()

        time.sleep(2)

        # selecting newly created graph btn
        knows_graph_sitem = self.locator_finder_by_xpath(knows_graph_id)
        knows_graph_sitem.click()

        time.sleep(3)
        self.webdriver.back()

    def create_satellite_graph(self, importer, test_data_dir):
        """creating satellite graph"""
        if super().current_package_version() >= 3.8:
            self.select_graph_page()
            knows_path = test_data_dir / "ui_data" / "graph_page" / "knows"
            select_graph_sitem = self.locator_finder_by_id(self.select_create_graph_id)
            select_graph_sitem.click()

            # list of id's for satellite graph
            select_satellite = "tab-satelliteGraph"
            new_graph = self.select_new_graph_name_id
            edge_definition = "s2id_newEdgeDefinitions0"
            from_collection = "s2id_fromCollections0"
            to_collection = "s2id_toCollections0"
            create_btn_id = "modalButton1"

            # selecting satellite graph tab
            select_satellite_sitem = self.locator_finder_by_id(select_satellite)
            select_satellite_sitem.click()

            new_graph_sitem = self.locator_finder_by_id(new_graph)
            new_graph_sitem.click()
            new_graph_sitem.clear()
            new_graph_sitem.send_keys("satellite_graph")

            # selecting edge definition from auto suggestion
            edge_definition_sitem = self.locator_finder_by_id(edge_definition)
            edge_definition_sitem.click()
            super().send_key_action("knows_edge")
            super().send_key_action(Keys.ENTER)

            # selecting from collection from auto suggestion
            from_collection_sitem = self.locator_finder_by_id(from_collection)
            from_collection_sitem.click()
            super().send_key_action("persons")
            super().send_key_action(Keys.ENTER)

            time.sleep(1)

            # selecting to collection from auto suggestion
            to_collection_sitem = self.locator_finder_by_id(to_collection)
            to_collection_sitem.click()
            super().send_key_action("persons")
            super().send_key_action(Keys.ENTER)

            time.sleep(1)

            # selecting create graph btn
            create_btn_sitem = self.locator_finder_by_id(create_btn_id)
            create_btn_sitem.click()

            time.sleep(2)

            # importing collections using arangoimport
            print("Importing knows_edge collections \n")
            importer.import_smart_edge_collection("knows_edge", knows_path / "knows_edge.json", ["profiles_smart"])

            print("Importing persons collections \n")
            importer.import_collection("persons", knows_path / "persons.json")

            # Selecting satellite graph settings to view and delete
            satellite_settings_id = '//*[@id="satellite_graph_tile"]/div/h5'
            satellite_settings_sitem = self.locator_finder_by_xpath(satellite_settings_id)
            satellite_settings_sitem.click()

            time.sleep(5)
            self.webdriver.back()
            time.sleep(1)

            print("\n")
            print("Smart Graph deleting started \n")
            satellite_settings_id = "satellite_graph_settings"
            satellite_settings_sitem = self.locator_finder_by_id(satellite_settings_id)
            satellite_settings_sitem.click()

            delete_btn_id = "modalButton0"
            delete_sitem = self.locator_finder_by_id(delete_btn_id)
            delete_sitem.click()

            delete_check_id = "dropGraphCollections"
            delete_check_sitem = self.locator_finder_by_id(delete_check_id)
            delete_check_sitem.click()

            delete_confirm_btn_id = "modal-confirm-delete"
            delete_confirm_btn_sitem = self.locator_finder_by_id(delete_confirm_btn_id)
            delete_confirm_btn_sitem.click()

            time.sleep(2)
            print("Satellite Graph deleted successfully \n")
            self.webdriver.refresh()
        else:
            print("Satellite Graph is not supported for the current package \n")

    def create_smart_graph(self, importer, test_data_dir, disjointgraph=False):
        """Adding smart disjoint graph"""
        page_path = test_data_dir / "ui_data" / "graph_page" / "pregel_community"

        if super().current_package_version() >= 3.6 and disjointgraph is False:
            select_graph_id = self.select_create_graph_id
            select_graph_sitem = self.locator_finder_by_id(select_graph_id)
            select_graph_sitem.click()

            # list of id's for smart graph
            select_smart = "tab-smartGraph"
            new_graph = self.select_new_graph_name_id
            shard = "new-numberOfShards"
            replication = "new-replicationFactor"
            write_concern = "new-writeConcern"
            disjoint = "new-isDisjoint"
            smart_attribute = "new-smartGraphAttribute"

            edge_definition = "s2id_newEdgeDefinitions0"
            from_collection = "s2id_fromCollections0"
            to_collection = "s2id_toCollections0"
            create_btn_id = "modalButton1"

            # selecting smart graph tab
            select_smart_sitem = self.locator_finder_by_id(select_smart)
            select_smart_sitem.click()

            new_graph_sitem = self.locator_finder_by_id(new_graph)
            new_graph_sitem.click()
            new_graph_sitem.clear()
            new_graph_sitem.send_keys("smart_graph")

            # specifying number of shards
            shard_sitem = self.locator_finder_by_id(shard)
            shard_sitem.click()
            shard_sitem.send_keys("3")

            # specifying replication of shards
            replication_sitem = self.locator_finder_by_id(replication)
            replication_sitem.click()
            replication_sitem.send_keys("3")

            # specifying write concern of shards
            write_concern_sitem = self.locator_finder_by_id(write_concern)
            write_concern_sitem.click()
            write_concern_sitem.send_keys("1")

            # specifying write disjoint graphs
            if disjointgraph:
                disjoint_sitem = self.locator_finder_by_id(disjoint)
                disjoint_sitem.click()
            else:
                print("Disjoint Graph not selected. \n")

            # specifying write concern of shards
            smart_attribute_sitem = self.locator_finder_by_id(smart_attribute)
            smart_attribute_sitem.click()
            smart_attribute_sitem.send_keys("community")

            # scrolling down
            super().scroll(1)
            time.sleep(2)

            # selecting edge definition from auto suggestion
            edge_definition_sitem = self.locator_finder_by_id(edge_definition)
            edge_definition_sitem.click()

            super().send_key_action("relations")
            super().send_key_action(Keys.ENTER)

            # selecting from collection from auto suggestion
            from_collection_sitem = self.locator_finder_by_id(from_collection)
            from_collection_sitem.click()
            super().send_key_action("profiles")
            super().send_key_action(Keys.ENTER)

            time.sleep(1)

            # selecting to collection from auto suggestion
            to_collection_sitem = self.locator_finder_by_id(to_collection)
            to_collection_sitem.click()
            super().send_key_action("profiles")
            super().send_key_action(Keys.ENTER)
            time.sleep(1)

            # selecting create graph btn
            create_btn_sitem = self.locator_finder_by_id(create_btn_id)
            create_btn_sitem.click()
            time.sleep(2)

            print("Importing profile collections \n")
            importer.import_collection("profiles", page_path / "profiles.jsonl")

            print("Importing relations collections \n")
            importer.import_smart_edge_collection("relations", page_path / "relations.jsonl", ["profiles_smart"])

            # opening smart graph
            smart_graph_id = "smart_graph_tile"
            smart_graph_sitem = self.locator_finder_by_id(smart_graph_id)
            smart_graph_sitem.click()
            time.sleep(2)

            # loading full graph
            load_graph_id = "loadFullGraph"
            load_graph_sitem = self.locator_finder_by_id(load_graph_id)
            load_graph_sitem.click()
            time.sleep(1)

            load_full_graph_id = "modalButton1"
            load_full_graph_sitem = self.locator_finder_by_id(load_full_graph_id)
            load_full_graph_sitem.click()
            time.sleep(5)

            self.webdriver.back()

            time.sleep(2)

            print("\n")
            print("Smart Graph deleting started \n")
            smart_settings_id = "smart_graph_settings"
            smart_settings_sitem = self.locator_finder_by_id(smart_settings_id)
            smart_settings_sitem.click()

            delete_btn_id = "modalButton0"
            delete_btn_sitem = self.locator_finder_by_id(delete_btn_id)
            delete_btn_sitem.click()

            delete_check_id = "dropGraphCollections"
            delete_check_sitem = self.locator_finder_by_id(delete_check_id)
            delete_check_sitem.click()

            delete_confirm_btn_id = "modal-confirm-delete"
            delete_confirm_btn_sitem = self.locator_finder_by_id(delete_confirm_btn_id)
            delete_confirm_btn_sitem.click()

            time.sleep(2)
            print("Smart Graph deleted successfully \n")

            self.webdriver.refresh()
        else:
            print("Disjoint Graph is not supported for the current package \n")

    def create_disjoint_smart_graph(self, importer, test_data_dir):
        """wrap it with disjoint true"""
        self.create_smart_graph(importer, test_data_dir, disjointgraph=True)

    def create_graph(self, graph: GraphExample, importer, test_data_dir):
        """Creating new example graphs"""
        create_graph = GRAPH_SETS[graph]
        if create_graph.handler is not None:
            create_graph.handler(self, importer, test_data_dir)
            return
        select_graph_sitem = self.locator_finder_by_id(self.select_create_graph_id)
        select_graph_sitem.click()
        time.sleep(1)
        # Selecting example graph button
        select_example_graph_sitem = self.locator_finder_by_id(self.select_example_graph_btn_id)
        select_example_graph_sitem.click()
        time.sleep(1)
        select_graph_button_sitem = self.locator_finder_by_xpath(self.select_ex_graph_format % (int(graph)))
        select_graph_button_sitem.click()
        time.sleep(10)

    def check_required_collections(self, graph):
        """selecting collection tab and search for required collections"""
        collection_page_sitem = self.locator_finder_by_id(self.select_collection_page_id)
        collection_page_sitem.click()

        for collection in GRAPH_SETS[graph].collections:
            search_collection_id = "//*[@id='collection_%s']/div/h5" % collection.name
            collection_sitem = self.locator_finder_by_xpath(search_collection_id)
            search_sitem = self.locator_finder_by_id(self.select_search_id)
            search_sitem.click()
            search_sitem.clear()
            search_sitem.send_keys(collection.name)
            if collection_sitem.text == collection.name:
                print(collection.name + " collectionhas been validated")
            else:
                print(collection.name + " collection wasn't found")
            time.sleep(3)
            self.webdriver.refresh()
        self.webdriver.back()
        self.webdriver.refresh()

    def checking_collection_creation(self, graph: GraphExample):
        """Checking required collections creation for the particular example graph."""
        graph_sitem = self.locator_finder_by_id(GRAPH_SETS[graph].btn_id)
        graph_sitem.click()

        time.sleep(3)
        select_graph_cancel_btn_sitem = self.locator_finder_by_id(self.select_graph_cancel_btn_id)
        select_graph_cancel_btn_sitem.click()
        time.sleep(3)

    def select_sort_descend(self):
        """Sorting all graphs to descending and then ascending again"""
        select_sort_settings_sitem = self.locator_finder_by_id(self.select_sort_settings_id)
        select_sort_settings_sitem.click()
        time.sleep(2)

        descend = self.select_sort_descend_id
        ascend = self.select_sort_descend_id

        print("Sorting Graphs to Descending\n")
        descend_sitem = self.locator_finder_by_xpath(descend)
        descend_sitem.click()
        time.sleep(2)

        print("Sorting Graphs to Ascending\n")
        ascend_sitem = self.locator_finder_by_xpath(ascend)
        ascend_sitem.click()
        time.sleep(2)

    def inspect_knows_graph(self):
        """Selecting Knows Graph for checking graph functionality"""
        print("Selecting Knows Graph\n")
        graph_sitem = self.locator_finder_by_id(self.knows_graph_id)
        graph_sitem.click()
        time.sleep(4)

        print("Selecting Knows Graph share option\n")
        share_sitem = self.locator_finder_by_xpath(self.select_share_id)
        share_sitem.click()
        time.sleep(2)

        print("Selecting load full graph button\n")
        full_graph_sitem = self.locator_finder_by_id(self.select_load_full_graph_id)
        full_graph_sitem.click()
        time.sleep(4)

        if self.webdriver.name == "chrome":  # this will check browser name
            print("Download has been disabled for the Chrome browser \n")
        else:
            print("Selecting Graph download button\n")
            camera = self.select_camera_download_icon
            camera_sitem = self.locator_finder_by_xpath(camera)
            camera_sitem.click()
            time.sleep(3)
            # super().clear_download_bar()

        # TODO: fullscreen may only work interactive with pynput
        # print("Selecting full screen mode\n")
        # full_screen_sitem = self.locator_finder_by_xpath(self.select_full_screen_btn_id)
        # full_screen_sitem.click()
        # time.sleep(3)
        # print("Return to normal mode\n")
        # super().escape()
        # time.sleep(3)

        # print("Selecting Resume layout button \n")
        # resume = self.select_resume_layout_btn_id
        # pause = self.select_resume_layout_btn_id
        #
        # resume_sitem = self.locator_finder_by_xpath(resume)
        # resume_sitem.click()
        # time.sleep(3)
        # pause_sitem = self.locator_finder_by_xpath(pause)
        # pause_sitem.click()
        # time.sleep(3)

    def graph_setting(self):
        """Checking all the options inside graph settings"""
        self.webdriver.refresh()
        configure_graph_settings_sitem = self.locator_finder_by_id(self.configure_graph_settings_id)
        configure_graph_settings_sitem.click()
        time.sleep(2)
        print("Selecting different layouts for the graph\n")
        print("Selecting Fruchtermann layout\n")
        layout2 = self.select_graph_layout_option_id
        self.locator_finder_by_select(layout2, 2)
        time.sleep(3)

        print("Selecting Force layout\n")
        layout1 = self.select_graph_layout_option_id
        self.locator_finder_by_select(layout1, 1)
        time.sleep(3)

        print("Selecting WebGL experimental renderer\n")
        renderer = self.select_renderer_id
        self.locator_finder_by_select(renderer, 1)
        time.sleep(3)

        print("Changing Search Depth\n")
        depth1 = self.select_depth_id
        depth2 = self.select_depth_id
        depth1 = self.locator_finder_by_xpath(depth1)
        depth1.clear()
        time.sleep(3)
        depth2 = self.locator_finder_by_xpath(depth2)
        depth2.send_keys("4")

        print("Changing Search Limit\n")
        limit = self.select_limit_id
        limit1 = self.select_limit_id
        limit2 = self.select_limit_id

        self.locator_finder_by_xpath(limit).click()
        time.sleep(2)
        limit1 = self.locator_finder_by_xpath(limit1)
        limit1.clear()
        limit2 = self.locator_finder_by_xpath(limit2)
        limit2.send_keys("300")
        time.sleep(3)

        print("Adding collection name with nodes to YES\n")
        self.locator_finder_by_select(self.add_collection_name_id, 0)
        time.sleep(3)

        print("Selecting color by collection to NO\n")
        self.locator_finder_by_select(self.select_color_collection_id, 0)
        time.sleep(3)

        print("Selecting size by edges to NO\n")
        self.locator_finder_by_select(self.select_size_by_edges_id, 1)
        time.sleep(3)

        print("Adding edge name to the node to YES\n")
        self.locator_finder_by_select(self.select_add_edge_col_name_id, 0)
        time.sleep(3)

        print("Adding Color by edge collection ot YES\n")
        self.locator_finder_by_select(self.select_color_node_by_edge_id, 1)
        time.sleep(3)

        print("Selecting different representation of relation between nodes\n")
        print("Maximizing the window")
        self.webdriver.maximize_window()
        time.sleep(2)

        tip1 = self.select_depth_id
        tip2 = self.select_depth_id
        tip4 = self.select_depth_id
        tip5 = self.select_depth_id
        tip6 = self.select_depth_id

        restore1 = self.select_restore_settings_id
        restore2 = self.select_restore_settings_id
        restore4 = self.select_restore_settings_id
        restore5 = self.select_restore_settings_id
        restore6 = self.select_restore_settings_id

        type1 = self.select_edge_type_id
        type3 = self.select_edge_type_id
        type4 = self.select_edge_type_id
        type5 = self.select_edge_type_id
        type6 = self.select_edge_type_id

        self.webdriver.find_element_by_xpath(tip1).click()
        super().scroll(1)
        time.sleep(2)
        restore1 = self.locator_finder_by_xpath(restore1)
        restore1.click()
        time.sleep(1)

        print("Changing relation representation type to Line")
        self.locator_finder_by_select(type1, 0)
        time.sleep(5)

        self.webdriver.find_element_by_xpath(tip2).click()
        super().scroll(1)
        time.sleep(2)
        restore2 = self.locator_finder_by_xpath(restore2)
        restore2.click()
        time.sleep(1)

        print("Changing relation representation type to Curve")
        self.locator_finder_by_select(type3, 2)
        time.sleep(5)

        self.webdriver.find_element_by_xpath(tip4).click()
        super().scroll(1)
        time.sleep(2)
        restore4 = self.locator_finder_by_xpath(restore4)
        restore4.click()
        time.sleep(1)

        print("Changing relation representation type to Dotted")
        self.locator_finder_by_select(type4, 3)
        time.sleep(5)

        self.webdriver.find_element_by_xpath(tip5).click()
        super().scroll(1)
        time.sleep(2)
        restore5 = self.locator_finder_by_xpath(restore5)
        restore5.click()
        time.sleep(1)

        print("Changing relation representation type to Dashed")
        self.locator_finder_by_select(type5, 4)
        time.sleep(5)

        self.webdriver.find_element_by_xpath(tip6).click()
        super().scroll(1)
        time.sleep(2)
        restore6 = self.locator_finder_by_xpath(restore6)
        restore6.click()
        time.sleep(1)

        print("Changing relation representation type to Tapered\n")
        self.locator_finder_by_select(type6, 5)
        time.sleep(5)

        print("Going Back to original window size \n")
        self.webdriver.set_window_size(1250, 1000)  # custom window size
        self.webdriver.back()
        self.wait_for_ajax()

    def delete_graph(self, graph: GraphExample):
        """Deleting created graphs"""
        print("Deleting %s Graph" % GRAPH_SETS[graph].clear_name)
        self.wait_for_ajax()
        btn_id = GRAPH_SETS[graph].btn_id
        select_graph_setting_btn_sitem = self.locator_finder_by_id(btn_id)
        select_graph_setting_btn_sitem.click()
        self.wait_for_ajax()

        time.sleep(0.1)
        confirm_delete_graph_sitem = self.locator_finder_by_text_id(self.confirm_delete_graph_id)
        confirm_delete_graph_sitem.click()
        self.wait_for_ajax()

        time.sleep(0.1)
        delete_with_collection_sitem = self.locator_finder_by_text_id(self.delete_with_collection_id)
        delete_with_collection_sitem.click()
        self.wait_for_ajax()

        time.sleep(0.1)
        select_really_delete_btn_sitem = self.locator_finder_by_id(self.select_really_delete_btn_id)
        select_really_delete_btn_sitem.click()
        self.wait_for_ajax()


GRAPH_SETS = [
    GraphCreateSet(None, None, [], None),
    GraphCreateSet("Knows", "knows_graph_settings", [VCol("persons"), ECol("knows")]),
    GraphCreateSet("Traversal", "traversalGraph_settings", [VCol("circles"), ECol("edges")]),
    GraphCreateSet("kShortestPaths", "kShortestPathsGraph_settings", [VCol("places"), ECol("connections")]),
    GraphCreateSet("Mps", "mps_graph_settings", [VCol("mps_verts"), ECol("mps_edges")]),
    GraphCreateSet("World", "worldCountry_settings", [VCol("worldVertices"), ECol("worldEdges")]),
    GraphCreateSet("Social", "social_settings", [VCol("male"), VCol("female"), ECol("relation")]),
    GraphCreateSet(
        "City",
        "routeplanner_settings",
        [
            VCol("frenchCity"),
            VCol("germanCity"),
            ECol("frenchHighway"),
            ECol("germanHighway"),
            ECol("internationalHighway"),
        ],
    ),
    GraphCreateSet(
        "Manual Knows",
        "knows_graph_manual_settings",
        [VCol("persons"), ECol("manual_edge")],
        GraphPage.create_manual_graph,
    ),
    GraphCreateSet("Satelite Graph", "satellite_graph_settings", [], GraphPage.create_satellite_graph),
    GraphCreateSet("Smartgraph", "satellite_graph_settings", [], GraphPage.create_smart_graph),
    GraphCreateSet("disjoint Smartgraph", "satellite_graph_settings", [], GraphPage.create_disjoint_smart_graph),
    GraphCreateSet("Connected Components", "connectedComponentsGraph_settings", [], None),  # TODO?
]
