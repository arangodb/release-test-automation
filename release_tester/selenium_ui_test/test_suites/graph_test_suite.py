from selenium_ui_test.test_suites.base_test_suite import BaseTestSuite, testcase
from selenium_ui_test.pages.graph_page import GraphPage, GraphExample, get_graph_name

class GraphTestSuite(BaseTestSuite):
    @testcase
    def test_graph(self):
        """testing graph page"""
        print("---------Checking Graphs started--------- \n")
        # login = LoginPage(self.webdriver)
        # login.login('root', self.root_passvoid)

        # creating multiple graph obj
        # print('z'*80)
        this_graph = GraphPage(self.webdriver)
        print("Manual Graph creation started \n")

        this_graph.select_graph_page()
        # print("Creating '%s' Graph"%get_graph_name(GraphExample.MANUAL_KNOWS))
        # this_graph.create_graph(GraphExample.MANUAL_KNOWS, self.importer, self.test_data_dir)
        # print("Manual Graph creation completed \n")
        # this_graph.delete_graph(GraphExample.MANUAL_KNOWS)
        # self.webdriver.refresh()
        #
        # if cfg.enterprise:
        #    print("Adding Satellite Graph started \n")
        #    this_graph.create_graph(GraphExample.MANUAL_SATELITE_GRAPH, self.importer, self.test_data_dir)
        #    print("Adding Satellite Graph started \n")
        #
        #    print("Adding Smart Graph started \n")
        #    this_graph.create_graph(GraphExample.MANUAL_SMART_GRAHP, self.importer, self.test_data_dir)
        #    print("Adding Smart Graph completed \n")
        #
        #    print("Adding Disjoint Smart Graph started \n")
        #    this_graph.create_graph(GraphExample.MANUAL_DISJOINT_SMART_GRAHP, self.importer, self.test_data_dir)
        #    print("Adding Disjoint Smart Graph completed \n")

        print("Example Graphs creation started\n")
        for graph in GraphExample:
            #graph = GraphExample.MANUAL_KNOWS
            #this_graph.navbar_goto("graphs")
            print(graph)
            print("Creating '%s' Graph" % get_graph_name(graph))
            this_graph.create_graph(graph, self.importer, self.test_data_dir)
            this_graph.check_required_collections(graph)

            this_graph.select_graph_page()

        print("Example Graphs creation Completed\n")

        print("Sorting all graphs as descending\n")
        this_graph.select_sort_descend()

        print("Selecting Knows Graph for inspection\n")
        this_graph.inspect_knows_graph()
        # print("Selecting Graphs settings menu\n")
        # this_graph.graph_setting()
        print("Deleting created Graphs started\n")
        for graph in GraphExample:
            # if graph == GraphExample.MANUAL_KNOWS:
            #    break
            this_graph.navbar_goto("graphs")
            this_graph.delete_graph(graph)
        print("Deleting created Graphs Completed\n")
        # login.logout_button()
        # del login
        print("---------Checking Graphs completed--------- \n")
