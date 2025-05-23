#!/usr/bin/env python3
""" dashboard page object """
import time
from selenium.common.exceptions import TimeoutException
from selenium_ui_test.pages.navbar import NavigationBarPage
import semver

# can't circumvent long lines.. nAttr nLines
# pylint: disable=line-too-long disable=too-many-instance-attributes disable=too-many-statements


class DashboardPage(NavigationBarPage):
    """Class for Dashboard page"""

    def __init__(self, driver, cfg, video_start_time, enterprise):
        """dashboardPage class initialization"""
        super().__init__(driver, cfg, video_start_time)
        self.check_server_package_name_id = "enterpriseLabel" if enterprise else "communityLabel"
        self.check_current_package_version_id = "currentVersion"
        self.check_current_username_id = "//li[@id='userBar']//span[@class='toggle']"
        self.check_current_db_id = "//li[@id='dbStatus']/a[@class='state']"
        self.check_db_status_id = "//li[@id='healthStatus']/a[.='GOOD']"
        self.check_cluster_status_id = '//*[@id="healthStatus"]/a[2]'
        self.check_db_engine_id = "nodeattribute-Engine"
        self.check_db_uptime_id = "/html//div[@id='nodeattribute-Uptime']"
        self.check_system_resource_id = "system-statistics"
        self.check_system_metrics_id = "metrics-statistics"
        self.show_text = "toggleView"
        self.select_reload_btn_id = "reloadMetrics"
        self.metrics_download_id = "downloadAs"

    def check_server_package_name(self):
        """checking server package version name"""
        check_server_package_name_sitem = self.locator_finder_by_id(self.check_server_package_name_id)
        self.tprint(f"Server Package: {check_server_package_name_sitem.text}")
        time.sleep(1)

    def check_current_package_version(self):
        """checking current package version from the dashboard"""
        self.current_package_version()

    def check_current_username(self):
        """checking current username from the dashboard"""
        check_current_username_sitem = self.locator_finder_by_xpath(self.check_current_username_id, benchmark=True)
        self.tprint(f"Current User: {check_current_username_sitem.text}")
        time.sleep(1)

    def check_current_db(self):
        """checking current database name from the dashboard"""
        check_current_db_sitem = self.locator_finder_by_xpath(self.check_current_db_id, benchmark=True)
        self.tprint(f"Current DB: {check_current_db_sitem.text}")
        time.sleep(1)

    def check_db_status(self, cluster):
        """checking current database status from the dashboard"""
        if cluster:
            status = self.locator_finder_by_xpath(self.check_cluster_status_id, benchmark=True)
            self.tprint(f"Cluster Health: {status.text}")
        else:
            status = self.locator_finder_by_xpath(self.check_db_status_id, benchmark=True)
            self.tprint(f"Current Status: {status.text}")
        if cluster:
            assert (
                status.text in "NODES OK"
            ), f"Expected page title GOOD but got {status.text}"

        else:
            assert (
                status.text in "GOOD"
            ), f"Expected page title GOOD but got {status.text}"
        time.sleep(1)

    def check_db_engine(self):
        """checking current database status from the dashboard"""
        check_db_engine_sitem = self.locator_finder_by_id(self.check_db_engine_id)
        self.tprint(f"Current Engine: {check_db_engine_sitem.text}")
        time.sleep(1)

    def check_db_uptime(self):
        """checking current database uptime status from the dashboard"""
        check_db_uptime_sitem = self.locator_finder_by_xpath(self.check_db_uptime_id)
        self.tprint(f"DB Uptime: {check_db_uptime_sitem.text}")
        time.sleep(1)

    def check_responsiveness_for_dashboard(self):
        """Checking LOG tab causes unresponsive UI (found in 3.8 server package"""
        self.check_ui_responsiveness()

    def check_system_resource(self):
        """checking system resource tab from the dashboard"""
        try:
            check_system_resource_sitem = self.locator_finder_by_id(self.check_system_resource_id)
            check_system_resource_sitem.click()
            time.sleep(3)
        except TimeoutException as ex:
            self.tprint("FAIL: cound not find the system-statistics locator! \n" + str(ex))

    def check_distribution_tab(self):
        """Checking distribution tab"""
        distribution = '//*[@id="subNavigationBar"]/ul[2]/li[2]/a'
        distribution_sitem = self.locator_finder_by_xpath(distribution)
        distribution_sitem.click()
        time.sleep(3)

    def check_maintenance_tab(self):
        """Checking maintenance tab"""
        maintenance = '//*[@id="subNavigationBar"]/ul[2]/li[3]/a'
        maintenance_sitem = self.locator_finder_by_xpath(maintenance)
        maintenance_sitem.click()
        time.sleep(3)

    def check_system_metrics(self):
        """checking system metrics tab from the dashboard"""
        if self.check_version_is_newer("3.8.0"):
            check_system_metrics_sitem = self.locator_finder_by_id(self.check_system_metrics_id)
            check_system_metrics_sitem.click()
            time.sleep(1)

            self.tprint("scrolling the current page \n")
            self.scroll()

            # toggle view text to table and vice-versa
            self.tprint("Changing metrics tab to table view \n")
            text_view = self.locator_finder_by_id(self.show_text)
            text_view.click()
            time.sleep(3)

            self.tprint("Changing metrics tab to text view \n")
            table_view = self.locator_finder_by_id(self.show_text)
            table_view.click()
            time.sleep(3)

            # Reloading system metrics tab from the dashboard
            select_reload_btn_sitem = self.locator_finder_by_id(self.select_reload_btn_id)
            select_reload_btn_sitem.click()

            # Downloading metrics from the dashboard
            if self.webdriver.name == "chrome":  # this will check browser name
                self.tprint("Downloading metrics has been disabled for the Chrome browser \n")
            else:
                metrics_download_sitem = self.locator_finder_by_id(self.metrics_download_id)
                metrics_download_sitem.click()
                time.sleep(3)
                # self.clear_download_bar()
        else:
            self.tprint("Metrics Tab not supported for the current package \n")

    def get_twitter_link_id(self):
        """Clicking on twitter link on dashboard"""
        if self.current_package_version() >= semver.VersionInfo.parse("3.11.100"):
            return '//*[@id="navigationBar"]/div/p[1]/a'
        return "//*[@id='navigationBar']/div[2]/p[1]/a"

    def get_slack_link_id(self):
        """Clicking on twitter link on dashboard"""
        if self.current_package_version() >= semver.VersionInfo.parse("3.11.100"):
            return '//*[@id="navigationBar"]/div/p[2]/a'
        return "//*[@id='navigationBar']/div[2]/p[2]/a"

    def get_stackoverflow_link_id(self):
        """Clicking on stack overflow link on dashboard"""
        if self.current_package_version() >= semver.VersionInfo.parse("3.11.100"):
            return '//*[@id="navigationBar"]/div/p[3]/a'
        return "//*[@id='navigationBar']/div[2]/p[3]/a"

    def get_google_group_link_id(self):
        """Clicking on Google group link on dashboard"""
        if self.current_package_version() >= semver.VersionInfo.parse("3.11.100"):
            return '//*[@id="navigationBar"]/div/p[4]/a'
        return "//*[@id='navigationBar']/div[2]/p[4]/a"
