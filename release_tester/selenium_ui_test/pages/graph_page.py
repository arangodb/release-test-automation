#!/usr/bin/env python
"""graph testsuite"""
import time
from enum import IntEnum
import semver
from selenium_ui_test.pages.base_page import Keys
from selenium.webdriver.common.by import By
from selenium_ui_test.pages.navbar import NavigationBarPage
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException

# can't circumvent long lines.. nAttr nLines
# pylint: disable=line-too-long disable=too-many-lines disable=too-many-instance-attributes disable=too-many-statements disable=too-many-locals


class GraphExample(IntEnum):
    """identify example and manual graphs to be managed herein"""

    # pylint: disable=too-few-public-methods
    KNOWS = 1
    TRAVERSAL = 2
    K_SHORTEST_PATH = 3
    MAPS = 4
    WORLD = 5
    SOCIAL = 6
    CITY = 7
    CONNECTED = 8
    # these are non graph-example tabs; their index doesn't align with their table column:
    # if more example graphs are added, add them above, move numbers.
    MANUAL_KNOWS = 9 # overlaps with knows graph
    MANUAL_SATELLITE_GRAPH = 10 # overlaps with knows graph
    MANUAL_SMART_GRAHP = 11
    MANUAL_DISJOINT_SMART_GRAHP = 12


class VCol:
    """maps a vertex collection to a graph"""

    # pylint: disable=too-few-public-methods
    def __init__(self, name):
        self.name = name
        self.ctype = "v"


class ECol:
    """maps an edge collection to a graph"""

    # pylint: disable=too-few-public-methods
    def __init__(self, name):
        self.name = name
        self.ctype = "e"

ALL_VERSIONS="3.0.0"
class GraphCreateSet:
    """this has all we need to know to create an example graph"""

    # pylint: disable=too-few-public-methods disable=too-many-arguments
    def __init__(self, clear_name, btn_id, collections,
                 handler=None,
                 enterprise=False,
                 min_version=ALL_VERSIONS,
                 non_cl_min_ver=ALL_VERSIONS):
        self.clear_name = clear_name
        self.btn_id = btn_id
        self.handler = handler
        self.collections = collections
        self.min_version = semver.VersionInfo.parse(min_version)
        self.non_cl_min_ver = non_cl_min_ver
        self.requires_enterprise = enterprise

    def is_graph_supported(self, enterprise, version, is_cluster):
        """will this graph be supported in your environment?"""
        if self.requires_enterprise and not enterprise:
            return False
        if not is_cluster and version < self.non_cl_min_ver:
            return False
        return version > self.min_version

    def get_name(self):
        """resolves the enum to a printeable string"""
        return self.clear_name

GRAPH_SETS = []

def get_graph(graph: GraphExample):
    """look up the graph"""
    try:
        return GRAPH_SETS[graph]
    except IndexError as ex:
        raise Exception("unknown Graph " + str(graph)) from ex


