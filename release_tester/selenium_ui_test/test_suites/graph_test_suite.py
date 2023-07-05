#!/usr/bin/env python3
""" graph testsuite """

from selenium_ui_test.test_suites.base_selenium_test_suite import BaseSeleniumTestSuite
from test_suites_core.base_test_suite import testcase
from selenium_ui_test.pages.graph_page import GraphPage, GraphExample, get_graph


class GraphTestSuite(BaseSeleniumTestSuite):
    """ graph testsuite """
    @testcase
    def test_graph(self):
        """testing graph page"""
        print("---------Checking Graphs started--------- \n")
        this_graph = GraphPage(self.webdriver, self.cfg)
        assert this_graph.current_user() == "ROOT", "current user is root?"
        assert this_graph.current_database() == "_SYSTEM", "current database is _system?"
        print("Manual Graph creation started \n")

        this_graph.select_graph_page()

        for graph_id in GraphExample:
            # these graphs have overlapping collections, so we create / delete them one by one.
            print(graph_id)
            graph = get_graph(graph_id)
            if (graph.is_graph_supported(self.cfg.enterprise, self.cfg.semver, self.is_cluster) and
                graph_id >= GraphExample.CONNECTED):
                print("Creating '%s' Graph" % graph.get_name())
                this_graph.navbar_goto("graphs")
                self.webdriver.refresh()
                this_graph.create_graph(graph_id, self.importer, self.ui_data_dir)
                this_graph.check_required_collections(graph_id)

                this_graph.select_graph_page()
                this_graph.navbar_goto("graphs")
                this_graph.delete_graph(graph_id)
            else:
                print("Skipping '%s' Graph not supported by the current setup" % graph.get_name())

        # if we create more graphs at once, the collection list will not show all collections anymore:
        print("Example Graphs creation started\n")
        for graph_id in GraphExample:
            print(graph_id)
            graph = get_graph(graph_id)
            if (graph.is_graph_supported(self.cfg.enterprise, self.cfg.semver, self.is_cluster) and
                graph_id < GraphExample.CONNECTED):
                self.webdriver.refresh()
                this_graph.navbar_goto("graphs")
                self.webdriver.refresh()
                print("Creating '%s' Graph" % graph.get_name())
                this_graph.create_graph(graph_id, self.importer, self.ui_data_dir)
                this_graph.check_required_collections(graph_id)

                this_graph.select_graph_page()
            else:
                print("Skipping '%s' Graph not supported by the current setup" % graph.get_name())


        print("Example Graphs creation Completed\n")

        print("Sorting all graphs as descending\n")
        this_graph.select_sort_descend()

        print("Selecting Knows Graph for inspection\n")
        this_graph.inspect_knows_graph()
        # print("Selecting Graphs settings menu\n")
        # this_graph.graph_setting()
        print("Deleting created Graphs started\n")
        for graph_id in GraphExample:
            graph = get_graph(graph_id)
            if (graph.is_graph_supported(self.cfg.enterprise, self.cfg.semver, self.is_cluster) and
                graph_id < GraphExample.CONNECTED):
                this_graph.navbar_goto("graphs")
                this_graph.delete_graph(graph_id)
        print("Deleting created Graphs Completed\n")


        # login.logout_button()
        # del login
        print("---------Checking Graphs completed--------- \n")
