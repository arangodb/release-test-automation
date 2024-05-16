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
        
        self.tprint("Checking saved query feature \n")
        if query_page.current_package_version() > semver.VersionInfo.parse("3.10.99"):
            query_page.saved_query_check()
        
        if query_page.current_package_version() >= semver.VersionInfo.parse("3.10.0"):
            if query_page.current_package_version() > semver.VersionInfo.parse("3.11.99"):
                # TODO for 3.12.x
                self.tprint("skipped")
        else:
            self.tprint("Importing IMDB collections \n")
            query_page.import_collections(self.restore, self.ui_data_dir, self.is_cluster)

            self.tprint("Selecting Query page for basic CRUD operation \n")
            query_page.selecting_query_page()

            self.tprint("Executing insert query \n")
            query_page.execute_insert_query()

            self.tprint("Profiling current query \n")
            query_page.profile_query()
            self.tprint("Explaining current query \n")
            query_page.explain_query()
            self.tprint("Debug packaged downloading for the current query \n")
            query_page.debug_package_download()
            self.tprint("Removing all query results \n")
            query_page.remove_query_result()
            self.tprint("Importing IMDB collections \n")
            query_page.import_collections(self.restore, self.ui_data_dir, self.is_cluster)

            self.tprint("Selecting Query page for basic CRUD operation \n")
            query_page.selecting_query_page()

            self.tprint("Executing insert query \n")
            query_page.execute_insert_query()

            self.tprint("Profiling current query \n")
            query_page.profile_query()
            self.tprint("Explaining current query \n")
            query_page.explain_query()
            self.tprint("Debug packaged downloading for the current query \n")
            query_page.debug_package_download()
            self.tprint("Removing all query results \n")
            query_page.remove_query_result()

            # TODO: self.tprint("Executing spot light functionality \n")
            # query_page.spot_light_function('COUNT')  # can be used for search different keyword

            self.tprint("Executing read query\n")
            query_page.execute_read_query()

            self.tprint("Updating documents\n")
            query_page.update_documents()
            self.tprint("Executing query with bind parameters \n")
            query_page.bind_parameters_query()

            self.tprint("Executing example graph query \n")
            graph = GraphExample.WORLD
            query_page.navbar_goto("graphs")
            self.webdriver.refresh()
            self.tprint("Creating '%s' Graph" % get_graph(graph).get_name())
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
            self.tprint("Creating '%s' Graph" % get_graph(graph).get_name())
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
            self.tprint("Creating '%s' Graph" % get_graph(graph).get_name())
            graph_page.create_graph(graph, self.importer, self.ui_data_dir)
            graph_page.check_required_collections(graph)
            self.tprint("Executing City Graph query \n")
            query_page.city_graph()
            query_page.navbar_goto("graphs")
            self.webdriver.refresh()
            graph_page.delete_graph(graph)

            graph_page.navbar_goto("queries")
            self.webdriver.refresh()

            # self.tprint("Importing new queries \n") # untill the fix arrive
            # query_page.import_queries(str(self.ui_data_dir / "ui_data" / "query_page" / "imported_query.json"))
            self.tprint("Saving Current query as custom query\n")
            query_page.custom_query()
            self.tprint("Changing the number of results from 1000 to 100\n")
            query_page.number_of_results()

            self.tprint("Deleting collections begins \n")
            query_page.delete_all_collections()
            self.tprint("Deleting collections completed \n")

        del query_page
        self.tprint("---------Checking Query completed--------- \n")
