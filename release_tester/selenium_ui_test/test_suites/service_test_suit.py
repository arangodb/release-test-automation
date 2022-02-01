#!/usr/bin/env python3
""" service page testsuite """
from selenium_ui_test.pages.service_page import ServicePage
from selenium_ui_test.test_suites.base_selenium_test_suite import BaseSeleniumTestSuite
from selenium_ui_test.test_suites.base_test_suite import testcase

class ServiceTestSuite(BaseSeleniumTestSuite):
    """ analyzer page testsuite """
    @testcase
    def test_service(self):
        """ service page test """
        # pylint: disable=too-many-statements
        print("---------Service Page Test Begin--------- \n")
        service = ServicePage(self.webdriver)

        assert service.current_user() == "ROOT", "current user is root?"
        assert service.current_database() == "_SYSTEM", "current database is _system?"

        service.select_service_page()
        service.select_add_service_button()
        service.service_search_option('demo')
        service.service_search_option('tab')
        service.service_search_option('grafana')
        service.service_category_option()
        service.select_category_option_from_list('connector')
        service.select_category_option_from_list('service')
        service.select_category_option_from_list('geo')
        service.select_category_option_from_list('demo')
        service.select_category_option_from_list('graphql')
        service.select_category_option_from_list('prometheus')
        service.select_category_option_from_list('monitoring')

        service.select_category_option_search_filter('geo')
        service.select_category_option_search_filter('demo')
        service.select_category_option_search_filter('connector')

        service.setup_demo_geo_s2_service()
        # need to provide service mount path and collection dir path
        service.install_demo_geo_s2_service('/myservice', self.test_data_dir)
        service.check_demo_geo_s2_service_api()
        service.inspect_foxx_leaflet_iframe()

        service.delete_service('demo_geo_s2')

        del service

        print("---------Service Page Test Completed--------- \n")