import time

from baseSelenium import BaseSelenium


class GraphPage(BaseSelenium):

    def __init__(self, driver):
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

        self.select_graph_settings_menu = "settingsMenu"
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

    # selecting Graph tab
    def select_graph_page(self):
        self.select_graph_page_id = \
            BaseSelenium.locator_finder_by_id(self, self.select_graph_page_id)
        self.select_graph_page_id.click()

    # selecting collection tab and search for required collections
    def check_required_collection(self, graph):
        self.select_collection_page_id = \
            BaseSelenium.locator_finder_by_id(self, self.select_collection_page_id)
        self.select_collection_page_id.click()

        if graph == 1:
            s1 = self.select_search_id
            s2 = self.select_search_id

            s1 = BaseSelenium.locator_finder_by_id(self, s1)
            s1.click()
            s1.clear()
            s1.send_keys("knows")
            time.sleep(3)
            self.driver.refresh()
            s2 = BaseSelenium.locator_finder_by_id(self, s2)
            s2.click()
            s2.clear()
            s2.send_keys("persons")
            time.sleep(3)

        elif graph == 2:
            s1 = self.select_search_id
            s2 = self.select_search_id

            s1 = BaseSelenium.locator_finder_by_id(self, s1)
            s1.click()
            s1.clear()
            s1.send_keys("circles")
            time.sleep(3)
            self.driver.refresh()
            s2 = BaseSelenium.locator_finder_by_id(self, s2)
            s2.click()
            s2.clear()
            s2.send_keys("edges")
            time.sleep(3)

        elif graph == 3:
            s1 = self.select_search_id
            s2 = self.select_search_id

            s1 = BaseSelenium.locator_finder_by_id(self, s1)
            s1.click()
            s1.clear()
            s1.send_keys("connections")
            time.sleep(3)
            self.driver.refresh()
            s2 = BaseSelenium.locator_finder_by_id(self, s2)
            s2.click()
            s2.clear()
            s2.send_keys("places")
            time.sleep(3)

        elif graph == 4:
            s1 = self.select_search_id
            s2 = self.select_search_id

            s1 = BaseSelenium.locator_finder_by_id(self, s1)
            s1.click()
            s1.clear()
            s1.send_keys("mps_edges")
            time.sleep(3)
            self.driver.refresh()
            s2 = BaseSelenium.locator_finder_by_id(self, s2)
            s2.click()
            s2.clear()
            s2.send_keys("mps_verts")
            time.sleep(3)

        elif graph == 5:
            s1 = self.select_search_id
            s2 = self.select_search_id

            s1 = BaseSelenium.locator_finder_by_id(self, s1)
            s1.click()
            s1.clear()
            s1.send_keys("worldEdges")
            time.sleep(3)
            self.driver.refresh()
            s2 = BaseSelenium.locator_finder_by_id(self, s2)
            s2.click()
            s2.clear()
            s2.send_keys("worldvertices")
            time.sleep(3)

        elif graph == 6:
            s1 = self.select_search_id
            s2 = self.select_search_id
            s3 = self.select_search_id

            s1 = BaseSelenium.locator_finder_by_id(self, s1)
            s1.click()
            s1.clear()
            s1.send_keys("male")
            time.sleep(3)
            self.driver.refresh()
            s2 = BaseSelenium.locator_finder_by_id(self, s2)
            s2.click()
            s2.clear()
            s2.send_keys("female")
            time.sleep(3)
            self.driver.refresh()
            s3 = BaseSelenium.locator_finder_by_id(self, s3)
            s3.click()
            s3.clear()
            s3.send_keys("relation")
            time.sleep(3)

        elif graph == 7:
            s1 = self.select_search_id
            s2 = self.select_search_id
            s3 = self.select_search_id
            s4 = self.select_search_id
            s5 = self.select_search_id

            s1 = BaseSelenium.locator_finder_by_id(self, s1)
            s1.click()
            s1.clear()
            s1.send_keys("frenchCity")
            time.sleep(3)
            self.driver.refresh()
            s2 = BaseSelenium.locator_finder_by_id(self, s2)
            s2.click()
            s2.clear()
            s2.send_keys("frenchHighway")
            time.sleep(3)
            self.driver.refresh()
            s3 = BaseSelenium.locator_finder_by_id(self, s3)
            s3.click()
            s3.clear()
            s3.send_keys("germanCity")
            time.sleep(3)
            self.driver.refresh()
            s4 = BaseSelenium.locator_finder_by_id(self, s4)
            s4.click()
            s4.clear()
            s4.send_keys("germanHighway")
            time.sleep(3)
            self.driver.refresh()
            s5 = BaseSelenium.locator_finder_by_id(self, s5)
            s5.click()
            s5.clear()
            s5.send_keys("internationalHighway")
            time.sleep(3)

    # Creating new example graphs
    def select_create_graph(self, graph):
        self.select_create_graph_id = \
            BaseSelenium.locator_finder_by_id(self, self.select_create_graph_id)
        self.select_create_graph_id.click()
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

    # Checking required collections creation for the particular example graph.
    def checking_collection_creation(self, graph):
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

    # Sorting all graphs to descending and then ascending again
    def select_sort_descend(self):
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

    # Selecting Knows Graph for checking graph functionality
    def inspect_knows_graph(self):
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
        print("Selecting full screen mode\n")
        full_screen = self.select_full_screen_btn_id
        full_screen = BaseSelenium.locator_finder_by_xpath(self, full_screen)
        full_screen.click()
        time.sleep(3)
        print("Return to normal mode\n")
        super().escape()
        time.sleep(2)

    # Checking all the options inside graph settings
    def graph_setting(self):
        select_graph_settings_menu = BaseSelenium.locator_finder_by_id(self, self.select_graph_settings_menu)
        select_graph_settings_menu.click()
        print("Selecting different layouts for the graph\n")

        print("Selecting No Overlapping layout\n")
        layout1 = self.select_graph_layout_option_id
        BaseSelenium.locator_finder_by_select(self, layout1, 1)
        time.sleep(3)
        print("Selecting Fruchtermann layout\n")
        layout2 = self.select_graph_layout_option_id
        BaseSelenium.locator_finder_by_select(self, layout2, 2)
        time.sleep(3)

        print("Selecting WebGL experimental renderer\n")
        renderer = self.select_renderer_id
        BaseSelenium.locator_finder_by_select(self, renderer, 1)
        time.sleep(3)

        print("Changing Search Depth\n")
        depth = self.select_depth_id
        depth1 = BaseSelenium.locator_finder_by_xpath(self, depth)
        depth1.clear()
        depth2 = BaseSelenium.locator_finder_by_xpath(self, depth)
        depth2.send_keys("3")
        time.sleep(3)

        print("Changing Search Limit\n")
        limit = self.select_limit_id
        limit1 = BaseSelenium.locator_finder_by_xpath(self, limit)
        limit1.clear()
        limit2 = BaseSelenium.locator_finder_by_xpath(self, limit)
        limit2.send_keys("20")
        time.sleep(3)

        print("Adding collection name with nodes\n")
        BaseSelenium.locator_finder_by_select(self, self.add_collection_name_id, 0)
        time.sleep(3)

        print("Selecting color by collection\n")
        BaseSelenium.locator_finder_by_select(self, self.select_color_collection_id, 0)
        time.sleep(3)

        print("Selecting size by edges\n")
        BaseSelenium.locator_finder_by_select(self, self.select_size_by_edges_id, 0)
        time.sleep(3)

        print("Adding edge name to the node\n")
        BaseSelenium.locator_finder_by_select(self, self.select_add_edge_col_name_id, 0)
        time.sleep(3)

        print("Adding Color by edge collection\n")
        BaseSelenium.locator_finder_by_select(self, self.select_add_edge_col_name_id, 1)
        time.sleep(3)

        print("Selecting different representation of relation between nodes\n")
        print("Maximizing the window \n")
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

        print("Changing relation representation type to Line\n")
        BaseSelenium.locator_finder_by_select(self, type1, 0)
        time.sleep(5)

        self.driver.find_element_by_xpath(tip2).click()
        super().scroll(1)
        time.sleep(2)
        restore2 = BaseSelenium.locator_finder_by_xpath(self, restore2)
        restore2.click()

        print("Changing relation representation type to Curve\n")
        BaseSelenium.locator_finder_by_select(self, type3, 2)
        time.sleep(5)

        self.driver.find_element_by_xpath(tip4).click()
        super().scroll(1)
        time.sleep(2)
        restore4 = BaseSelenium.locator_finder_by_xpath(self, restore4)
        restore4.click()

        print("Changing relation representation type to Dotted\n")
        BaseSelenium.locator_finder_by_select(self, type4, 3)
        time.sleep(5)

        self.driver.find_element_by_xpath(tip5).click()
        super().scroll(1)
        time.sleep(2)
        restore5 = BaseSelenium.locator_finder_by_xpath(self, restore5)
        restore5.click()

        print("Changing relation representation type to Dashed\n")
        BaseSelenium.locator_finder_by_select(self, type5, 4)
        time.sleep(5)

        self.driver.find_element_by_xpath(tip6).click()
        super().scroll(1)
        time.sleep(2)
        restore6 = BaseSelenium.locator_finder_by_xpath(self, restore6)
        restore6.click()

        print("Changing relation representation type to Tapered\n")
        BaseSelenium.locator_finder_by_select(self, type6, 5)
        time.sleep(5)

        print("Going Back to original window size \n")
        self.driver.set_window_size(1000, 1000)  # custom window size
        self.driver.back()
        time.sleep(3)

    # Deleting created graphs
    def delete_graph(self, graph):

        if graph == 1:
            self.select_knows_graphs_setting_btn_id = \
                BaseSelenium.locator_finder_by_id(self, self.select_knows_graphs_setting_btn_id)
            self.select_knows_graphs_setting_btn_id.click()
            print("Deleting knows Graph\n")
        elif graph == 2:
            self.select_traversal_graphs_setting_btn_id = \
                BaseSelenium.locator_finder_by_id(self, self.select_traversal_graphs_setting_btn_id)
            self.select_traversal_graphs_setting_btn_id.click()
            print("Deleting Traversal Graph\n")
        elif graph == 3:
            self.select_k_shortest_path_graphs_setting_btn_id = \
                BaseSelenium.locator_finder_by_id(self, self.select_k_shortest_path_graphs_setting_btn_id)
            self.select_k_shortest_path_graphs_setting_btn_id.click()
            print("Deleting K Shortest Path Graph\n")
        elif graph == 4:
            self.select_maps_graphs_setting_btn_id = \
                BaseSelenium.locator_finder_by_id(self, self.select_maps_graphs_setting_btn_id)
            self.select_maps_graphs_setting_btn_id.click()
            print("Deleting Mps Graph\n")
        elif graph == 5:
            self.select_world_graphs_setting_btn_id = \
                BaseSelenium.locator_finder_by_id(self, self.select_world_graphs_setting_btn_id)
            self.select_world_graphs_setting_btn_id.click()
            print("Deleting World Graph\n")
        elif graph == 6:
            self.select_social_graphs_setting_btn_id = \
                BaseSelenium.locator_finder_by_id(self, self.select_social_graphs_setting_btn_id)
            self.select_social_graphs_setting_btn_id.click()
            print("Deleting Social Graph\n")
        elif graph == 7:
            self.select_route_planner_graphs_setting_btn_id = \
                BaseSelenium.locator_finder_by_id(self, self.select_route_planner_graphs_setting_btn_id)
            self.select_route_planner_graphs_setting_btn_id.click()
            print("Deleting City Graph\n")
        elif graph == 8:
            self.select_connected_graphs_setting_btn_id = \
                BaseSelenium.locator_finder_by_id(self, self.select_connected_graphs_setting_btn_id)
            self.select_connected_graphs_setting_btn_id.click()
            print("Deleting Connected Component Graph\n")
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