class GraphPage(NavigationBarPage):
    """class for Graph page"""

    def __init__(self, driver, cfg):
        """Graph page initialization"""
        super().__init__(driver, cfg)
        self.select_graph_page_id = "graphs"
        self.select_create_graph_id = "createGraph"
        self.select_example_graph_btn_id = "tab-exampleGraphs"
        self.select_ex_graph_format = "//*[@id='exampleGraphs']/table/tbody/tr[%d]/td[2]/button"

        self.confirm_delete_graph_selector = "//button[text()='Delete' and not(ancestor::div[contains(@style,'display:none')]) and not(ancestor::div[contains(@style,'display: none')])]"
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
        self.selected_dropdown_class = (
            "select2-results-dept-0.select2-result.select2-result-selectable.select2-highlighted"
        )

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

    
    def checking_created_collections_for_312(self, graph_name):
        """selecting collection tab"""
        # todo add navigation instead
        self.navbar_goto("collections")
        self.wait_for_ajax()
        self.webdriver.maximize_window()
        time.sleep(1)

        # reset = "//*[text()='Reset']"
        # reset_sitem = self.locator_finder_by_xpath(reset)
        # reset_sitem.click()
        # time.sleep(1)

        filters = "//*[text()='Filters']"
        filters_sitem = self.locator_finder_by_xpath(filters)
        filters_sitem.click()
        time.sleep(1)

        # selecting add_filter
        add_filter = "//button[contains(@class, 'chakra-button') and @aria-label='Add filter']"
        add_filter_sitem = self.locator_finder_by_xpath(add_filter)
        add_filter_sitem.click()
        time.sleep(1)

        # selecting name filter from the filter type
        name_filter = "(//button[normalize-space()='Name'])[1]"
        name_filter_sitem = self.locator_finder_by_xpath(name_filter)
        name_filter_sitem.click()
        time.sleep(1)

        # selecting name filter search input field
        selecting_search_input = "(//input[@id='name'])[1]"
        selecting_search_input_sitem = self.locator_finder_by_xpath(
            selecting_search_input
        )
        selecting_search_input_sitem.click()
        time.sleep(1)
        selecting_search_input_sitem.clear()
        selecting_search_input_sitem.send_keys("knows")

        if graph_name == "knows_graph":
            knows_collection = "(//a[normalize-space()='knows'])[1]"
            knows_collection_sitem = self.locator_finder_by_xpath(knows_collection)

            expected_title = "knows"
            try:
                assert (
                        expected_title == knows_collection_sitem.text
                ), f"Expected page title {expected_title} but got {knows_collection_sitem.text}"
            except AssertionError:
                print(f"Assertion Error occurred! for {expected_title}\n")
        
        self.webdriver.set_window_size(1600, 900)
    
    
    def create_example_graph_for_312(self, graph_name):
        """Creating example graphs"""
        self.webdriver.refresh()
        self.navbar_goto("graphs")
        self.wait_for_ajax()

        print(f"selecting {graph_name} \n")

        select_graph = "//*[text()='Add graph']"
        select_graph = self.locator_finder_by_xpath(select_graph)
        select_graph.click()
        time.sleep(1)
        # Selecting example graph button
        example_btn = "//*[text()='Examples']"
        example_btn_sitem = self.locator_finder_by_xpath(example_btn)
        example_btn_sitem.click()
        time.sleep(1)

        if graph_name == "Knows Graph":
            self.select_knows_graph_id = self.locator_finder_by_xpath(
                "(//button[@type='submit'][normalize-space()='Create'])[1]"
            )
            self.select_knows_graph_id.click()

            # TODO
            # print(f"Checking required collections created for {graph_name}\n")
            # self.checking_created_collections_for_312("knows_graph")

        elif graph_name == "Traversal Graph":
            self.select_traversal_graph_id = self.locator_finder_by_xpath(
                "(//button[@type='submit'][normalize-space()='Create'])[2]"
            )
            self.select_traversal_graph_id.click()
        elif graph_name == "k Shortest Paths Graph":
            self.select_k_shortest_path_id = self.locator_finder_by_xpath(
                "(//button[@type='submit'][normalize-space()='Create'])[3]"
            )
            self.select_k_shortest_path_id.click()
        elif graph_name == "Mps Graph":
            self.select_maps_graph_id = self.locator_finder_by_xpath(
                "(//button[@type='submit'][normalize-space()='Create'])[4]"
            )
            self.select_maps_graph_id.click()
        elif graph_name == "World Graph":
            self.select_world_graph_id = self.locator_finder_by_xpath(
                "(//button[@type='submit'][normalize-space()='Create'])[5]"
            )
            self.select_world_graph_id.click()
        elif graph_name == "Social Graph":
            self.select_social_graph_id = self.locator_finder_by_xpath(
                "(//button[@type='submit'][normalize-space()='Create'])[6]"
            )
            self.select_social_graph_id.click()
        elif graph_name == "City Graph":
            self.select_city_graph_id = self.locator_finder_by_xpath(
                "(//button[@type='submit'][normalize-space()='Create'])[7]"
            )
            self.select_city_graph_id.click()
        else:
            print("Invalid Graph\n")
        time.sleep(3)
        self.wait_for_ajax()
    
    def checking_created_collections(self, graph_name):
        """This method will check all the example graphs created collections"""
        self.wait_for_ajax()
        # todo add navigation instead
        print(f"Checking created collections for {graph_name}")
        self.navbar_goto("collections")
        self.wait_for_ajax()

        if graph_name == "Knows Graph":
            self.wait_for_ajax()
            knows_collection = '//*[@id="collection_knows"]/div/h5'
            knows_collection_sitem = self.locator_finder_by_xpath(knows_collection)
            expected_title = "knows"
            try:
                assert (
                    expected_title == knows_collection_sitem.text
                ), f"Expected page title {expected_title} but got {knows_collection_sitem.text}"
            except AssertionError as ex:
                raise Exception("Assertion Error occurred! for {expected_title} \n") from ex

            person_collection = '//*[@id="collection_persons"]/div/h5'
            person_collection_sitem = self.locator_finder_by_xpath(person_collection)
            expected_title = "persons"
            try:
                assert (
                    expected_title == person_collection_sitem.text
                ), f"Expected page title {expected_title} but got {person_collection_sitem.text}"
            except AssertionError as ex:
                raise Exception("Assertion Error occurred! for {expected_title} \n") from ex
        elif graph_name == "Traversal Graph":
            self.wait_for_ajax()
            circle_collection = '//*[@id="collection_circles"]/div/h5'
            circle_collection_sitem = self.locator_finder_by_xpath(circle_collection)
            expected_title = "circles"
            try:
                assert (
                    expected_title == circle_collection_sitem.text
                ), f"Expected page title {expected_title} but got {circle_collection_sitem.text}"
            except AssertionError as ex:
                raise Exception("Assertion Error occurred! for {expected_title} \n") from ex

            edges_collection = '//*[@id="collection_edges"]/div/h5'
            edges_collection_sitem = self.locator_finder_by_xpath(edges_collection)
            expected_title = "edges"
            try:
                assert (
                    expected_title == edges_collection_sitem.text
                ), f"Expected page title {expected_title} but got {edges_collection_sitem.text}"
            except AssertionError as ex:
                raise Exception("Assertion Error occurred! for {expected_title} \n") from ex
        elif graph_name == "k Shortest Paths Graph":
            self.wait_for_ajax()
            connections_collection = '//*[@id="collection_connections"]/div/h5'
            connections_collection_sitem = self.locator_finder_by_xpath(
                connections_collection
            )
            expected_title = "connections"
            try:
                assert (
                    expected_title == connections_collection_sitem.text
                ), f"Expected page title {expected_title} but got {connections_collection_sitem.text}"
            except AssertionError as ex:
                raise Exception("Assertion Error occurred! for {expected_title} \n") from ex

            places_collection = '//*[@id="collection_places"]/div/h5'
            places_collection_sitem = self.locator_finder_by_xpath(places_collection)
            expected_title = "places"
            try:
                assert (
                    expected_title == places_collection_sitem.text
                ), f"Expected page title {expected_title} but got {places_collection_sitem.text}"
            except AssertionError as ex:
                raise Exception("Assertion Error occurred! for {expected_title} \n") from ex
        elif graph_name == "Mps Graph":
            self.wait_for_ajax()
            mps_verts_collection = '//*[@id="collection_mps_verts"]/div/h5'
            mps_verts_collection_sitem = self.locator_finder_by_xpath(
                mps_verts_collection
            )
            expected_title = "mps_verts"
            try:
                assert (
                    expected_title == mps_verts_collection_sitem.text
                ), f"Expected page title {expected_title} but got {mps_verts_collection_sitem.text}"
            except AssertionError as ex:
                raise Exception("Assertion Error occurred! for {expected_title} \n") from ex

            mps_edges_collection = '//*[@id="collection_mps_edges"]/div/h5'
            mps_edges_collection_sitem = self.locator_finder_by_xpath(
                mps_edges_collection
            )
            expected_title = "mps_edges"
            try:
                assert (
                    expected_title == mps_edges_collection_sitem.text
                ), f"Expected page title {expected_title} but got {mps_edges_collection_sitem.text}"
            except AssertionError as ex:
                raise Exception("Assertion Error occurred! for {expected_title} \n") from ex
        elif graph_name == "World Graph":
            self.wait_for_ajax()
            worldVertices_collection = '//*[@id="collection_worldVertices"]/div/h5'
            worldVertices_collection_sitem = self.locator_finder_by_xpath(
                worldVertices_collection
            )
            expected_title = "worldVertices"
            try:
                assert (
                    expected_title == worldVertices_collection_sitem.text
                ), f"Expected page title {expected_title} but got {worldVertices_collection_sitem.text}"
            except AssertionError as ex:
                raise Exception("Assertion Error occurred! for {expected_title} \n") from ex

            worldEdges_collection = '//*[@id="collection_worldEdges"]/div/h5'
            worldEdges_collection_sitem = self.locator_finder_by_xpath(
                worldEdges_collection
            )
            expected_title = "worldEdges"
            try:
                assert (
                    expected_title == worldEdges_collection_sitem.text
                ), f"Expected page title {expected_title} but got {worldEdges_collection_sitem.text}"
            except AssertionError as ex:
                raise Exception("Assertion Error occurred! for {expected_title} \n") from ex
        elif graph_name == "Social Graph":
            self.wait_for_ajax()
            male_collection = '//*[@id="collection_male"]/div/h5'
            male_collection_sitem = self.locator_finder_by_xpath(male_collection)
            expected_title = "male"
            try:
                assert (
                    expected_title == male_collection_sitem.text
                ), f"Expected page title {expected_title} but got {male_collection_sitem.text}"
            except AssertionError as ex:
                raise Exception("Assertion Error occurred! for {expected_title} \n") from ex

            female_collection = '//*[@id="collection_female"]/div/h5'
            female_collection_sitem = self.locator_finder_by_xpath(female_collection)
            expected_title = "female"
            try:
                assert (
                    expected_title == female_collection_sitem.text
                ), f"Expected page title {expected_title} but got {female_collection_sitem.text}"
            except AssertionError as ex:
                raise Exception("Assertion Error occurred! for {expected_title} \n") from ex

            relation_collection = '//*[@id="collection_relation"]/div/h5'
            relation_collection_sitem = self.locator_finder_by_xpath(
                relation_collection
            )
            expected_title = "relation"
            try:
                assert (
                    expected_title == relation_collection_sitem.text
                ), f"Expected page title {expected_title} but got {relation_collection_sitem.text}"
            except AssertionError as ex:
                raise Exception("Assertion Error occurred! for {expected_title} \n") from ex
        elif graph_name == "City Graph":
            self.wait_for_ajax()
            frenchCity_collection = '//*[@id="collection_frenchCity"]/div/h5'
            frenchCity_collection_sitem = self.locator_finder_by_xpath(
                frenchCity_collection
            )
            expected_title = "frenchCity"
            try:
                assert (
                    expected_title == frenchCity_collection_sitem.text
                ), f"Expected page title {expected_title} but got {frenchCity_collection_sitem.text}"
            except AssertionError as ex:
                raise Exception("Assertion Error occurred! for {expected_title} \n") from ex

            germanCity_collection = '//*[@id="collection_germanCity"]/div/h5'
            germanCity_collection_sitem = self.locator_finder_by_xpath(
                germanCity_collection
            )
            expected_title = "germanCity"
            try:
                assert (
                    expected_title == germanCity_collection_sitem.text
                ), f"Expected page title {expected_title} but got {germanCity_collection_sitem.text}"
            except AssertionError as ex:
                raise Exception("Assertion Error occurred! for {expected_title} \n") from ex

            frenchHighway_collection = '//*[@id="collection_frenchHighway"]/div/h5'
            frenchHighway_collection_sitem = self.locator_finder_by_xpath(
                frenchHighway_collection
            )
            expected_title = "frenchHighway"
            try:
                assert (
                    expected_title == frenchHighway_collection_sitem.text
                ), f"Expected page title {expected_title} but got {frenchHighway_collection_sitem.text}"
            except AssertionError as ex:
                raise Exception("Assertion Error occurred! for {expected_title} \n") from ex

            germanHighway_collection = '//*[@id="collection_germanHighway"]/div/h5'
            germanHighway_collection_sitem = self.locator_finder_by_xpath(
                germanHighway_collection
            )
            expected_title = "germanHighway"
            try:
                assert (
                    expected_title == germanHighway_collection_sitem.text
                ), f"Expected page title {expected_title} but got {germanHighway_collection_sitem.text}"
            except AssertionError as ex:
                raise Exception("Assertion Error occurred! for {expected_title} \n") from ex

    
    def create_example_graph(self, graph_name):
        """This method will create all the example graphs"""
        self.webdriver.refresh()
        self.navbar_goto("graphs")
        self.wait_for_ajax()
        print(f"Creating {graph_name}\n")

        self.locator_finder_by_id(self.select_create_graph_id).click()
        time.sleep(1)
        # Selecting example graph button
        example_btn_sitem = self.locator_finder_by_id(self.select_example_graph_btn_id)
        example_btn_sitem.click()
        time.sleep(1)

        if graph_name == "Knows Graph":
            self.wait_for_ajax()
            graph_id = "(//button[@graph-id='knows_graph'])[1]"
            graph_id_sitem = self.locator_finder_by_xpath(graph_id)
            graph_id_sitem.click()
            time.sleep(3)
            self.checking_created_collections(graph_name)
        elif graph_name == "Traversal Graph":
            self.wait_for_ajax()
            graph_id = "(//button[@graph-id='traversalGraph'])[1]"
            graph_id_sitem = self.locator_finder_by_xpath(graph_id)
            graph_id_sitem.click()
            time.sleep(3)
            self.checking_created_collections(graph_name)
        elif graph_name == "k Shortest Paths Graph":
            self.wait_for_ajax()
            graph_id = "(//button[@graph-id='kShortestPathsGraph'])[1]"
            graph_id_sitem = self.locator_finder_by_xpath(graph_id)
            graph_id_sitem.click()
            time.sleep(3)
            self.checking_created_collections(graph_name)
        elif graph_name == "Mps Graph":
            self.wait_for_ajax()
            graph_id = "(//button[@graph-id='mps_graph'])[1]"
            graph_id_sitem = self.locator_finder_by_xpath(graph_id)
            graph_id_sitem.click()
            time.sleep(3)
            self.checking_created_collections(graph_name)
        elif graph_name == "World Graph":
            self.wait_for_ajax()
            graph_id = "(//button[@graph-id='worldCountry'])[1]"
            graph_id_sitem = self.locator_finder_by_xpath(graph_id)
            graph_id_sitem.click()
            time.sleep(3)
            self.checking_created_collections(graph_name)
        elif graph_name == "Social Graph":
            self.wait_for_ajax()
            graph_id = "(//button[@graph-id='social'])[1]"
            graph_id_sitem = self.locator_finder_by_xpath(graph_id)
            graph_id_sitem.click()
            time.sleep(3)
            self.checking_created_collections(graph_name)

        elif graph_name == "City Graph":
            self.wait_for_ajax()
            graph_id = "(//button[@graph-id='routeplanner'])[1]"
            graph_id_sitem = self.locator_finder_by_xpath(graph_id)
            graph_id_sitem.click()
            time.sleep(3)
            self.checking_created_collections(graph_name)

        elif graph_name == "Connected Components Graph":
            self.wait_for_ajax()
            graph_id = "(//button[@graph-id='connectedComponentsGraph'])[1]"
            graph_id_sitem = self.locator_finder_by_xpath(graph_id)
            graph_id_sitem.click()
            time.sleep(3)
            self.checking_created_collections(graph_name)
    
    # pylint: disable=unused-argument
    def create_manual_graph(self, importer, test_data_dir):
        """creating graph manually"""
        self.navbar_goto("collections")
        self.wait_for_ajax()

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
        self.choose_item_from_a_dropdown_menu(from_collection_sitem, "manual_vertices")
        time.sleep(10)

        # selecting to collection from auto suggestion
        to_collection_sitem = self.locator_finder_by_id(to_collection)
        self.choose_item_from_a_dropdown_menu(to_collection_sitem, "manual_vertices")

        time.sleep(10)

        # selecting create graph btn
        create_btn_sitem = self.locator_finder_by_id(create_btn_id)
        create_btn_sitem.click()

        time.sleep(20)

        # selecting newly created graph btn
        knows_graph_sitem = self.locator_finder_by_xpath(knows_graph_id)
        knows_graph_sitem.click()

        time.sleep(3)
        self.webdriver.back()

    def create_satellite_graph(self, importer, test_data_dir):
        """creating satellite graph"""
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
        self.send_key_action("knows_edge")
        self.send_key_action(Keys.ENTER)

        # selecting from collection from auto suggestion
        from_collection_sitem = self.locator_finder_by_id(from_collection)
        from_collection_sitem.click()
        self.send_key_action("persons")
        self.send_key_action(Keys.ENTER)

        time.sleep(1)

        # selecting to collection from auto suggestion
        to_collection_sitem = self.locator_finder_by_id(to_collection)
        to_collection_sitem.click()
        self.send_key_action("persons")
        self.send_key_action(Keys.ENTER)

        time.sleep(1)

        # selecting create graph btn
        create_btn_sitem = self.locator_finder_by_id(create_btn_id)
        create_btn_sitem.click()

        time.sleep(2)

        # importing collections using arangoimport
        print("Importing knows_edge collections \n")
        importer.import_smart_edge_collection("knows_edge", knows_path / "manual_edge.json", ["profiles_smart"])

        print("Importing persons collections \n")
        importer.import_collection("persons", knows_path / "manual_vertices.json")

        # Selecting satellite graph settings to view and delete
        satellite_settings_id = '//*[@id="satellite_graph_tile"]/div/h5'
        satellite_settings_sitem = self.locator_finder_by_xpath(satellite_settings_id)
        satellite_settings_sitem.click()

        time.sleep(5)
        self.webdriver.back()
        time.sleep(1)

