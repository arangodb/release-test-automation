#!/usr/bin/env python3
""" dashboard testsuite """
import semver
from selenium_ui_test.test_suites.base_selenium_test_suite import BaseSeleniumTestSuite
from test_suites_core.base_test_suite import testcase
from selenium_ui_test.pages.dashboard_page import DashboardPage


class DashboardTestSuite(BaseSeleniumTestSuite):
    """testing dashboard page"""
    @testcase
    def test_dashboard(self):
        """testing dashboard page"""
        self.print("---------Checking Dashboard started--------- \n")
        # login = LoginPage(self.webdriver, self.cfg)
        # login.login('root', self.root_passvoid)
        # creating object for dashboard
        dash = DashboardPage(self.webdriver, self.cfg, self.is_enterprise)
        assert dash.current_user() == "ROOT", "current user is root?"
        assert dash.current_database() == "_SYSTEM", "current database is _system?"
        dash.navbar_goto("cluster" if self.is_cluster else "dashboard")
        dash.check_server_package_name()
        version = dash.current_package_version()
        dash.check_current_username()
        dash.check_current_db()
        dash.check_db_status(self.is_cluster)
        # only 3.6 & 3.7 only support mmfiles... dash.check_db_engine()
        if not self.is_cluster:
            dash.check_db_uptime()
            # TODO: version dependend? cluster?
            dash.check_responsiveness_for_dashboard()
            self.print("\nSwitch to System Resource tab\n")
            dash.check_system_resource()
            self.print("Switch to Metrics tab\n")
            dash.check_system_metrics()

        if self.is_cluster and version >= semver.VersionInfo.parse("3.8.0"):
            self.print("Checking distribution tab \n")
            dash.check_distribution_tab()
            self.print("Checking maintenance tab \n")
            dash.check_maintenance_tab()

        dash.navbar_goto("support")
        self.print("Opening Twitter link \n")
        dash.click_twitter_link()
        self.print("Opening Slack link \n")
        dash.click_slack_link()
        self.print("Opening Stackoverflow link \n")
        dash.click_stackoverflow_link()
        self.print("Opening Google group link \n")
        dash.click_google_group_link()
        # login.logout_button()
        self.print("---------Checking Dashboard Completed--------- \n")
