
#!/usr/bin/env python
"""
aardvark graphs page object
"""
import time
from enum import IntEnum

from selenium_ui_test.base_selenium import BaseSelenium, Keys
# can't circumvent long lines.. nAttr nLines
# pylint: disable=C0301 disable=C0302 disable=R0902 disable=R0915 disable=R0914


class GraphExample(IntEnum):
    KNOWS = 1
    TRAVERSAL = 2
    K_SHORTEST_PATH = 3
    MAPS = 4
    WORLD = 5
    SOCIAL = 6
    CITY = 7
    # enterprise? CONNECTED = 8
class vCol():
    def __init__(self, name):
        self.name = name
        self.ctype = 'v'
    
class eCol(vCol):
    def __init__(self, name):
        self.name = name
        self.ctype = 'e'
    
class GraphCreateSet():
    def __init__(self, clear_name, btn_id, collections, handler):
        self.clear_name = clear_name
        self.btn_id = btn_id
        self.handler = handler
        self.collections = collections

GRAPH_SETS = [
    GraphCreateSet(None, None, [], None),
    GraphCreateSet("Knows", "knows_graph_settings", [ vCol('persons'), eCol('knows') ], None),
    GraphCreateSet("Traversal", "traversalGraph_settings", [vCol('circles'), eCol('edges')], None),
    GraphCreateSet("kShortestPaths", "kShortestPathsGraph_settings", [ vCol('places'), eCol('edges') ], None),
    GraphCreateSet("Mps", "mps_graph_settings", [ vCol('mps_verts'), eCol('mps_edges') ], None),
    GraphCreateSet("World", "worldCountry_settings", [ vCol('worldVertices'), eCol('worldEdges') ], None),
    GraphCreateSet("Social", "social_settings", [ vCol('male'), vCol('female'), eCol('relation') ], None),
    GraphCreateSet("City", "routeplanner_settings", [
        vCol('frenchCity'),
        vCol('germanCity'),
        eCol('frenchHighway'),
        eCol('germanHighway'),
        eCol('internationalHighway')
    ], None),
    GraphCreateSet("Connected Components", "connectedComponentsGraph_settings", [], None) #TODO?
]

def get_graph_name(graph:GraphExample):
    return GRAPH_SETS[graph].clear_name

