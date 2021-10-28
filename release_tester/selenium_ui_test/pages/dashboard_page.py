import time
from selenium.common.exceptions import TimeoutException
from selenium_ui_test.pages.navbar import NavigationBarPage

# can't circumvent long lines.. nAttr nLines
# pylint: disable=C0301 disable=R0902 disable=R0915


class DashboardPage(NavigationBarPage):
    """Class for Dashboard page"""

    def __init__(self, driver, enterprise):
        """dashboardPage class initialization"""
        super().__init__(driver)
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
        print("Server Package: ", check_server_package_name_sitem.text)
        time.sleep(1)

    def check_current_package_version(self):
        """checking current package version from the dashboard"""
        super().current_package_version()

    def check_current_username(self):
        """checking current username from the dashboard"""
        check_current_username_sitem = self.locator_finder_by_xpath(self.check_current_username_id)
        print("Current User: ", check_current_username_sitem.text)
        time.sleep(1)

    def check_current_db(self):
        """checking current database name from the dashboard"""
        check_current_db_sitem = self.locator_finder_by_xpath(self.check_current_db_id)
        print("Current DB: ", check_current_db_sitem.text)
        time.sleep(1)

    def check_db_status(self):
        """checking current database status from the dashboard"""
        try:
            check_db_status_sitem = self.locator_finder_by_xpath(self.check_db_status_id)
            print("Current Status: ", check_db_status_sitem.text)
            time.sleep(1)
        except TimeoutException:
            node_sitem = self.locator_finder_by_xpath(self.check_cluster_status_id)
            print("Cluster Health: ", node_sitem.text)
            time.sleep(1)

    def check_db_engine(self):
        """checking current database status from the dashboard"""
        check_db_engine_sitem = self.locator_finder_by_id(self.check_db_engine_id)
        print("Current Engine: ", check_db_engine_sitem.text)
        time.sleep(1)

    def check_db_uptime(self):
        """checking current database uptime status from the dashboard"""
        check_db_uptime_sitem = self.locator_finder_by_xpath(self.check_db_uptime_id)
        print("DB Uptime: ", check_db_uptime_sitem.text)
        time.sleep(1)

    def check_responsiveness_for_dashboard(self):
        """Checking LOG tab causes unresponsive UI (found in 3.8 server package"""
        super().check_ui_responsiveness()

    def check_system_resource(self):
        """checking system resource tab from the dashboard"""
        try:
            check_system_resource_sitem = self.locator_finder_by_id(self.check_system_resource_id)
            check_system_resource_sitem.click()
            time.sleep(3)
        except TimeoutException as ex:
            print('FAIL: cound not find the system-statistics locator! \n')

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

            print("scrolling the current page \n")
            super().scroll()

            # toggle view text to table and vice-versa
            print("Changing metrics tab to table view \n")

            text_view = self.locator_finder_by_id(self.show_text)
            text_view.click()
            time.sleep(3)

            print("Changing metrics tab to text view \n")
            table_view = self.locator_finder_by_id(self.show_text)
            table_view.click()
            time.sleep(3)

            # Reloading system metrics tab from the dashboard
            select_reload_btn_sitem = self.locator_finder_by_id(self.select_reload_btn_id)
            select_reload_btn_sitem.click()

            # Downloading metrics from the dashboard
            if self.webdriver.name == "chrome":  # this will check browser name
                print("Downloading metrics has been disabled for the Chrome browser \n")
            else:
                metrics_download_sitem = self.locator_finder_by_id(self.metrics_download_id)
                metrics_download_sitem.click()
                time.sleep(3)
                # self.clear_download_bar()
        else:
            print("Metrics Tab not supported for the current package \n")
