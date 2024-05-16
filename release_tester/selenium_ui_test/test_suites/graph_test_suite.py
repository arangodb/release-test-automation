#!/usr/bin/env python3
""" graph testsuite """
import semver
from selenium_ui_test.test_suites.base_selenium_test_suite import BaseSeleniumTestSuite
from test_suites_core.base_test_suite import testcase
from selenium_ui_test.pages.graph_page import GraphPage, GraphExample, get_graph


class GraphTestSuite(BaseSeleniumTestSuite):
    """ graph testsuite """
    @testcase
    def test_graph(self):
        """testing graph page"""
        self.tprint("---------Checking Graphs started--------- \n")
        this_graph = GraphPage(self.webdriver, self.cfg, self.video_start_time)
        assert this_graph.current_user() == "ROOT", "current user is root?"
        assert this_graph.current_database() == "_SYSTEM", "current database is _system?"
        
        graph = GraphPage(self.webdriver, self.cfg, self.video_start_time)  # creating obj for Graph
        
        self.tprint("Example Graphs creation started\n")
        if graph.current_package_version() > semver.VersionInfo.parse("3.11.100"):
            graph.create_example_graph_for_312("Knows Graph")
            graph.create_example_graph_for_312("Traversal Graph")
            graph.create_example_graph_for_312("k Shortest Paths Graph")
            graph.create_example_graph_for_312("Mps Graph")
            graph.create_example_graph_for_312("World Graph")
            graph.create_example_graph_for_312("Social Graph")
            graph.create_example_graph_for_312("City Graph")

            graph.deleting_example_graphs("knows_graph")
            graph.deleting_example_graphs("traversalGraph")
            graph.deleting_example_graphs("kShortestPathsGraph")
            graph.deleting_example_graphs("mps_graph")
            graph.deleting_example_graphs("worldCountry")
            graph.deleting_example_graphs("social")
            graph.deleting_example_graphs("routeplanner")

        else:
            graph.create_example_graph("Knows Graph")
            graph.create_example_graph("Traversal Graph")
            graph.create_example_graph("k Shortest Paths Graph")
            graph.create_example_graph("Mps Graph")
            graph.create_example_graph("World Graph")
            graph.create_example_graph("Social Graph")
            # graph.create_example_graph("City Graph")
            # graph.create_example_graph("Connected Components Graph") # overlapped with a kshortest path collection

            self.tprint("Deleting all example graphs started")
            graph.deleting_example_graphs("Knows Graph")
            graph.deleting_example_graphs("Traversal Graph")
            graph.deleting_example_graphs("k Shortest Paths Graph")
            graph.deleting_example_graphs("Mps Graph")
            graph.deleting_example_graphs("World Graph")
            graph.deleting_example_graphs("Social Graph")
            # graph.deleting_example_graphs("City Graph")
        
        # self.tprint("Manual Graph creation started \n")
        # this_graph.select_graph_page()

        # for graph_id in GraphExample:
        #     # these graphs have overlapping collections, so we create / delete them one by one.
        #     self.tprint(graph_id)
        #     graph = get_graph(graph_id)
        #     if (graph.is_graph_supported(self.cfg.enterprise, self.cfg.semver, self.is_cluster) and
        #         graph_id >= GraphExample.CONNECTED):
        #         self.tprint("Creating '%s' Graph" % graph.get_name())
        #         this_graph.navbar_goto("graphs")
        #         self.webdriver.refresh()
        #         this_graph.create_graph(graph_id, self.importer, self.ui_data_dir)
        #         this_graph.check_required_collections(graph_id)

        #         this_graph.select_graph_page()
        #         this_graph.navbar_goto("graphs")
        #         this_graph.delete_graph(graph_id)
        #     else:
        #         self.tprint("Skipping '%s' Graph not supported by the current setup" % graph.get_name())

        # # if we create more graphs at once, the collection list will not show all collections anymore:
        # self.tprint("Example Graphs creation started\n")
        # for graph_id in GraphExample:
        #     self.tprint(graph_id)
        #     graph = get_graph(graph_id)
        #     if (graph.is_graph_supported(self.cfg.enterprise, self.cfg.semver, self.is_cluster) and
        #         graph_id < GraphExample.CONNECTED):
        #         self.webdriver.refresh()
        #         this_graph.navbar_goto("graphs")
        #         self.webdriver.refresh()
        #         self.tprint("Creating '%s' Graph" % graph.get_name())
        #         this_graph.create_graph(graph_id, self.importer, self.ui_data_dir)
        #         this_graph.check_required_collections(graph_id)

        #         this_graph.select_graph_page()
        #     else:
        #         self.tprint("Skipping '%s' Graph not supported by the current setup" % graph.get_name())


        # self.tprint("Example Graphs creation Completed\n")

        # self.tprint("Sorting all graphs as descending\n")
        # this_graph.select_sort_descend()

        # self.tprint("Selecting Knows Graph for inspection\n")
        # this_graph.inspect_knows_graph()
        # # self.tprint("Selecting Graphs settings menu\n")
        # # this_graph.graph_setting()
        # self.tprint("Deleting created Graphs started\n")
        # for graph_id in GraphExample:
        #     graph = get_graph(graph_id)
        #     if (graph.is_graph_supported(self.cfg.enterprise, self.cfg.semver, self.is_cluster) and
        #         graph_id < GraphExample.CONNECTED):
        #         this_graph.navbar_goto("graphs")
        #         this_graph.delete_graph(graph_id)
        # self.tprint("Deleting created Graphs Completed\n")


        # login.logout_button()
        # del login
        self.tprint("---------Checking Graphs completed--------- \n")
