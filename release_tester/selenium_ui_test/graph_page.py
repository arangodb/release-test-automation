#!/usr/bin/env python
"""
aardvark graphs page object
"""

import time

from selenium_ui_test.base_selenium import BaseSelenium

# can't circumvent long lines.. nAttr nLines
# pylint: disable=C0301 disable=C0302 disable=R0902 disable=R0915 disable=R0914

class GraphPage(BaseSelenium):
    """class for Graph page"""

    def __init__(self, driver):
        """Graph page initialization"""
        super().__init__()
        self.driver = driver
        self.select_graph_page_id = "graphs"
        self.select_create_graph_id = "createGraph"
        self.select_example_graph_btn_id = "tab-exampleGraphs"
        self.select_knows_graph_id = "//*[@id='exampleGraphs']/table/tbody/tr[1]/td[2]/button"
        self.select_traversal_graph_id = "//*[@id='exampleGraphs']/table/tbody/tr[2]/td[2]/button"
        self.select_k_shortest_path_id = "//*[@id='exampleGraphs']/table/tbody/tr[3]/td[2]/button"
        self.select_maps_graph_id = "//*[@id='exampleGraphs']/table/tbody/tr[4]/td[2]/button"
        self.select_world_graph_id = "//*[@id='exampleGraphs']/table/tbody/tr[5]/td[2]/button"
        self.select_social_graph_id = "//*[@id='exampleGraphs']/table/tbody/tr[6]/td[2]/button"
        self.select_city_graph_id = "//*[@id='exampleGraphs']/table/tbody/tr[7]/td[2]/button"
        self.select_connected_component_graph_id = "//*[@id='exampleGraphs']/table/tbody/tr[8]/td[2]/button"

        self.select_knows_graphs_setting_btn_id = "knows_graph_settings"
        self.select_knows_graphs_setting_btn_id_check = "knows_graph_settings"

        self.select_traversal_graphs_setting_btn_id = "traversalGraph_settings"
        self.select_traversal_graphs_setting_btn_id_check = "traversalGraph_settings"

        self.select_k_shortest_path_graphs_setting_btn_id = "kShortestPathsGraph_settings"
        self.select_k_shortest_path_graphs_setting_btn_id_check = "kShortestPathsGraph_settings"

        self.select_maps_graphs_setting_btn_id = "mps_graph_settings"
        self.select_maps_graphs_setting_btn_id_check = "mps_graph_settings"

        self.select_world_graphs_setting_btn_id = "worldCountry_settings"
        self.select_world_graphs_setting_btn_id_check = "worldCountry_settings"

        self.select_social_graphs_setting_btn_id = "social_settings"
        self.select_social_graphs_setting_btn_id_check = "social_settings"

        self.select_route_planner_graphs_setting_btn_id = "routeplanner_settings"
        self.select_route_planner_graphs_setting_btn_id_check = "routeplanner_settings"

        self.select_connected_graphs_setting_btn_id = "connectedComponentsGraph_settings"

        self.select_knows_graph_manual_id = "knows_graph_manual_settings"

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

    def create_manual_graph(self):
        """creating graph manually"""
        collection_page = self.select_collection_page_id
        collection_page = \
            BaseSelenium.locator_finder_by_id(self, collection_page)
        collection_page.click()

        # first collection for the knows_graph_manual begins
        col1 = self.create_new_collection_id
        col1_name = self.new_collection_name_id
        col1_save = self.save_collection_btn_id
        col1_select = "//*[@id='collection_knows_edge']/div/h5"
        col1_edge_id = "new-collection-type"
        col1_upload = self.select_upload_btn_id
        col1_file = self.select_choose_file_btn_id
        col1_import = self.select_confirm_upload_btn_id
        path1 = 'release-test-automation\\test_data\\ui_data\\graph_page\\knows_edge.json'

        print("Creating knows_edge collections for knows_graph_manual Graph\n")
        col1 = \
            BaseSelenium.locator_finder_by_id(self, col1)
        col1.click()

        col1_name = \
            BaseSelenium.locator_finder_by_id(self, col1_name)
        col1_name.click()
        col1_name.send_keys("knows_edge")

        BaseSelenium.locator_finder_by_select(self, col1_edge_id, 1)

        col1_save = \
            BaseSelenium.locator_finder_by_xpath(self, col1_save)
        col1_save.click()

        col1_select = \
            BaseSelenium.locator_finder_by_xpath(self, col1_select)
        col1_select.click()

        # selecting collection upload btn
        col1_upload = \
            BaseSelenium.locator_finder_by_xpath(self, col1_upload)
        col1_upload.click()
        time.sleep(3)

        # This method will upload the file with the file path given
        col1_file = \
            BaseSelenium.locator_finder_by_xpath(self, col1_file)
        time.sleep(2)
        col1_file.send_keys(path1)

        print("Importing knows_edge.json to the collection\n")
        col1_import = \
            BaseSelenium.locator_finder_by_id(self, col1_import)
        col1_import.click()
        time.sleep(2)
        print("Importing knows_edge.json to the collection completed\n")

        self.driver.back()

        # second collection for the knows_graph_manual begins
        col2 = self.create_new_collection_id
        col2_name = self.new_collection_name_id
        col2_save = self.save_collection_btn_id
        col2_select = "//*[@id='collection_persons']/div/h5"
        col2_upload = self.select_upload_btn_id
        col2_file = self.select_choose_file_btn_id
        col2_import = self.select_confirm_upload_btn_id
        path2 = 'release-test-automation\\test_data\\ui_data\\graph_page\\persons.json'

        print("Creating person_vertices collections for knows_graph_manual Graph\n")
        col2 = \
            BaseSelenium.locator_finder_by_id(self, col2)
        col2.click()

        col2_name = \
            BaseSelenium.locator_finder_by_id(self, col2_name)
        col2_name.click()
        col2_name.send_keys("persons")

        col2_save = \
            BaseSelenium.locator_finder_by_xpath(self, col2_save)
        col2_save.click()

        col2_select = \
            BaseSelenium.locator_finder_by_xpath(self, col2_select)
        col2_select.click()

        # selecting collection upload btn
        col2_upload = \
            BaseSelenium.locator_finder_by_xpath(self, col2_upload)
        col2_upload.click()
        time.sleep(3)

        # This method will upload the file with the file path given
        col2_file = \
            BaseSelenium.locator_finder_by_xpath(self, col2_file)
        time.sleep(2)
        col2_file.send_keys(path2)

        print("Importing person_vertices.json to the collection\n")
        col2_import = \
            BaseSelenium.locator_finder_by_id(self, col2_import)
        col2_import.click()
        time.sleep(3)
        print("Importing person_vertices.json to the collection completed\n")

    def select_graph_page(self):
        """selecting Graph tab"""
        self.select_graph_page_id = \
            BaseSelenium.locator_finder_by_id(self, self.select_graph_page_id)
        self.select_graph_page_id.click()

    def adding_knows_manual_graph(self):
        """adding knows_graph_manual graph"""
        select_graph_id = self.select_create_graph_id
        select_graph_id = \
            BaseSelenium.locator_finder_by_id(self, select_graph_id)
        select_graph_id.click()

        # list of id's for manual graph
        new_graph = self.select_new_graph_name_id
        edge_definition = "row_newEdgeDefinitions0"
        from_collection = "s2id_fromCollections0"
        to_collection = "s2id_toCollections0"
        create_btn_id = "modalButton1"
        knows_graph_id = '//*[@id="knows_graph_manual_tile"]/div/h5'

        new_graph = \
            BaseSelenium.locator_finder_by_id(self, new_graph)
        new_graph.click()
        new_graph.clear()
        new_graph.send_keys("knows_graph_manual")

        # selecting edge definition from auto suggestion
        edge_definition = \
            BaseSelenium.locator_finder_by_id(self, edge_definition)
        edge_definition.click()
        super().send_key_action(Keys.ENTER)

        # selecting from collection from auto suggestion
        from_collection = \
            BaseSelenium.locator_finder_by_id(self, from_collection)
        from_collection.click()
        super().send_key_action(Keys.ENTER)

        time.sleep(1)

        # selecting to collection from auto suggestion
        to_collection = \
            BaseSelenium.locator_finder_by_id(self, to_collection)
        to_collection.click()
        super().send_key_action(Keys.ENTER)

        time.sleep(1)

        # selecting create graph btn
        create_btn_id = \
            BaseSelenium.locator_finder_by_id(self, create_btn_id)
        create_btn_id.click()

        time.sleep(2)

        # selecting newly created graph btn
        knows_graph_id = \
            BaseSelenium.locator_finder_by_xpath(self, knows_graph_id)
        knows_graph_id.click()

        time.sleep(3)
        self.driver.back()

    def adding_satellite_graph(self, importer, testdata_path):
        """creating satellite graph"""
        knows_path = testdata_path / 'ui_data' / 'graph_page' / 'knows'
        select_graph_id = self.select_create_graph_id
        select_graph_id = \
            BaseSelenium.locator_finder_by_id(self, select_graph_id)
        select_graph_id.click()

        # list of id's for satellite graph
        select_satellite = 'tab-satelliteGraph'
        new_graph = self.select_new_graph_name_id
        edge_definition = "s2id_newEdgeDefinitions0"
        from_collection = "s2id_fromCollections0"
        to_collection = "s2id_toCollections0"
        create_btn_id = "modalButton1"

        # selecting satellite graph tab
        select_satellite = \
            BaseSelenium.locator_finder_by_id(self, select_satellite)
        select_satellite.click()

        new_graph = \
            BaseSelenium.locator_finder_by_id(self, new_graph)
        new_graph.click()
        new_graph.clear()
        new_graph.send_keys("satellite_graph")

        # selecting edge definition from auto suggestion
        edge_definition = \
            BaseSelenium.locator_finder_by_id(self, edge_definition)
        edge_definition.click()
        super().send_key_action('knows_edge')
        super().send_key_action(Keys.ENTER)

        # selecting from collection from auto suggestion
        from_collection = \
            BaseSelenium.locator_finder_by_id(self, from_collection)
        from_collection.click()
        super().send_key_action('persons')
        super().send_key_action(Keys.ENTER)

        time.sleep(1)

        # selecting to collection from auto suggestion
        to_collection = \
            BaseSelenium.locator_finder_by_id(self, to_collection)
        to_collection.click()
        super().send_key_action('persons')
        super().send_key_action(Keys.ENTER)

        time.sleep(1)

        # selecting create graph btn
        create_btn_id = \
            BaseSelenium.locator_finder_by_id(self, create_btn_id)
        create_btn_id.click()

        time.sleep(2)

        # importing collections using arangoimport
        print("Importing knows_edge collections \n")
        importer.import_smart_edge_collection("knows_edge", knows_path / 'knows_edge.json', ['profiles_smart'])

        print("Importing persons collections \n")
        importer.import_collection('persons', knows_path / 'persons.json')

        # Selecting satellite graph settings to view and delete
        satellite_settings_id = '//*[@id="satellite_graph_tile"]/div/h5'
        satellite_settings_id = \
            BaseSelenium.locator_finder_by_xpath(self, satellite_settings_id)
        satellite_settings_id.click()

        time.sleep(5)
        self.driver.back()
        time.sleep(1)

        print("\n")
        print("Smart Graph deleting started \n")
        satellite_settings_id = 'satellite_graph_settings'
        satellite_settings_id = BaseSelenium.locator_finder_by_id(self, satellite_settings_id)
        satellite_settings_id.click()

        delete_btn = 'modalButton0'
        delete_btn = BaseSelenium.locator_finder_by_id(self, delete_btn)
        delete_btn.click()

        delete_check_id = 'dropGraphCollections'
        delete_check_id = BaseSelenium.locator_finder_by_id(self, delete_check_id)
        delete_check_id.click()

        delete_confirm_btn = 'modal-confirm-delete'
        delete_confirm_btn = BaseSelenium.locator_finder_by_id(self, delete_confirm_btn)
        delete_confirm_btn.click()

        time.sleep(2)
        print("Satellite Graph deleted successfully \n")
        self.driver.refresh()

    def adding_smart_graph(self, importer, testdata_path, disjointgraph=False):
        """Adding smart disjoint graph"""
        page_path = testdata_path / 'ui_data' / 'graph_page' / 'pregel_community'
        select_graph_id = self.select_create_graph_id
        select_graph_id = \
            BaseSelenium.locator_finder_by_id(self, select_graph_id)
        select_graph_id.click()

        # list of id's for smart graph
        select_smart = 'tab-smartGraph'
        new_graph = self.select_new_graph_name_id
        shard = 'new-numberOfShards'
        replication = 'new-replicationFactor'
        write_concern = 'new-writeConcern'
        disjoint = 'new-isDisjoint'
        smart_attribute = "new-smartGraphAttribute"

        edge_definition = "s2id_newEdgeDefinitions0"
        from_collection = "s2id_fromCollections0"
        to_collection = "s2id_toCollections0"
        create_btn_id = "modalButton1"

        # selecting smart graph tab
        select_smart = \
            BaseSelenium.locator_finder_by_id(self, select_smart)
        select_smart.click()

        new_graph = \
            BaseSelenium.locator_finder_by_id(self, new_graph)
        new_graph.click()
        new_graph.clear()
        new_graph.send_keys("smart_graph")

        # specifying number of shards
        shard = \
            BaseSelenium.locator_finder_by_id(self, shard)
        shard.click()
        shard.send_keys('3')

        # specifying replication of shards
        replication = \
            BaseSelenium.locator_finder_by_id(self, replication)
        replication.click()
        replication.send_keys('3')

        # specifying write concern of shards
        write_concern = \
            BaseSelenium.locator_finder_by_id(self, write_concern)
        write_concern.click()
        write_concern.send_keys('1')

        # specifying write disjoint graphs
        if disjointgraph:
            disjoint = \
                BaseSelenium.locator_finder_by_id(self, disjoint)
            disjoint.click()
        else:
            print('Disjoint Graph not selected. \n')

        # specifying write concern of shards
        smart_attribute = \
            BaseSelenium.locator_finder_by_id(self, smart_attribute)
        smart_attribute.click()
        smart_attribute.send_keys('community')

        # scrolling down
        super().scroll(1)
        time.sleep(2)

        # selecting edge definition from auto suggestion
        edge_definition = \
            BaseSelenium.locator_finder_by_id(self, edge_definition)
        edge_definition.click()

        super().send_key_action('relations')
        super().send_key_action(Keys.ENTER)

        # selecting from collection from auto suggestion
        from_collection = \
            BaseSelenium.locator_finder_by_id(self, from_collection)
        from_collection.click()
        super().send_key_action('profiles')
        super().send_key_action(Keys.ENTER)

        time.sleep(1)

        # selecting to collection from auto suggestion
        to_collection = \
            BaseSelenium.locator_finder_by_id(self, to_collection)
        to_collection.click()
        super().send_key_action('profiles')
        super().send_key_action(Keys.ENTER)
        time.sleep(1)

        # selecting create graph btn
        create_btn_id = \
            BaseSelenium.locator_finder_by_id(self, create_btn_id)
        create_btn_id.click()
        time.sleep(2)

        print("Importing profile collections \n")
        importer.import_collection('profiles', page_path / 'profiles.jsonl')

        print("Importing relations collections \n")
        importer.import_smart_edge_collection('relations', page_path / 'relations.jsonl', ['profiles_smart'])

        # opening smart graph
        smart_graph = 'smart_graph_tile'
        smart_graph = BaseSelenium.locator_finder_by_id(self, smart_graph)
        smart_graph.click()
        time.sleep(2)

        # loading full graph
        load_graph = 'loadFullGraph'
        load_graph = BaseSelenium.locator_finder_by_id(self, load_graph)
        load_graph.click()
        time.sleep(1)

        load_full_graph = 'modalButton1'
        load_full_graph = BaseSelenium.locator_finder_by_id(self, load_full_graph)
        load_full_graph.click()
        time.sleep(5)

        self.driver.back()

        time.sleep(2)

        print("\n")
        print("Smart Graph deleting started \n")
        smart_settings = 'smart_graph_settings'
        smart_settings = BaseSelenium.locator_finder_by_id(self, smart_settings)
        smart_settings.click()

        delete_btn = 'modalButton0'
        delete_btn = BaseSelenium.locator_finder_by_id(self, delete_btn)
        delete_btn.click()

        delete_check_id = 'dropGraphCollections'
        delete_check_id = BaseSelenium.locator_finder_by_id(self, delete_check_id)
        delete_check_id.click()

        delete_confirm_btn = 'modal-confirm-delete'
        delete_confirm_btn = BaseSelenium.locator_finder_by_id(self, delete_confirm_btn)
        delete_confirm_btn.click()

        time.sleep(2)
        print("Smart Graph deleted successfully \n")

        self.driver.refresh()

    def select_create_graph(self, graph):
        """Creating new example graphs"""
        select_graph = self.select_create_graph_id
        select_graph = \
            BaseSelenium.locator_finder_by_id(self, select_graph)
        select_graph.click()
        time.sleep(1)
        # Selecting example graph button
        self.select_example_graph_btn_id = \
            BaseSelenium.locator_finder_by_id(self, self.select_example_graph_btn_id)
        self.select_example_graph_btn_id.click()
        time.sleep(1)

        if graph == 1:
            self.select_knows_graph_id = \
                BaseSelenium.locator_finder_by_xpath(self, self.select_knows_graph_id)
            self.select_knows_graph_id.click()
        elif graph == 2:
            self.select_traversal_graph_id = \
                BaseSelenium.locator_finder_by_xpath(self, self.select_traversal_graph_id)
            self.select_traversal_graph_id.click()
        elif graph == 3:
            self.select_k_shortest_path_id = \
                BaseSelenium.locator_finder_by_xpath(self, self.select_k_shortest_path_id)
            self.select_k_shortest_path_id.click()
        elif graph == 4:
            self.select_maps_graph_id = \
                BaseSelenium.locator_finder_by_xpath(self, self.select_maps_graph_id)
            self.select_maps_graph_id.click()
        elif graph == 5:
            self.select_world_graph_id = \
                BaseSelenium.locator_finder_by_xpath(self, self.select_world_graph_id)
            self.select_world_graph_id.click()
        elif graph == 6:
            self.select_social_graph_id = \
                BaseSelenium.locator_finder_by_xpath(self, self.select_social_graph_id)
            self.select_social_graph_id.click()
        elif graph == 7:
            self.select_city_graph_id = \
                BaseSelenium.locator_finder_by_xpath(self, self.select_city_graph_id)
            self.select_city_graph_id.click()
        elif graph == 8:
            self.select_connected_component_graph_id = \
                BaseSelenium.locator_finder_by_xpath(self, self.select_connected_component_graph_id)
            self.select_connected_component_graph_id.click()
        else:
            print("Invalid Graph\n")
        time.sleep(2)

    def check_required_collection(self, graph):
        """selecting collection tab and search for required collections"""
        collection_page = self.select_collection_page_id
        collection_page = \
            BaseSelenium.locator_finder_by_id(self, collection_page)
        collection_page.click()

        if graph == 1:
            search1 = self.select_search_id
            search2 = self.select_search_id
            person = "//*[@id='collection_persons']/div/h5"
            knows = "//*[@id='collection_knows']/div/h5"

            knows = BaseSelenium.locator_finder_by_xpath(self, knows)
            search1 = BaseSelenium.locator_finder_by_id(self, search1)
            search1.click()
            search1.clear()
            search1.send_keys("knows")
            if knows.text == 'knows':
                print("knows collection creation has been validated.\n")
            else:
                print("knows collection not found\n")
            time.sleep(3)
            self.driver.refresh()

            person = BaseSelenium.locator_finder_by_xpath(self, person)
            search2 = BaseSelenium.locator_finder_by_id(self, search2)
            search2.click()
            search2.clear()
            search2.send_keys("persons")
            if person.text == 'persons':
                print("persons collection creation has been validated.\n")
            else:
                print("person collection not found\n")
            time.sleep(3)

        elif graph == 2:
            search1 = self.select_search_id
            search2 = self.select_search_id
            circle = "//*[@id='collection_circles']/div/h5"
            edges = "//*[@id='collection_edges']/div/h5"

            circle = BaseSelenium.locator_finder_by_xpath(self, circle)
            search1 = BaseSelenium.locator_finder_by_id(self, search1)
            search1.click()
            search1.clear()
            search1.send_keys("circles")
            if circle.text == 'circles':
                print("circle collection creation has been validated.\n")
            else:
                print("circle collection not found\n")
            time.sleep(3)
            self.driver.refresh()

            edges = BaseSelenium.locator_finder_by_xpath(self, edges)
            search2 = BaseSelenium.locator_finder_by_id(self, search2)
            search2.click()
            search2.clear()
            search2.send_keys("edges")
            if edges.text == 'edges':
                print("edges collection creation has been validated.\n")
            else:
                print("edges collection not found\n")
            time.sleep(3)

        elif graph == 3:
            search1 = self.select_search_id
            search2 = self.select_search_id
            connections = "//*[@id='collection_connections']/div/h5"
            places = "//*[@id='collection_places']/div/h5"

            connections = BaseSelenium.locator_finder_by_xpath(self, connections)
            search1 = BaseSelenium.locator_finder_by_id(self, search1)
            search1.click()
            search1.clear()
            search1.send_keys("connections")
            if connections.text == 'connections':
                print("connections collection creation has been validated.\n")
            else:
                print("connections collection not found\n")
            time.sleep(3)
            self.driver.refresh()

            places = BaseSelenium.locator_finder_by_xpath(self, places)
            search2 = BaseSelenium.locator_finder_by_id(self, search2)
            search2.click()
            search2.clear()
            search2.send_keys("places")
            if places.text == 'places':
                print("places collection creation has been validated.\n")
            else:
                print("places collection not found\n")
            time.sleep(3)

        elif graph == 4:
            search1 = self.select_search_id
            search2 = self.select_search_id
            mps_edges = "//*[@id='collection_mps_edges']/div/h5"
            mps_verts = "//*[@id='collection_mps_verts']/div/h5"

            mps_edges = BaseSelenium.locator_finder_by_xpath(self, mps_edges)
            search1 = BaseSelenium.locator_finder_by_id(self, search1)
            search1.click()
            search1.clear()
            search1.send_keys("mps_edges")
            if mps_edges.text == 'mps_edges':
                print("mps_edges collection creation has been validated.\n")
            else:
                print("mps_edges collection not found\n")
            time.sleep(3)
            self.driver.refresh()

            mps_verts = BaseSelenium.locator_finder_by_xpath(self, mps_verts)
            search2 = BaseSelenium.locator_finder_by_id(self, search2)
            search2.click()
            search2.clear()
            search2.send_keys("mps_verts")
            if mps_verts.text == 'mps_verts':
                print("mps_verts collection creation has been validated.\n")
            else:
                print("mps_verts collection not found\n")
            time.sleep(3)

        elif graph == 5:
            search1 = self.select_search_id
            search2 = self.select_search_id
            world_edges = "//*[@id='collection_worldEdges']/div/h5"
            world_vertices = "//*[@id='collection_worldVertices']/div/h5"

            world_edges = BaseSelenium.locator_finder_by_xpath(self, world_edges)
            search1 = BaseSelenium.locator_finder_by_id(self, search1)
            search1.click()
            search1.clear()
            search1.send_keys("worldEdges")
            if world_edges.text == 'worldEdges':
                print("worldEdges collection creation has been validated.\n")
            else:
                print("worldEdges collection not found\n")
            time.sleep(3)
            self.driver.refresh()

            world_vertices = BaseSelenium.locator_finder_by_xpath(self, world_vertices)
            search2 = BaseSelenium.locator_finder_by_id(self, search2)
            search2.click()
            search2.clear()
            search2.send_keys("worldVertices")
            if world_vertices.text == 'worldVertices':
                print("worldVertices collection creation has been validated.\n")
            else:
                print("worldVertices collection not found\n")
            time.sleep(3)

        elif graph == 6:
            search1 = self.select_search_id
            search2 = self.select_search_id
            search3 = self.select_search_id
            female = "//*[@id='collection_female']/div/h5"
            male = "//*[@id='collection_male']/div/h5"
            relation = "//*[@id='collection_relation']/div/h5"

            female = BaseSelenium.locator_finder_by_xpath(self, female)
            search1 = BaseSelenium.locator_finder_by_id(self, search1)
            search1.click()
            search1.clear()
            search1.send_keys("female")
            if female.text == 'female':
                print("female collection creation has been validated.\n")
            else:
                print("female collection not found\n")
            time.sleep(3)
            self.driver.refresh()

            male = BaseSelenium.locator_finder_by_xpath(self, male)
            search2 = BaseSelenium.locator_finder_by_id(self, search2)
            search2.click()
            search2.clear()
            search2.send_keys("male")
            if male.text == 'male':
                print("male collection creation has been validated.\n")
            else:
                print("male collection not found\n")
            time.sleep(3)
            self.driver.refresh()

            relation = BaseSelenium.locator_finder_by_xpath(self, relation)
            search3 = BaseSelenium.locator_finder_by_id(self, search3)
            search3.click()
            search3.clear()
            search3.send_keys("relation")
            if relation.text == 'relation':
                print("relation collection creation has been validated.\n")
            else:
                print("relation collection not found\n")
            time.sleep(3)

        elif graph == 7:
            search1 = self.select_search_id
            search2 = self.select_search_id
            search3 = self.select_search_id
            search4 = self.select_search_id
            search5 = self.select_search_id
            french_city = "//*[@id='collection_frenchCity']/div/h5"
            french_highway = '//*[@id="collection_frenchHighway"]/div/h5'
            german_city = '//*[@id="collection_germanCity"]/div/h5'
            german_highway = '//*[@id="collection_germanHighway"]/div/h5'
            international_highway = '//*[@id="collection_internationalHighway"]/div/h5'

            french_city = BaseSelenium.locator_finder_by_xpath(self, french_city)
            search1 = BaseSelenium.locator_finder_by_id(self, search1)
            search1.click()
            search1.clear()
            search1.send_keys("frenchCity")
            if french_city.text == 'frenchCity':
                print("frenchCity collection creation has been validated.\n")
            else:
                print("frenchCity collection not found\n")
            time.sleep(3)
            self.driver.refresh()

            french_highway = BaseSelenium.locator_finder_by_xpath(self, french_highway)
            search2 = BaseSelenium.locator_finder_by_id(self, search2)
            search2.click()
            search2.clear()
            search2.send_keys("frenchHighway")
            if french_highway.text == 'frenchHighway':
                print("frenchHighway collection creation has been validated.\n")
            else:
                print("frenchHighway collection not found\n")
            time.sleep(3)
            self.driver.refresh()

            german_city = BaseSelenium.locator_finder_by_xpath(self, german_city)
            search3 = BaseSelenium.locator_finder_by_id(self, search3)
            search3.click()
            search3.clear()
            search3.send_keys("germanCity")
            if german_city.text == 'germanCity':
                print("germanCity collection creation has been validated.\n")
            else:
                print("germanCity collection not found\n")
            time.sleep(3)
            self.driver.refresh()

            german_highway = BaseSelenium.locator_finder_by_xpath(self, german_highway)
            search4 = BaseSelenium.locator_finder_by_id(self, search4)
            search4.click()
            search4.clear()
            search4.send_keys("germanHighway")
            if german_highway.text == 'germanHighway':
                print("germanHighway collection creation has been validated.\n")
            else:
                print("germanHighway collection not found\n")
            time.sleep(3)
            self.driver.refresh()

            international_highway = BaseSelenium.locator_finder_by_xpath(self, international_highway)
            search5 = BaseSelenium.locator_finder_by_id(self, search5)
            search5.click()
            search5.clear()
            search5.send_keys("internationalHighway")
            if international_highway.text == 'internationalHighway':
                print("internationalHighway collection creation has been validated.\n")
            else:
                print("internationalHighway collection not found\n")
            time.sleep(3)

        self.driver.back()
        self.driver.refresh()

    def checking_collection_creation(self, graph):
        """Checking required collections creation for the particular example graph."""
        if graph == 1:
            self.select_knows_graphs_setting_btn_id_check = \
                BaseSelenium.locator_finder_by_id(self, self.select_knows_graphs_setting_btn_id_check)
            self.select_knows_graphs_setting_btn_id_check.click()
        elif graph == 2:
            self.select_traversal_graphs_setting_btn_id_check = \
                BaseSelenium.locator_finder_by_id(self, self.select_traversal_graphs_setting_btn_id_check)
            self.select_traversal_graphs_setting_btn_id_check.click()
        elif graph == 3:
            self.select_k_shortest_path_graphs_setting_btn_id_check = \
                BaseSelenium.locator_finder_by_id(self, self.select_k_shortest_path_graphs_setting_btn_id_check)
            self.select_k_shortest_path_graphs_setting_btn_id_check.click()
        elif graph == 4:
            self.select_maps_graphs_setting_btn_id_check = \
                BaseSelenium.locator_finder_by_id(self, self.select_maps_graphs_setting_btn_id_check)
            self.select_maps_graphs_setting_btn_id_check.click()
        elif graph == 5:
            self.select_world_graphs_setting_btn_id_check = \
                BaseSelenium.locator_finder_by_id(self, self.select_world_graphs_setting_btn_id_check)
            self.select_world_graphs_setting_btn_id_check.click()
        elif graph == 6:
            self.select_social_graphs_setting_btn_id_check = \
                BaseSelenium.locator_finder_by_id(self, self.select_social_graphs_setting_btn_id_check)
            self.select_social_graphs_setting_btn_id_check.click()
        elif graph == 7:
            self.select_route_planner_graphs_setting_btn_id_check = \
                BaseSelenium.locator_finder_by_id(self, self.select_route_planner_graphs_setting_btn_id_check)
            self.select_route_planner_graphs_setting_btn_id_check.click()
        else:
            print("Invalid Graph choice\n")

        time.sleep(3)
        self.select_graph_cancel_btn_id = \
            BaseSelenium.locator_finder_by_id(self, self.select_graph_cancel_btn_id)
        self.select_graph_cancel_btn_id.click()
        time.sleep(3)

    def select_sort_descend(self):
        """Sorting all graphs to descending and then ascending again"""
        self.select_sort_settings_id = \
            BaseSelenium.locator_finder_by_id(self, self.select_sort_settings_id)
        self.select_sort_settings_id.click()
        time.sleep(2)

        descend = self.select_sort_descend_id
        ascend = self.select_sort_descend_id

        print("Sorting Graphs to Descending\n")
        descend = \
            BaseSelenium.locator_finder_by_xpath(self, descend)
        descend.click()
        time.sleep(2)

        print("Sorting Graphs to Ascending\n")
        ascend = \
            BaseSelenium.locator_finder_by_xpath(self, ascend)
        ascend.click()
        time.sleep(2)

    def inspect_knows_graph(self):
        """Selecting Knows Graph for checking graph functionality"""
        print("Selecting Knows Graph\n")
        graph = self.knows_graph_id
        graph = BaseSelenium.locator_finder_by_id(self, graph)
        graph.click()
        time.sleep(4)

        print("Selecting Knows Graph share option\n")
        share = self.select_share_id
        share = BaseSelenium.locator_finder_by_xpath(self, share)
        share.click()
        time.sleep(2)

        print("Selecting load full graph button\n")
        full_graph = self.select_load_full_graph_id
        full_graph = BaseSelenium.locator_finder_by_id(self, full_graph)
        full_graph.click()
        time.sleep(4)

        print("Selecting Graph download button\n")
        camera = self.select_camera_download_icon
        camera = BaseSelenium.locator_finder_by_xpath(self, camera)
        camera.click()
        time.sleep(3)

        super().clear_download_bar()

        print("Selecting full screen mode\n")
        full_screen = self.select_full_screen_btn_id
        full_screen = BaseSelenium.locator_finder_by_xpath(self, full_screen)
        full_screen.click()
        time.sleep(3)
        print("Return to normal mode\n")
        super().escape()
        time.sleep(3)

        print("Selecting Resume layout button \n")
        resume = self.select_resume_layout_btn_id
        pause = self.select_resume_layout_btn_id

        resume = BaseSelenium.locator_finder_by_xpath(self, resume)
        resume.click()
        time.sleep(3)
        pause = BaseSelenium.locator_finder_by_xpath(self, pause)
        pause.click()
        time.sleep(3)

    def graph_setting(self):
        """Checking all the options inside graph settings"""
        configure_graph_settings_id = BaseSelenium.locator_finder_by_id(self, self.configure_graph_settings_id)
        configure_graph_settings_id.click()
        time.sleep(2)
        print("Selecting different layouts for the graph\n")
        print("Selecting Fruchtermann layout\n")
        layout2 = self.select_graph_layout_option_id
        BaseSelenium.locator_finder_by_select(self, layout2, 2)
        time.sleep(3)

        print("Selecting Force layout\n")
        layout1 = self.select_graph_layout_option_id
        BaseSelenium.locator_finder_by_select(self, layout1, 1)
        time.sleep(3)

        print("Selecting WebGL experimental renderer\n")
        renderer = self.select_renderer_id
        BaseSelenium.locator_finder_by_select(self, renderer, 1)
        time.sleep(3)

        print("Changing Search Depth\n")
        depth1 = self.select_depth_id
        depth2 = self.select_depth_id
        depth1 = BaseSelenium.locator_finder_by_xpath(self, depth1)
        depth1.clear()
        time.sleep(3)
        depth2 = BaseSelenium.locator_finder_by_xpath(self, depth2)
        depth2.send_keys("4")

        print("Changing Search Limit\n")
        limit = self.select_limit_id
        limit1 = self.select_limit_id
        limit2 = self.select_limit_id

        BaseSelenium.locator_finder_by_xpath(self, limit).click()
        time.sleep(2)
        limit1 = BaseSelenium.locator_finder_by_xpath(self, limit1)
        limit1.clear()
        limit2 = BaseSelenium.locator_finder_by_xpath(self, limit2)
        limit2.send_keys("300")
        time.sleep(3)

        print("Adding collection name with nodes to YES\n")
        BaseSelenium.locator_finder_by_select(self, self.add_collection_name_id, 0)
        time.sleep(3)

        print("Selecting color by collection to NO\n")
        BaseSelenium.locator_finder_by_select(self, self.select_color_collection_id, 0)
        time.sleep(3)

        print("Selecting size by edges to NO\n")
        BaseSelenium.locator_finder_by_select(self, self.select_size_by_edges_id, 1)
        time.sleep(3)

        print("Adding edge name to the node to YES\n")
        BaseSelenium.locator_finder_by_select(self, self.select_add_edge_col_name_id, 0)
        time.sleep(3)

        print("Adding Color by edge collection ot YES\n")
        BaseSelenium.locator_finder_by_select(self, self.select_color_node_by_edge_id, 1)
        time.sleep(3)

        print("Selecting different representation of relation between nodes\n")
        print("Maximizing the window")
        self.driver.maximize_window()
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

        self.driver.find_element_by_xpath(tip1).click()
        super().scroll(1)
        time.sleep(2)
        restore1 = BaseSelenium.locator_finder_by_xpath(self, restore1)
        restore1.click()
        time.sleep(1)

        print("Changing relation representation type to Line")
        BaseSelenium.locator_finder_by_select(self, type1, 0)
        time.sleep(5)

        self.driver.find_element_by_xpath(tip2).click()
        super().scroll(1)
        time.sleep(2)
        restore2 = BaseSelenium.locator_finder_by_xpath(self, restore2)
        restore2.click()
        time.sleep(1)

        print("Changing relation representation type to Curve")
        BaseSelenium.locator_finder_by_select(self, type3, 2)
        time.sleep(5)

        self.driver.find_element_by_xpath(tip4).click()
        super().scroll(1)
        time.sleep(2)
        restore4 = BaseSelenium.locator_finder_by_xpath(self, restore4)
        restore4.click()
        time.sleep(1)

        print("Changing relation representation type to Dotted")
        BaseSelenium.locator_finder_by_select(self, type4, 3)
        time.sleep(5)

        self.driver.find_element_by_xpath(tip5).click()
        super().scroll(1)
        time.sleep(2)
        restore5 = BaseSelenium.locator_finder_by_xpath(self, restore5)
        restore5.click()
        time.sleep(1)

        print("Changing relation representation type to Dashed")
        BaseSelenium.locator_finder_by_select(self, type5, 4)
        time.sleep(5)

        self.driver.find_element_by_xpath(tip6).click()
        super().scroll(1)
        time.sleep(2)
        restore6 = BaseSelenium.locator_finder_by_xpath(self, restore6)
        restore6.click()
        time.sleep(1)

        print("Changing relation representation type to Tapered\n")
        BaseSelenium.locator_finder_by_select(self, type6, 5)
        time.sleep(5)

        print("Going Back to original window size \n")
        self.driver.set_window_size(1250, 1000)  # custom window size
        self.driver.back()
        time.sleep(3)

    def delete_graph(self, graph):
        """Deleting created graphs"""
        if graph == 1:
            self.select_knows_graphs_setting_btn_id = \
                BaseSelenium.locator_finder_by_id(self, self.select_knows_graphs_setting_btn_id)
            self.select_knows_graphs_setting_btn_id.click()
            print("Deleting knows Graph\n")
            time.sleep(1)
        elif graph == 2:
            self.select_traversal_graphs_setting_btn_id = \
                BaseSelenium.locator_finder_by_id(self, self.select_traversal_graphs_setting_btn_id)
            self.select_traversal_graphs_setting_btn_id.click()
            print("Deleting Traversal Graph\n")
            time.sleep(2)
        elif graph == 3:
            self.select_k_shortest_path_graphs_setting_btn_id = \
                BaseSelenium.locator_finder_by_id(self, self.select_k_shortest_path_graphs_setting_btn_id)
            self.select_k_shortest_path_graphs_setting_btn_id.click()
            print("Deleting K Shortest Path Graph\n")
            time.sleep(1)
        elif graph == 4:
            self.select_maps_graphs_setting_btn_id = \
                BaseSelenium.locator_finder_by_id(self, self.select_maps_graphs_setting_btn_id)
            self.select_maps_graphs_setting_btn_id.click()
            print("Deleting Mps Graph\n")
            time.sleep(1)
        elif graph == 5:
            self.select_world_graphs_setting_btn_id = \
                BaseSelenium.locator_finder_by_id(self, self.select_world_graphs_setting_btn_id)
            self.select_world_graphs_setting_btn_id.click()
            print("Deleting World Graph\n")
            time.sleep(1)
        elif graph == 6:
            self.select_social_graphs_setting_btn_id = \
                BaseSelenium.locator_finder_by_id(self, self.select_social_graphs_setting_btn_id)
            self.select_social_graphs_setting_btn_id.click()
            print("Deleting Social Graph\n")
            time.sleep(1)
        elif graph == 7:
            self.select_route_planner_graphs_setting_btn_id = \
                BaseSelenium.locator_finder_by_id(self, self.select_route_planner_graphs_setting_btn_id)
            self.select_route_planner_graphs_setting_btn_id.click()
            print("Deleting City Graph\n")
            time.sleep(1)
        elif graph == 8:
            self.select_connected_graphs_setting_btn_id = \
                BaseSelenium.locator_finder_by_id(self, self.select_connected_graphs_setting_btn_id)
            self.select_connected_graphs_setting_btn_id.click()
            print("Deleting Connected Component Graph\n")
            time.sleep(1)
        # for manual graph
        elif graph == 9:
            self.select_knows_graph_manual_id = \
                BaseSelenium.locator_finder_by_id(self, self.select_knows_graph_manual_id)
            self.select_knows_graph_manual_id.click()
            print("Deleting knows_graph_manual Graph\n")
            time.sleep(1)
        else:
            print("Invalid Graph")

        self.confirm_delete_graph_id = \
            BaseSelenium.locator_finder_by_id(self, self.confirm_delete_graph_id)
        self.confirm_delete_graph_id.click()
        time.sleep(1)

        self.delete_with_collection_id = \
            BaseSelenium.locator_finder_by_id(self, self.delete_with_collection_id)
        self.delete_with_collection_id.click()
        time.sleep(1)

        self.select_really_delete_btn_id = \
            BaseSelenium.locator_finder_by_id(self, self.select_really_delete_btn_id)
        self.select_really_delete_btn_id.click()
        time.sleep(3)
