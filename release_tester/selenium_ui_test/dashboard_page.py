#!/usr/bin/env python
"""
aardvark dashboard page object
"""

import time

from selenium.common.exceptions import TimeoutException

from selenium_ui_test.base_selenium import BaseSelenium

# can't circumvent long lines.. nAttr nLines
# pylint: disable=C0301 disable=R0902 disable=R0915

class DashboardPage(BaseSelenium):
    """Class for Dashboard page"""

    def __init__(self, driver):
        """ dashboardPage class initialization"""
        super().__init__()
        self.driver = driver
        self.check_server_package_name_id = "enterpriseLabel"
        self.check_current_package_version_id = "currentVersion"
        self.check_current_username_id = "//li[@id='userBar']//span[@class='toggle']"
        self.check_current_db_id = "//li[@id='dbStatus']/a[@class='state']"
        self.check_db_status_id = "//li[@id='healthStatus']/a[.='GOOD']"
        self.check_cluster_status_id = '//*[@id="healthStatus"]/a[2]'
        self.check_db_engine_id = "nodeattribute-Engine"
        self.check_db_uptime_id = "/html//div[@id='nodeattribute-Uptime']"
        self.check_system_resource_id = "system-statistics"
        self.check_system_metrics_id = "metrics-statistics"
        self.select_reload_btn_id = "reloadMetrics"
        self.metrics_download_id = "downloadAs"
        self.click_twitter_link_id = "//*[@id='navigationBar']/div[2]/p[1]/a"
        self.click_slack_link_id = "//*[@id='navigationBar']/div[2]/p[2]/a"
        self.click_stackoverflow_link_id = "//*[@id='navigationBar']/div[2]/p[3]/a"
        self.click_google_group_link_id = "//*[@id='navigationBar']/div[2]/p[4]/a"

    def check_server_package_name(self):
        """checking server package version name"""
        self.check_server_package_name_id = \
            BaseSelenium.locator_finder_by_text_id(self, self.check_server_package_name_id)
        print("Server Package: ", self.check_server_package_name_id)
        time.sleep(1)

    def check_current_package_version(self):
        """checking current package version from the dashboard"""
        super().current_package_version()

    def check_current_username(self):
        """checking current username from the dashboard"""
        self.check_current_username_id = \
            BaseSelenium.locator_finder_by_text_xpath(self, self.check_current_username_id)
        print("Current User: ", self.check_current_username_id)
        time.sleep(1)

    def check_current_db(self):
        """checking current database name from the dashboard"""
        self.check_current_db_id = \
            BaseSelenium.locator_finder_by_text_xpath(self, self.check_current_db_id)
        print("Current DB: ", self.check_current_db_id)
        time.sleep(1)

    def check_db_status(self):
        """checking current database status from the dashboard"""
        try:
            self.check_db_status_id = \
                BaseSelenium.locator_finder_by_text_xpath(self, self.check_db_status_id)
            print("Current Status: ", self.check_db_status_id)
            time.sleep(1)
        except TimeoutException:
            node = self.check_cluster_status_id
            node = \
                BaseSelenium.locator_finder_by_text_xpath(self, node)
            print("Cluster Health: ", node)
            time.sleep(1)

    def check_db_engine(self):
        """checking current database status from the dashboard"""
        self.check_db_engine_id = \
            BaseSelenium.locator_finder_by_text_id(self, self.check_db_engine_id)
        print("Current Engine: ", self.check_db_engine_id)
        time.sleep(1)

    def check_db_uptime(self):
        """checking current database uptime status from the dashboard"""
        self.check_db_uptime_id = \
            BaseSelenium.locator_finder_by_text_xpath(self, self.check_db_uptime_id)
        print("DB Uptime: ", self.check_db_uptime_id)
        time.sleep(1)

    def check_responsiveness_for_dashboard(self):
        """Checking LOG tab causes unresponsive UI (found in 3.8 server package"""
        super().check_ui_responsiveness()

    def check_system_resource(self):
        """checking system resource tab from the dashboard"""
        self.check_system_resource_id = BaseSelenium.locator_finder_by_id(self, self.check_system_resource_id)
        self.check_system_resource_id.click()
        time.sleep(1)

    def check_system_metrics(self):
        """checking system metrics tab from the dashboard"""
        if self.check_current_package_version() >= 3.8:
            self.check_system_metrics_id = BaseSelenium.locator_finder_by_id(self, self.check_system_metrics_id)
            self.check_system_metrics_id.click()
            time.sleep(1)

            print("scrolling the current page \n")
            super().scroll()

            # Reloading system metrics tab from the dashboard
            self.select_reload_btn_id = BaseSelenium.locator_finder_by_id(self, self.select_reload_btn_id)
            self.select_reload_btn_id.click()

            # Downloading metrics from the dashboard
            if self.driver.name == "chrome":  # this will check browser name
                 print("Downloading metrics has been disabled for the Chrome browser \n")
            else:
                self.metrics_download_id = BaseSelenium.locator_finder_by_id(self, self.metrics_download_id)
                self.metrics_download_id.click()
                time.sleep(3)
                # self.clear_download_bar()
        else:
            print('Metrics Tab not supported for the current package \n')

    def click_twitter_link(self):
        """Clicking on twitter link on dashboard"""
        self.click_twitter_link_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.click_twitter_link_id)
        title = self.switch_tab(self.click_twitter_link_id)  # this method will call switch tab and close tab
        expected_title = "arangodb (@arangodb) / Twitter"
        assert title in expected_title, f"Expected page title {expected_title} but got {title}"

    def click_slack_link(self):
        """Clicking on twitter link on dashboard"""
        self.click_slack_link_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.click_slack_link_id)
        title = self.switch_tab(self.click_slack_link_id)
        expected_title = 'Join ArangoDB Community on Slack!'
        assert title in expected_title, f"Expected page title {expected_title} but got {title}"

    def click_stackoverflow_link(self):
        """Clicking on stack overflow link on dashboard"""
        self.click_stackoverflow_link_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.click_stackoverflow_link_id)
        title = self.switch_tab(self.click_stackoverflow_link_id)
        expected_title = "Newest 'arangodb' Questions - Stack Overflow"
        assert title in expected_title, f"Expected page title {expected_title} but got {title}"

    def click_google_group_link(self):
        """Clicking on Google group link on dashboard"""
        self.click_google_group_link_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.click_google_group_link_id)
        title = self.switch_tab(self.click_google_group_link_id)
        expected_title = "ArangoDB - Google Groups"
        assert title in expected_title, f"Expected page title {expected_title} but got {title}"
