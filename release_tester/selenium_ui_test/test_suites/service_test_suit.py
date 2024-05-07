#!/usr/bin/env python3
""" service page testsuite """
from selenium_ui_test.pages.service_page import ServicePage
from selenium_ui_test.test_suites.base_selenium_test_suite import BaseSeleniumTestSuite
from test_suites_core.base_test_suite import testcase
import traceback


class ServiceTestSuite(BaseSeleniumTestSuite):
    """service page testsuite"""

    @testcase
    def test_service(self):
        """service page test"""
        # pylint: disable=too-many-statements
        print("---------Service Page Test Begin--------- \n")
        service = ServicePage(self.webdriver, self.cfg)
        self.exception = False
        self.error = None
        assert service.current_user() == "ROOT", "current user is root?"
        assert service.current_database() == "_SYSTEM", "current database is _system?"

        try:
            service.select_service_page()
            service.select_add_service_button()
            service.service_search_option("demo")
            service.service_search_option("tab")
            service.service_search_option("grafana")
            service.service_category_option()
            service.select_category_option_from_list("connector")
            service.select_category_option_from_list("service")
            service.select_category_option_from_list("geo")
            service.select_category_option_from_list("demo")
            service.select_category_option_from_list("graphql")
            service.select_category_option_from_list("prometheus")
            service.select_category_option_from_list("monitoring")
            service.select_category_option_search_filter("geo")
            service.select_category_option_search_filter("demo")
            service.select_category_option_search_filter("connector")
            # service.checking_demo_geo_s2_service_github()
            service.install_demo_geo_s2_service("/geo", self.ui_data_dir)
            # service.check_demo_geo_s2_service_api()
            # service.inspect_foxx_leaflet_iframe()
            service.install_demo_graph_hql_service("/graphql")
            # service.replace_service()

        except BaseException:
            print("x" * 45, "\nINFO: Error Occurred! Force Deletion Started\n", "x" * 45)
            self.exception = True  # mark the exception as true
            self.error = traceback.format_exc()

        finally:
            service.delete_service("/geo")
            service.delete_service("/graphql")
            del service
            print("---------Service Page Test Completed--------- \n")
            if self.exception:
                raise Exception(self.error)
