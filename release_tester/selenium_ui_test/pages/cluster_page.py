#!/usr/bin/python3
"""the cluster pgae object"""
import time

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium_ui_test.pages.navbar import NavigationBarPage


class ClusterPage(NavigationBarPage):
    """Class for Cluster page"""

    def __init__(self, driver):
        """Cluster page initialization"""
        super().__init__(driver)

    def cluster_dashboard_get_count(self, timeout=15):
        """
        extract the coordinator / dbserver count from the 'cluster' page
        """
        ret = {}
        while True:
            try:
                elm = None
                elm_accepted = False
                while not elm_accepted:
                    elm = WebDriverWait(self.webdriver, timeout).until(
                        EC.presence_of_element_located((By.XPATH, '//*[@id="clusterCoordinators"]')),
                        message="UI-Test: [CLUSTER tab] coordinators path didn't arive "
                        + "on time %ds inspect screenshot!" % timeout,
                    )
                    elm_accepted = len(elm.text) > 0
                # elm = self.webdriver.find_element_by_xpath(
                #   '//*[@id="clusterCoordinators"]')
                ret["coordinators"] = elm.text
                elm = self.locator_finder_by_xpath('//*[@id="clusterDBServers"]')
                ret["dbservers"] = elm.text
                self.progress("health state: %s" % str(ret))
                return ret
            except StaleElementReferenceException:
                self.progress("retrying after stale element")
                time.sleep(1)
                continue