class GraphPage(BaseSelenium):
    """class for Graph page"""

    def __init__(self, driver):
        """Graph page initialization"""
        super().__init__()
        self.driver = driver
        self.select_graph_page_id = "graphs"
        self.select_create_graph_id = "createGraph"
        self.select_example_graph_btn_id = "tab-exampleGraphs"
        self.select_ex_graph_format = "//*[@id='exampleGraphs']/table/tbody/tr[%d]/td[2]/button"
        
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

    def create_manual_graph(self, testdata_path):
        """creating graph manually"""
        collection_page = self.locator_finder_by_id(self.select_collection_page_id)
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
        path1 = testdata_path / 'ui_data' / 'graph_page' / 'knows' / 'knows_edge.json'

        print("Creating knows_edge collections for knows_graph_manual Graph\n")
        col1 = self.locator_finder_by_id(col1)
        col1.click()

        col1_name = self.locator_finder_by_id(col1_name)
        col1_name.click()
        col1_name.send_keys("knows_edge")

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

        print("Importing knows_edge.json to the collection\n")
        col1_import = self.locator_finder_by_id(col1_import)
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
        path2 = testdata_path / 'ui_data' / 'graph_page' / 'knows' / 'persons.json'

        print("Creating person_vertices collections for knows_graph_manual Graph\n")
        col2 = self.locator_finder_by_id(col2)
        col2.click()

        col2_name = self.locator_finder_by_id(col2_name)
        col2_name.click()
        col2_name.send_keys("persons")

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

        print("Importing person_vertices.json to the collection\n")
        col2_import = self.locator_finder_by_id(col2_import)
        col2_import.click()
        time.sleep(3)
        print("Importing person_vertices.json to the collection completed\n")

    def select_graph_page(self):
        """selecting Graph tab"""
        select_graph_page_id = self.locator_finder_by_id(self.select_graph_page_id)
        select_graph_page_id.click()

    def adding_knows_manual_graph(self):
        """adding knows_graph_manual graph"""
        select_graph_id = self.locator_finder_by_id(self.select_create_graph_id)
        select_graph_id.click()

        # list of id's for manual graph
        new_graph = self.select_new_graph_name_id
        edge_definition = "row_newEdgeDefinitions0"
        from_collection = "s2id_fromCollections0"
        to_collection = "s2id_toCollections0"
        create_btn_id = "modalButton1"
        knows_graph_id = '//*[@id="knows_graph_manual_tile"]/div/h5'

        new_graph = self.locator_finder_by_id(new_graph)
        new_graph.click()
        new_graph.clear()
        new_graph.send_keys("knows_graph_manual")

        # selecting edge definition from auto suggestion
        edge_definition = self.locator_finder_by_id(edge_definition)
        edge_definition.click()
        super().send_key_action(Keys.ENTER)

        # selecting from collection from auto suggestion
        from_collection = self.locator_finder_by_id(from_collection)
        from_collection.click()
        super().send_key_action(Keys.ENTER)

        time.sleep(1)

        # selecting to collection from auto suggestion
        to_collection = self.locator_finder_by_id(to_collection)
        to_collection.click()
        super().send_key_action(Keys.ENTER)

        time.sleep(1)

        # selecting create graph btn
        create_btn_id = self.locator_finder_by_id(create_btn_id)
        create_btn_id.click()

        time.sleep(2)

        # selecting newly created graph btn
        knows_graph_id = self.locator_finder_by_xpath(knows_graph_id)
        knows_graph_id.click()

        time.sleep(3)
        self.driver.back()

    def adding_satellite_graph(self, importer, testdata_path):
        """creating satellite graph"""
        if super().current_package_version() >= 3.8:
            self.select_graph_page()
            knows_path = testdata_path / 'ui_data' / 'graph_page' / 'knows'
            select_graph = self.locator_finder_by_id(self.select_create_graph_id)
            select_graph.click()

            # list of id's for satellite graph
            select_satellite = 'tab-satelliteGraph'
            new_graph = self.select_new_graph_name_id
            edge_definition = "s2id_newEdgeDefinitions0"
            from_collection = "s2id_fromCollections0"
            to_collection = "s2id_toCollections0"
            create_btn_id = "modalButton1"

            # selecting satellite graph tab
            select_satellite = self.locator_finder_by_id(select_satellite)
            select_satellite.click()

            new_graph = self.locator_finder_by_id(new_graph)
            new_graph.click()
            new_graph.clear()
            new_graph.send_keys("satellite_graph")

            # selecting edge definition from auto suggestion
            edge_definition = self.locator_finder_by_id(edge_definition)
            edge_definition.click()
            super().send_key_action('knows_edge')
            super().send_key_action(Keys.ENTER)

            # selecting from collection from auto suggestion
            from_collection = self.locator_finder_by_id(from_collection)
            from_collection.click()
            super().send_key_action('persons')
            super().send_key_action(Keys.ENTER)

            time.sleep(1)

            # selecting to collection from auto suggestion
            to_collection = self.locator_finder_by_id(to_collection)
            to_collection.click()
            super().send_key_action('persons')
            super().send_key_action(Keys.ENTER)

            time.sleep(1)

            # selecting create graph btn
            create_btn_id = self.locator_finder_by_id(create_btn_id)
            create_btn_id.click()

            time.sleep(2)

            # importing collections using arangoimport
            print("Importing knows_edge collections \n")
            importer.import_smart_edge_collection("knows_edge", knows_path / 'knows_edge.json', ['profiles_smart'])

            print("Importing persons collections \n")
            importer.import_collection('persons', knows_path / 'persons.json')

            # Selecting satellite graph settings to view and delete
            satellite_settings_id = '//*[@id="satellite_graph_tile"]/div/h5'
            satellite_settings_id = self.locator_finder_by_xpath(satellite_settings_id)
            satellite_settings_id.click()

            time.sleep(5)
            self.driver.back()
            time.sleep(1)

            print("\n")
            print("Smart Graph deleting started \n")
            satellite_settings_id = 'satellite_graph_settings'
            satellite_settings_id = self.locator_finder_by_id(satellite_settings_id)
            satellite_settings_id.click()

            delete_btn = 'modalButton0'
            delete_btn = self.locator_finder_by_id(delete_btn)
            delete_btn.click()

            delete_check_id = 'dropGraphCollections'
            delete_check_id = self.locator_finder_by_id(delete_check_id)
            delete_check_id.click()

            delete_confirm_btn = 'modal-confirm-delete'
            delete_confirm_btn = self.locator_finder_by_id(delete_confirm_btn)
            delete_confirm_btn.click()

            time.sleep(2)
            print("Satellite Graph deleted successfully \n")
            self.driver.refresh()
        else:
            print('Satellite Graph is not supported for the current package \n')

    def adding_smart_graph(self, importer, testdata_path, disjointgraph=False):
        """Adding smart disjoint graph"""
        page_path = testdata_path / 'ui_data' / 'graph_page' / 'pregel_community'
        
        if super().current_package_version() >= 3.6 and disjointgraph is False:
            select_graph_id = self.select_create_graph_id
            select_graph_id = self.locator_finder_by_id(select_graph_id)
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
            select_smart = self.locator_finder_by_id(select_smart)
            select_smart.click()

            new_graph = self.locator_finder_by_id(new_graph)
            new_graph.click()
            new_graph.clear()
            new_graph.send_keys("smart_graph")

            # specifying number of shards
            shard = self.locator_finder_by_id(shard)
            shard.click()
            shard.send_keys('3')

            # specifying replication of shards
            replication = self.locator_finder_by_id(replication)
            replication.click()
            replication.send_keys('3')

            # specifying write concern of shards
            write_concern = self.locator_finder_by_id(write_concern)
            write_concern.click()
            write_concern.send_keys('1')

            # specifying write disjoint graphs
            if disjointgraph:
                disjoint = self.locator_finder_by_id(disjoint)
                disjoint.click()
            else:
                print('Disjoint Graph not selected. \n')

            # specifying write concern of shards
            smart_attribute = self.locator_finder_by_id(smart_attribute)
            smart_attribute.click()
            smart_attribute.send_keys('community')

            # scrolling down
            super().scroll(1)
            time.sleep(2)

            # selecting edge definition from auto suggestion
            edge_definition = self.locator_finder_by_id(edge_definition)
            edge_definition.click()

            super().send_key_action('relations')
            super().send_key_action(Keys.ENTER)

            # selecting from collection from auto suggestion
            from_collection = self.locator_finder_by_id(from_collection)
            from_collection.click()
            super().send_key_action('profiles')
            super().send_key_action(Keys.ENTER)

            time.sleep(1)

            # selecting to collection from auto suggestion
            to_collection = self.locator_finder_by_id(to_collection)
            to_collection.click()
            super().send_key_action('profiles')
            super().send_key_action(Keys.ENTER)
            time.sleep(1)

            # selecting create graph btn
            create_btn_id = self.locator_finder_by_id(create_btn_id)
            create_btn_id.click()
            time.sleep(2)

            print("Importing profile collections \n")
            importer.import_collection('profiles', page_path / 'profiles.jsonl')

            print("Importing relations collections \n")
            importer.import_smart_edge_collection('relations', page_path / 'relations.jsonl', ['profiles_smart'])

            # opening smart graph
            smart_graph = 'smart_graph_tile'
            smart_graph = self.locator_finder_by_id(smart_graph)
            smart_graph.click()
            time.sleep(2)

            # loading full graph
            load_graph = 'loadFullGraph'
            load_graph = self.locator_finder_by_id(load_graph)
            load_graph.click()
            time.sleep(1)

            load_full_graph = 'modalButton1'
            load_full_graph = self.locator_finder_by_id(load_full_graph)
            load_full_graph.click()
            time.sleep(5)

            self.driver.back()

            time.sleep(2)

            print("\n")
            print("Smart Graph deleting started \n")
            smart_settings = 'smart_graph_settings'
            smart_settings = self.locator_finder_by_id(smart_settings)
            smart_settings.click()

            delete_btn = 'modalButton0'
            delete_btn = self.locator_finder_by_id(delete_btn)
            delete_btn.click()

            delete_check_id = 'dropGraphCollections'
            delete_check_id = self.locator_finder_by_id(delete_check_id)
            delete_check_id.click()

            delete_confirm_btn = 'modal-confirm-delete'
            delete_confirm_btn = self.locator_finder_by_id(delete_confirm_btn)
            delete_confirm_btn.click()

            time.sleep(2)
            print("Smart Graph deleted successfully \n")

            self.driver.refresh()
        else:
            print('Disjoint Graph is not supported for the current package \n')


    def select_create_graph(self, graph:GraphExample):
        """Creating new example graphs"""
        select_graph =  self.locator_finder_by_id(self.select_create_graph_id)
        select_graph.click()
        time.sleep(1)
        # Selecting example graph button
        select_example_graph_elm = self.locator_finder_by_id(
            self.select_example_graph_btn_id)
        select_example_graph_elm.click()
        time.sleep(1)
        create_graph = GRAPH_SETS[graph]
        select_graph_button = self.locator_finder_by_xpath(
            self.select_ex_graph_format % (int(graph)))
        select_graph_button.click()
        time.sleep(10)

    def check_required_collections(self, graph):
        """selecting collection tab and search for required collections"""
        collection_page = self.select_collection_page_id
        collection_page = self.locator_finder_by_id(collection_page)
        collection_page.click()

        for collection in GRAPH_SETS[graph].collections:
            search_collection_id = "//*[@id='collection_%s']/div/h5" % collection.name
            collection_item = self.locator_finder_by_xpath(search_collection_id)
            search_item = self.locator_finder_by_id(self.select_search_id)
            search_item.click()
            search_item.clear()
            search_item.send_keys(collection.name)
            if collection_item.text == collection.name:
                print(collection.name + " collectionhas been validated")
            else:
                print(collection.name + " collection wasn't found")
            time.sleep(3)
            self.driver.refresh()


        self.driver.back()
        self.driver.refresh()

    def checking_collection_creation(self, graph):
        """Checking required collections creation for the particular example graph."""
        if graph == 1:
            select_knows_graphs_setting_btn_id_check = \
                self.locator_finder_by_id(self.select_knows_graphs_setting_btn_id_check)
            select_knows_graphs_setting_btn_id_check.click()
        elif graph == 2:
            select_traversal_graphs_setting_btn_id_check = \
                self.locator_finder_by_id(self.select_traversal_graphs_setting_btn_id_check)
            select_traversal_graphs_setting_btn_id_check.click()
        elif graph == 3:
            select_k_shortest_path_graphs_setting_btn_id_check = \
                self.locator_finder_by_id(self.select_k_shortest_path_graphs_setting_btn_id_check)
            select_k_shortest_path_graphs_setting_btn_id_check.click()
        elif graph == 4:
            select_maps_graphs_setting_btn_id_check = \
                self.locator_finder_by_id(self.select_maps_graphs_setting_btn_id_check)
            select_maps_graphs_setting_btn_id_check.click()
        elif graph == 5:
            select_world_graphs_setting_btn_id_check = \
                self.locator_finder_by_id(self.select_world_graphs_setting_btn_id_check)
            select_world_graphs_setting_btn_id_check.click()
        elif graph == 6:
            select_social_graphs_setting_btn_id_check = \
                self.locator_finder_by_id(self.select_social_graphs_setting_btn_id_check)
            select_social_graphs_setting_btn_id_check.click()
        elif graph == 7:
            select_route_planner_graphs_setting_btn_id_check = \
                self.locator_finder_by_id(self.select_route_planner_graphs_setting_btn_id_check)
            select_route_planner_graphs_setting_btn_id_check.click()
        else:
            print("Invalid Graph choice\n")

        time.sleep(3)
        select_graph_cancel_btn_id = \
            self.locator_finder_by_id(self.select_graph_cancel_btn_id)
        select_graph_cancel_btn_id.click()
        time.sleep(3)

    def select_sort_descend(self):
        """Sorting all graphs to descending and then ascending again"""
        select_sort_settings_id = \
            self.locator_finder_by_id(self.select_sort_settings_id)
        select_sort_settings_id.click()
        time.sleep(2)

        descend = self.select_sort_descend_id
        ascend = self.select_sort_descend_id

        print("Sorting Graphs to Descending\n")
        descend = self.locator_finder_by_xpath(descend)
        descend.click()
        time.sleep(2)

        print("Sorting Graphs to Ascending\n")
        ascend = self.locator_finder_by_xpath(ascend)
        ascend.click()
        time.sleep(2)

    def inspect_knows_graph(self):
        """Selecting Knows Graph for checking graph functionality"""
        print("Selecting Knows Graph\n")
        graph = self.knows_graph_id
        graph = self.locator_finder_by_id(graph)
        graph.click()
        time.sleep(4)

        print("Selecting Knows Graph share option\n")
        share = self.select_share_id
        share = self.locator_finder_by_xpath(share)
        share.click()
        time.sleep(2)

        print("Selecting load full graph button\n")
        full_graph = self.select_load_full_graph_id
        full_graph = self.locator_finder_by_id(full_graph)
        full_graph.click()
        time.sleep(4)

        if self.driver.name == "chrome":  # this will check browser name
            print("Download has been disabled for the Chrome browser \n")
        else:
            print("Selecting Graph download button\n")
            camera = self.select_camera_download_icon
            camera = self.locator_finder_by_xpath(camera)
            camera.click()
            time.sleep(3)
            # super().clear_download_bar()

        print("Selecting full screen mode\n")
        full_screen = self.select_full_screen_btn_id
        full_screen = self.locator_finder_by_xpath(full_screen)
        full_screen.click()
        time.sleep(3)
        print("Return to normal mode\n")
        super().escape()
        time.sleep(3)

        print("Selecting Resume layout button \n")
        resume = self.select_resume_layout_btn_id
        pause = self.select_resume_layout_btn_id

        resume = self.locator_finder_by_xpath(resume)
        resume.click()
        time.sleep(3)
        pause = self.locator_finder_by_xpath(pause)
        pause.click()
        time.sleep(3)

    def graph_setting(self):
        """Checking all the options inside graph settings"""
        configure_graph_settings_id = self.locator_finder_by_id(self.configure_graph_settings_id)
        configure_graph_settings_id.click()
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
        restore1 = self.locator_finder_by_xpath(restore1)
        restore1.click()
        time.sleep(1)

        print("Changing relation representation type to Line")
        self.locator_finder_by_select(type1, 0)
        time.sleep(5)

        self.driver.find_element_by_xpath(tip2).click()
        super().scroll(1)
        time.sleep(2)
        restore2 = self.locator_finder_by_xpath(restore2)
        restore2.click()
        time.sleep(1)

        print("Changing relation representation type to Curve")
        self.locator_finder_by_select(type3, 2)
        time.sleep(5)

        self.driver.find_element_by_xpath(tip4).click()
        super().scroll(1)
        time.sleep(2)
        restore4 = self.locator_finder_by_xpath(restore4)
        restore4.click()
        time.sleep(1)

        print("Changing relation representation type to Dotted")
        self.locator_finder_by_select(type4, 3)
        time.sleep(5)

        self.driver.find_element_by_xpath(tip5).click()
        super().scroll(1)
        time.sleep(2)
        restore5 = self.locator_finder_by_xpath(restore5)
        restore5.click()
        time.sleep(1)

        print("Changing relation representation type to Dashed")
        self.locator_finder_by_select(type5, 4)
        time.sleep(5)

        self.driver.find_element_by_xpath(tip6).click()
        super().scroll(1)
        time.sleep(2)
        restore6 = self.locator_finder_by_xpath(restore6)
        restore6.click()
        time.sleep(1)

        print("Changing relation representation type to Tapered\n")
        self.locator_finder_by_select(type6, 5)
        time.sleep(5)

        print("Going Back to original window size \n")
        self.driver.set_window_size(1250, 1000)  # custom window size
        self.driver.back()
        time.sleep(3)

    def delete_graph(self, graph):
        """Deleting created graphs"""
        if graph == 1:
            select_knows_graphs_setting_btn_id = \
                self.locator_finder_by_id(self.select_knows_graphs_setting_btn_id)
            select_knows_graphs_setting_btn_id.click()
            print("Deleting knows Graph\n")
            time.sleep(1)
        elif graph == 2:
            select_traversal_graphs_setting_btn_id = \
                self.locator_finder_by_id(self.select_traversal_graphs_setting_btn_id)
            select_traversal_graphs_setting_btn_id.click()
            print("Deleting Traversal Graph\n")
            time.sleep(2)
        elif graph == 3:
            select_k_shortest_path_graphs_setting_btn_id = \
                self.locator_finder_by_id(self.select_k_shortest_path_graphs_setting_btn_id)
            select_k_shortest_path_graphs_setting_btn_id.click()
            print("Deleting K Shortest Path Graph\n")
            time.sleep(1)
        elif graph == 4:
            select_maps_graphs_setting_btn_id = \
                self.locator_finder_by_id(self.select_maps_graphs_setting_btn_id)
            select_maps_graphs_setting_btn_id.click()
            print("Deleting Mps Graph\n")
            time.sleep(1)
        elif graph == 5:
            select_world_graphs_setting_btn_id = \
                self.locator_finder_by_id(self.select_world_graphs_setting_btn_id)
            select_world_graphs_setting_btn_id.click()
            print("Deleting World Graph\n")
            time.sleep(1)
        elif graph == 6:
            select_social_graphs_setting_btn_id = \
                self.locator_finder_by_id(self.select_social_graphs_setting_btn_id)
            select_social_graphs_setting_btn_id.click()
            print("Deleting Social Graph\n")
            time.sleep(1)
        elif graph == 7:
            select_route_planner_graphs_setting_btn_id = \
                self.locator_finder_by_id(self.select_route_planner_graphs_setting_btn_id)
            select_route_planner_graphs_setting_btn_id.click()
            print("Deleting City Graph\n")
            time.sleep(1)
        elif graph == 8:
            select_connected_graphs_setting_btn_id = \
                self.locator_finder_by_id(self.select_connected_graphs_setting_btn_id)
            select_connected_graphs_setting_btn_id.click()
            print("Deleting Connected Component Graph\n")
            time.sleep(1)
        # for manual graph
        elif graph == 9:
            select_knows_graph_manual_id = \
                self.locator_finder_by_id(self.select_knows_graph_manual_id)
            select_knows_graph_manual_id.click()
            print("Deleting knows_graph_manual Graph\n")
            time.sleep(1)
        else:
            print("Invalid Graph")

        confirm_delete_graph_id = \
            self.locator_finder_by_id(self.confirm_delete_graph_id)
        confirm_delete_graph_id.click()
        time.sleep(1)

        delete_with_collection_id = \
            self.locator_finder_by_id(self.delete_with_collection_id)
        delete_with_collection_id.click()
        time.sleep(1)

        select_really_delete_btn_id = \
            self.locator_finder_by_id(self.select_really_delete_btn_id)
        select_really_delete_btn_id.click()
        time.sleep(3)