#    def delete_sattelite_graph(self):
#        print("\n")
#        print("Smart Graph deleting started \n")
#        satellite_settings_id = "satellite_graph_settings"
#        satellite_settings_sitem = self.locator_finder_by_id(satellite_settings_id)
#        satellite_settings_sitem.click()
#
#        delete_btn_id = "modalButton0"
#        delete_sitem = self.locator_finder_by_id(delete_btn_id)
#        delete_sitem.click()
#
#        delete_check_id = "dropGraphCollections"
#        delete_check_sitem = self.locator_finder_by_id(delete_check_id)
#        delete_check_sitem.click()
#
#        delete_confirm_btn_id = "modal-confirm-delete"
#        delete_confirm_btn_sitem = self.locator_finder_by_id(delete_confirm_btn_id)
#        delete_confirm_btn_sitem.click()
#
#        time.sleep(2)
#        print("Satellite Graph deleted successfully \n")
#        self.webdriver.refresh()

    def create_smart_graph(self, importer, test_data_dir, disjointgraph=False):
        """Adding smart disjoint graph"""
        page_path = test_data_dir / "ui_data" / "graph_page" / "pregel_community"

        create_graph_sitem = self.locator_finder_by_id(self.select_create_graph_id)
        create_graph_sitem.click()

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
        self.scroll(1)
        time.sleep(2)

        # selecting edge definition from auto suggestion
        edge_definition_sitem = self.locator_finder_by_id(edge_definition)
        edge_definition_sitem.click()

        self.send_key_action("relations")
        self.send_key_action(Keys.ENTER)

        # selecting from collection from auto suggestion
        from_collection_sitem = self.locator_finder_by_id(from_collection)
        from_collection_sitem.click()
        self.send_key_action("profiles")
        self.send_key_action(Keys.ENTER)

        time.sleep(1)

        # selecting to collection from auto suggestion
        to_collection_sitem = self.locator_finder_by_id(to_collection)
        to_collection_sitem.click()
        self.send_key_action("profiles")
        self.send_key_action(Keys.ENTER)
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

