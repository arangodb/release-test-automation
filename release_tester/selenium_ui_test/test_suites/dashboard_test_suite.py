#!/usr/bin/env python3
""" dashboard testsuite """
import semver
from test_suites_core.base_test_suite import testcase
from selenium_ui_test.test_suites.base_selenium_test_suite import BaseSeleniumTestSuite
from selenium_ui_test.pages.dashboard_page import DashboardPage


class DashboardTestSuite(BaseSeleniumTestSuite):
    """testing dashboard page"""
    @testcase
    def test_dashboard(self):
        """testing dashboard page"""
        self.tprint("---------Checking Dashboard started--------- \n")
        # login = LoginPage(self.webdriver, self.cfg, self.video_start_time)
        # login.login('root', self.root_passvoid)
        # creating object for dashboard
        # pylint: disable=attribute-defined-outside-init
        self.dash = DashboardPage(self.webdriver,
                                  self.cfg,
                                  self.video_start_time,
                                  self.is_enterprise)
        assert self.dash.current_user() == "ROOT", "current user is root?"
        assert self.dash.current_database() == "_SYSTEM", "current database is _system?"
        self.dash.navbar_goto("cluster" if self.is_cluster else "dashboard")
        self.dash.check_server_package_name()
        version = self.dash.current_package_version()
        self.dash.check_current_username()
        self.dash.check_current_db()
        self.dash.check_db_status(self.is_cluster)
        # only 3.6 & 3.7 only support mmfiles... dash.check_db_engine()
        if not self.is_cluster:
            self.dash.check_db_uptime()
            # TODO: version dependend? cluster?
            self.dash.check_responsiveness_for_dashboard()
            self.tprint("\nSwitch to System Resource tab\n")
            self.dash.check_system_resource()
            self.tprint("Switch to Metrics tab\n")
            self.dash.check_system_metrics()

        if self.is_cluster and version >= semver.VersionInfo.parse("3.8.0"):
            self.tprint("Checking distribution tab \n")
            self.dash.check_distribution_tab()
            self.tprint("Checking maintenance tab \n")
            self.dash.check_maintenance_tab()

        self.dash.navbar_goto("support")
        self.tprint("Opening Twitter link \n")
        self.click_twitter_link()
        self.tprint("Opening Slack link \n")
        self.click_slack_link()
        self.tprint("Opening Stackoverflow link \n")
        self.click_stackoverflow_link()
        self.tprint("Opening Google group link \n")
        self.click_google_group_link()
        # login.logout_button()
        self.dash.print_combined_performance_results()
        del self.dash
        self.tprint("---------Checking Dashboard Completed--------- \n")

    def click_twitter_link(self):
        """Clicking on twitter link on dashboard"""
        click_twitter_link_id_sitem = self.dash.locator_finder_by_xpath(
            self.dash.get_twitter_link_id()
        )

        def check_title(title):
            # List of valid expected titles
            expected_titles = [
                "ArangoDB (@arangodb) / X",
                "Profile / X"
            ]

            # Check if the actual title is in the list of expected titles
            self.ui_assert((title in expected_titles),
                    f"Expected page title to be one of {expected_titles} but got {title}")
        self.dash.switch_tab_check(click_twitter_link_id_sitem, check_title)

    def click_slack_link(self):
        """Clicking on twitter link on dashboard"""
        click_slack_link_id_sitem = self.dash.locator_finder_by_xpath(self.dash.get_slack_link_id)
        def check_title(title):
            expected_title = "Join ArangoDB Community on Slack!"
            self.ui_assert(
                (title in expected_title),
                f"Expected page title {expected_title} but got {title}")
        self.dash.switch_tab_check(click_slack_link_id_sitem, check_title)

    def click_stackoverflow_link(self):
        """Clicking on stack overflow link on dashboard"""
        click_stackoverflow_link_id_sitem = self.dash.locator_finder_by_xpath(
            self.dash.get_stackoverflow_link_id()
        )
        def check_title(title):
            expected_title = "Newest 'arangodb' Questions - Stack Overflow"
            self.ui_assert(
                (title in expected_title),
                f"Expected page title {expected_title} but got {title}")
        self.dash.switch_tab_check(click_stackoverflow_link_id_sitem, check_title)

    def click_google_group_link(self):
        """Clicking on Google group link on dashboard"""

        click_google_group_link_id_sitem = self.dash.locator_finder_by_xpath(
            self.dash.get_google_group_link_id()
        )
        def check_title(title):
            expected_title = "ArangoDB - Google Groups"
            self.ui_assert((title in expected_title),
                    f"Expected page title {expected_title} but got {title}")
        self.dash.switch_tab_check(click_google_group_link_id_sitem, check_title)
