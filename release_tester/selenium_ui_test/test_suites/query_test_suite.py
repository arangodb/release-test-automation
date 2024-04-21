#!/usr/bin/env python3
""" query testsuite """
import semver
from selenium_ui_test.test_suites.base_selenium_test_suite import BaseSeleniumTestSuite
from test_suites_core.base_test_suite import testcase
from selenium_ui_test.pages.query_page import QueryPage
from selenium_ui_test.pages.graph_page import GraphPage
from selenium_ui_test.pages.graph_page import GraphExample, get_graph


class QueryTestSuite(BaseSeleniumTestSuite):
    """ query testsuite """
    @testcase
    def test_query(self):
        """testing query page"""
        # pylint: disable=too-many-statements
        query_page = QueryPage(self.webdriver, self.cfg)
        graph_page = GraphPage(self.webdriver, self.cfg)

        assert query_page.current_user() == "ROOT", "current user is root?"
        assert query_page.current_database() == "_SYSTEM", "current database is _system?"
        
        print("Checking saved query feature \n")
        if query_page.current_package_version() > semver.VersionInfo.parse("3.10.99"):
            query_page.saved_query_check()
        
        if query_page.current_package_version() >= semver.VersionInfo.parse("3.10.0"):
            if query_page.current_package_version() > semver.VersionInfo.parse("3.11.99"):
                # TODO for 3.12.x
                print("skipped")
        else:
            print("Importing IMDB collections \n")
            query_page.import_collections(self.restore, self.ui_data_dir, self.is_cluster)

            print("Selecting Query page for basic CRUD operation \n")
            query_page.selecting_query_page()

            print("Executing insert query \n")
            query_page.execute_insert_query()

            print("Profiling current query \n")
            query_page.profile_query()
            print("Explaining current query \n")
            query_page.explain_query()
            print("Debug packaged downloading for the current query \n")
            query_page.debug_package_download()
            print("Removing all query results \n")
            query_page.remove_query_result()
            print("Importing IMDB collections \n")
            query_page.import_collections(self.restore, self.ui_data_dir, self.is_cluster)

            print("Selecting Query page for basic CRUD operation \n")
            query_page.selecting_query_page()

            print("Executing insert query \n")
            query_page.execute_insert_query()

            print("Profiling current query \n")
            query_page.profile_query()
            print("Explaining current query \n")
            query_page.explain_query()
            print("Debug packaged downloading for the current query \n")
            query_page.debug_package_download()
            print("Removing all query results \n")
            query_page.remove_query_result()

            # TODO: print("Executing spot light functionality \n")
            # query_page.spot_light_function('COUNT')  # can be used for search different keyword

            print("Executing read query\n")
            query_page.execute_read_query()

            print("Updating documents\n")
            query_page.update_documents()
            print("Executing query with bind parameters \n")
            query_page.bind_parameters_query()

            print("Executing example graph query \n")
            graph = GraphExample.WORLD
            query_page.navbar_goto("graphs")
            self.webdriver.refresh()
            print("Creating '%s' Graph" % get_graph(graph).get_name())
            graph_page.create_graph(graph, self.importer, self.ui_data_dir)
            graph_page.check_required_collections(graph)
            query_page.world_country_graph_query()
            query_page.navbar_goto("graphs")
            self.webdriver.refresh()
            graph_page.delete_graph(graph)
            self.webdriver.refresh()

            graph = GraphExample.K_SHORTEST_PATH
            query_page.navbar_goto("graphs")
            self.webdriver.refresh()
            print("Creating '%s' Graph" % get_graph(graph).get_name())
            graph_page.create_graph(graph, self.importer, self.ui_data_dir)
            graph_page.check_required_collections(graph)
            query_page.k_shortest_paths_graph_query()
            query_page.navbar_goto("graphs")
            self.webdriver.refresh()
            graph_page.delete_graph(graph)
            self.webdriver.refresh()

            graph = GraphExample.CITY
            graph_page.navbar_goto("graphs")
            self.webdriver.refresh()
            print("Creating '%s' Graph" % get_graph(graph).get_name())
            graph_page.create_graph(graph, self.importer, self.ui_data_dir)
            graph_page.check_required_collections(graph)
            print("Executing City Graph query \n")
            query_page.city_graph()
            query_page.navbar_goto("graphs")
            self.webdriver.refresh()
            graph_page.delete_graph(graph)

            graph_page.navbar_goto("queries")
            self.webdriver.refresh()

            # print("Importing new queries \n") # untill the fix arrive
            # query_page.import_queries(str(self.ui_data_dir / "ui_data" / "query_page" / "imported_query.json"))
            print("Saving Current query as custom query\n")
            query_page.custom_query()
            print("Changing the number of results from 1000 to 100\n")
            query_page.number_of_results()

            print("Deleting collections begins \n")
            query_page.delete_all_collections()
            print("Deleting collections completed \n")

        del query_page
        print("---------Checking Query completed--------- \n")