#        time.sleep(2)
#
#        print("\n")
#        print("Smart Graph deleting started \n")
#        smart_settings_id = "smart_graph_settings"
#        smart_settings_sitem = self.locator_finder_by_id(smart_settings_id)
#        smart_settings_sitem.click()
#
#        delete_btn_id = "modalButton0"
#        delete_btn_sitem = self.locator_finder_by_id(delete_btn_id)
#        delete_btn_sitem.click()
#
#        delete_check_id = "dropGraphCollections"
#        delete_check_sitem = self.locator_finder_by_id(delete_check_id)
#        delete_check_sitem.click()
#
#        delete_confirm_btn_id = "modal-confirm-delete"
#        delete_confirm_btn_sitem = self.locator_finder_by_id(delete_confirm_btn_id)
#        delete_confirm_btn_sitem.click()
#
#        time.sleep(2)
#        print("Smart Graph deleted successfully \n")
#
#        self.webdriver.refresh()

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
                print(collection.name + " collection has been validated")
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
            # self.clear_download_bar()

        # TODO: fullscreen may only work interactive with pynput
        # print("Selecting full screen mode\n")
        # full_screen_sitem = self.locator_finder_by_xpath(self.select_full_screen_btn_id)
        # full_screen_sitem.click()
        # time.sleep(3)
        # print("Return to normal mode\n")
        # self.escape()
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

        self.locator_finder_by_xpath(tip1).click()
        self.scroll(1)
        time.sleep(2)
        restore1 = self.locator_finder_by_xpath(restore1)
        restore1.click()
        time.sleep(1)

        print("Changing relation representation type to Line")
        self.locator_finder_by_select(type1, 0)
        time.sleep(5)

        self.locator_finder_by_xpath(tip2).click()
        self.scroll(1)
        time.sleep(2)
        restore2 = self.locator_finder_by_xpath(restore2)
        restore2.click()
        time.sleep(1)

        print("Changing relation representation type to Curve")
        self.locator_finder_by_select(type3, 2)
        time.sleep(5)

        self.locator_finder_by_xpath(tip4).click()
        self.scroll(1)
        time.sleep(2)
        restore4 = self.locator_finder_by_xpath(restore4)
        restore4.click()
        time.sleep(1)

        print("Changing relation representation type to Dotted")
        self.locator_finder_by_select(type4, 3)
        time.sleep(5)

        self.locator_finder_by_xpath(tip5).click()
        self.scroll(1)
        time.sleep(2)
        restore5 = self.locator_finder_by_xpath(restore5)
        restore5.click()
        time.sleep(1)

        print("Changing relation representation type to Dashed")
        self.locator_finder_by_select(type5, 4)
        time.sleep(5)

        self.locator_finder_by_xpath(tip6).click()
        self.scroll(1)
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
        retry = 0
        while True:
            try:
                self.webdriver.refresh()
                self.wait_for_ajax()
                btn_id = GRAPH_SETS[graph].btn_id
                select_graph_setting_btn_sitem = self.locator_finder_by_id(btn_id)
                self.wait_for_ajax()
                select_graph_setting_btn_sitem.click()
                self.wait_for_ajax()

                time.sleep(0.1)
                # confirm_delete_graph_sitem = self.locator_finder_by_xpath(self.confirm_delete_graph_selector)
                # confirm_delete_graph_sitem.click()
                if self.current_package_version() >= semver.VersionInfo.parse("3.11.0"):
                    delete_btn = "(//button[normalize-space()='Delete'])[1]"
                    delete_btn_sitem = self.locator_finder_by_xpath(delete_btn)
                else:
                    delete_btn = "modalButton0"
                    delete_btn_sitem = self.locator_finder_by_id(delete_btn)
                delete_btn_sitem.click()
                self.wait_for_ajax()

                time.sleep(0.1)
                # delete_with_collection_sitem = self.locator_finder_by_id(self.delete_with_collection_id)
                # delete_with_collection_sitem.click()
                if self.current_package_version() >= semver.VersionInfo.parse("3.11.0"):
                    delete_with_collection = 'dropGraphCollections'
                    delete_with_collection_sitem = self.locator_finder_by_id(delete_with_collection)
                else:
                    delete_with_collection = '//*[@id="dropGraphCollections"]'
                    delete_with_collection_sitem = self.locator_finder_by_xpath(delete_with_collection)

                delete_with_collection_sitem.click()
                self.wait_for_ajax()

                time.sleep(0.1)
                select_really_delete_btn_sitem = self.locator_finder_by_id(self.select_really_delete_btn_id)
                select_really_delete_btn_sitem.click()
                self.wait_for_ajax()
                break
            except TimeoutException as exc:
                retry += 1
                if retry > 10:
                    raise exc
                print("retrying delete " + str(retry))
            except ElementClickInterceptedException as exc:
                retry += 1
                if retry > 10:
                    raise exc
                print("retrying delete " + str(retry))
    
    def deleting_example_graphs(self, graph_name):
        """This method will delete all the example graphs"""
        retry = 0
        while True:
            try:
                print(f"Deleting {graph_name} Graph \n")
                self.navbar_goto("graphs")
                self.webdriver.refresh()
                self.wait_for_ajax()

                if self.current_package_version() <= semver.VersionInfo.parse("3.11.99"):
                    graph_settings_id = ""

                    if graph_name == "Knows Graph":
                        graph_settings_id = "(//span[@id='knows_graph_settings'])[1]"
                    elif graph_name == "Traversal Graph":
                        graph_settings_id = "(//span[@id='traversalGraph_settings'])[1]"
                    elif graph_name == "k Shortest Paths Graph":
                        graph_settings_id = "(//span[@id='kShortestPathsGraph_settings'])[1]"
                    elif graph_name == "Mps Graph":
                        graph_settings_id = "(//span[@id='mps_graph_settings'])[1]"
                    elif graph_name == "World Graph":
                        graph_settings_id = "(//span[@id='worldCountry_settings'])[1]"
                    elif graph_name == "Social Graph":
                        graph_settings_id = "(//span[@id='social_settings'])[1]"
                    elif graph_name == "City Graph":
                        graph_settings_id = "(//span[@id='routeplanner_settings'])[1]"

                    graph_settings_id_sitem = self.locator_finder_by_xpath(graph_settings_id)
                    graph_settings_id_sitem.click()

                    time.sleep(0.1)
                    self.wait_for_ajax()
                    if self.current_package_version() >= semver.VersionInfo.parse("3.11.0"):
                        delete_btn = "(//button[normalize-space()='Delete'])[1]"
                        delete_btn_sitem = self.locator_finder_by_xpath(delete_btn)
                    else:
                        delete_btn = "modalButton0"
                        delete_btn_sitem = self.locator_finder_by_id(delete_btn)

                    delete_btn_sitem.click()

                    time.sleep(0.1)
                    self.wait_for_ajax()
                    try:
                        delete_with_collection = '//*[@id="dropGraphCollections"]'
                        delete_with_collection_sitem = self.locator_finder_by_xpath(delete_with_collection)
                    except Exception as e:
                        print(f"An error occurred: {e} trying different xpath locator \n")
                        # Attempting to use an alternative method
                        try:
                            time.sleep(0.1)
                            self.wait_for_ajax()
                            delete_with_collection = "//*[text()='also drop collections?']"
                            delete_with_collection_sitem = self.locator_finder_by_xpath(delete_with_collection)
                        except Exception as e_alternative:
                            print(f"An error occurred: {e_alternative} using alternative xpath locator \n")
                            # If both attempts fail, raise the original exception
                            raise e

                    delete_with_collection_sitem.click()

                    delete_confirm = "modal-confirm-delete"
                    delete_confirm_sitem = self.locator_finder_by_id(delete_confirm)
                    delete_confirm_sitem.click()
                    time.sleep(1)
                    break
                else:
                    # Find the <a> element with the text "knows_graph"
                    a_element = self.locator_finder_by_xpath(f"//a[text()='{graph_name}']")
                    # Navigate to the parent <td> element
                    td_element = a_element.find_element(By.XPATH, "./ancestor::td")
                    # Find the <button> element within the same row
                    button_element = td_element.find_element(By.XPATH, "./following-sibling::td//button[@type='button']")
                    # Click the button
                    button_element.click()

                    time.sleep(2)
                    self.wait_for_ajax()
                    delete_btn = "(//button[normalize-space()='Delete'])[1]"
                    delete_btn_sitem = self.locator_finder_by_xpath(delete_btn)
                    delete_btn_sitem.click()

                    time.sleep(2)
                    self.wait_for_ajax()
                    delete_with_collection = (
                        "(//label[normalize-space()='Also drop collections'])[1]"
                    )

                    delete_with_collection_sitem = self.locator_finder_by_xpath(
                        delete_with_collection
                    )
                    delete_with_collection_sitem.click()

                    time.sleep(2)
                    self.wait_for_ajax()
                    delete_confirm = "(//button[@type='submit'][normalize-space()='Delete'])[1]"
                    delete_confirm_sitem = self.locator_finder_by_xpath(delete_confirm)
                    delete_confirm_sitem.click()
                    break
            except TimeoutException as exc:
                retry += 1
                if retry > 2:
                    raise exc
                print("retrying delete " + str(retry))
            except ElementClickInterceptedException as exc:
                retry += 1
                if retry > 2:
                    raise exc
                print("retrying delete " + str(retry))


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
    GraphCreateSet("Connected Components", "connectedComponentsGraph_settings",
                   [
                       VCol("components"),
                       ECol("connections")
                   ],
                   None,
                   enterprise=True,
                   min_version='3.8.0'),
    # these are non graph-example tabs; their index doesn't align with their table column:
    GraphCreateSet(
        "Manual Knows",
        "knows_graph_manual_settings",
        [
            VCol("manual_vertices"),
            ECol("manual_edge")
        ],
        GraphPage.create_manual_graph,
    ),
    GraphCreateSet("Satellite Graph",
                   "satellite_graph_settings",
                   [
                       VCol("persons"),
                       ECol("knows_edge")
                   ],
                   GraphPage.create_satellite_graph,
                   enterprise=True,
                   non_cl_min_ver='3.10.0',
                   min_version='3.8.0'),
    GraphCreateSet("Smartgraph",
                   "smart_graph_settings",
                   [
                       VCol("profiles"),
                       ECol("relations")
                   ],
                   GraphPage.create_smart_graph,
                   enterprise=True,
                   non_cl_min_ver='3.10.0',
                   min_version='3.6.0'),
    GraphCreateSet("disjoint Smartgraph",
                   "smart_graph_settings",
                   [
                       VCol("profiles"),
                       ECol("relations")
                   ],
                   GraphPage.create_disjoint_smart_graph,
                   enterprise=True,
                   non_cl_min_ver='3.10.0',
                   min_version='3.6.0'),
]
