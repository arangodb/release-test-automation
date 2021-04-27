import time

from baseSelenium import BaseSelenium


class DashboardPage(BaseSelenium):

    def __init__(self, driver):
        super().__init__()
        self.driver = driver
        self.check_server_package_name_id = "enterpriseLabel"
        self.check_current_package_version_id = "currentVersion"
        self.check_current_username_id = "//li[@id='userBar']//span[@class='toggle']"
        self.check_current_db_id = "//li[@id='dbStatus']/a[@class='state']"
        self.check_db_status_id = "//li[@id='healthStatus']/a[.='GOOD']"
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

    # checking server package version name
    def check_server_package_name(self):
        self.check_server_package_name_id = \
            BaseSelenium.locator_finder_by_text_id(self, self.check_server_package_name_id)
        print("Server Package: ", self.check_server_package_name_id)
        time.sleep(1)

    # checking current package version from the dashboard
    def check_current_package_version(self):
        self.check_current_package_version_id = \
            BaseSelenium.locator_finder_by_text_id(self, self.check_current_package_version_id)
        print("Package Version: ", self.check_current_package_version_id)
        time.sleep(1)

    # checking current username from the dashboard
    def check_current_username(self):
        self.check_current_username_id = \
            BaseSelenium.locator_finder_by_text_xpath(self, self.check_current_username_id)
        print("Current User: ", self.check_current_username_id)
        time.sleep(1)

    # checking current database name from the dashboard
    def check_current_db(self):
        self.check_current_db_id = \
            BaseSelenium.locator_finder_by_text_xpath(self, self.check_current_db_id)
        print("Current DB: ", self.check_current_db_id)
        time.sleep(1)

    # checking current database status from the dashboard
    def check_db_status(self):
        self.check_db_status_id = \
            BaseSelenium.locator_finder_by_text_xpath(self, self.check_db_status_id)
        print("Current Status: ", self.check_db_status_id)
        time.sleep(1)

    # checking current database status from the dashboard
    def check_db_engine(self):
        self.check_db_engine_id = \
            BaseSelenium.locator_finder_by_text_id(self, self.check_db_engine_id)
        print("Current Engine: ", self.check_db_engine_id)
        time.sleep(1)

    # checking current database uptime status from the dashboard
    def check_db_uptime(self):
        self.check_db_uptime_id = \
            BaseSelenium.locator_finder_by_text_xpath(self, self.check_db_uptime_id)
        print("DB Uptime: ", self.check_db_uptime_id)
        time.sleep(1)

    # checking system resource tab from the dashboard
    def check_system_resource(self):
        self.check_system_resource_id = BaseSelenium.locator_finder_by_id(self, self.check_system_resource_id)
        self.check_system_resource_id.click()
        time.sleep(1)

    # checking system metrics tab from the dashboard
    def check_system_metrics(self):
        self.check_system_metrics_id = BaseSelenium.locator_finder_by_id(self, self.check_system_metrics_id)
        self.check_system_metrics_id.click()
        time.sleep(1)

    # Reloading system metrics tab from the dashboard
    def select_reload_btn(self):
        self.select_reload_btn_id = BaseSelenium.locator_finder_by_id(self, self.select_reload_btn_id)
        self.select_reload_btn_id.click()

    # Downloading metrics from the dashboard
    def metrics_download(self):
        self.metrics_download_id = BaseSelenium.locator_finder_by_id(self, self.metrics_download_id)
        self.metrics_download_id.click()
        time.sleep(3)

    # Clicking on twitter link on dashboard
    def click_twitter_link(self):
        self.click_twitter_link_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.click_twitter_link_id)
        self.switch_tab(self.click_twitter_link_id)  # this method will call switch tab and close tab

    # Clicking on twitter link on dashboard
    def click_slack_link(self):
        self.click_slack_link_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.click_slack_link_id)
        self.switch_tab(self.click_slack_link_id)

    # Clicking on stack overflow link on dashboard
    def click_stackoverflow_link(self):
        self.click_stackoverflow_link_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.click_stackoverflow_link_id)
        self.switch_tab(self.click_stackoverflow_link_id)

    # Clicking on Google group link on dashboard
    def click_google_group_link(self):
        self.click_google_group_link_id = \
            BaseSelenium.locator_finder_by_xpath(self, self.click_google_group_link_id)
        self.switch_tab(self.click_google_group_link_id)
