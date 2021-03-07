#!/usr/bin/env python3
""" base class for arangodb starter deployment selenium frontend tests """
from abc import abstractmethod, ABC
import time

from selenium.webdriver.common.keys import Keys

class SeleniumRunner(ABC):
    "abstract base class for selenium UI testing"
    def __init__(self, webdriver):
        """ hi """
        self.web = webdriver

    def disconnect(self):
        """ byebye """
        self.web.close()

    def connect_server(self, frontend_instance, database, cfg):
        """ login... """
        print("S: Opening page")
        self.web.get("http://root@" + frontend_instance[0].get_public_plain_url() + "/_db/_system/_admin/aardvark/index.html")
        assert "ArangoDB Web Interface" in self.web.title
        elem = self.web.find_element_by_id("loginUsername")
        elem.clear()
        elem.send_keys("root")
        elem.send_keys(Keys.RETURN)
        time.sleep(3)
        print("S: logging in")
        elem = self.web.find_element_by_id("goToDatabase").click()

        assert "No results found." not in self.web.page_source

    def detect_version(self, cfg):
        elem = self.web.find_element_by_id("currentVersion")
        print("S: check_version (%s) ~= frontend version? (%s)" % (str(cfg.semver), elem.text))
        print(dir(elem))
        print(elem.text)
        print(str(cfg.semver))
        print(dir(cfg.semver))
        assert elem.text.lower().startswith(str(cfg.semver))

    def navbar_goto(self, tag):
        """ click on any of the items in the 'navbar' """
        print("S: navbar goto %s"% tag)
        elem = self.web.find_element_by_id(tag)
        assert elem
        elem.click()

    def check_health_state(self, expect_state):
        elem = self.web.find_element_by_xpath('/html/body/div[2]/div/div[1]/div/ul[1]/li[2]/a[2]')
        # self.web.find_element_by_class_name("state health-state") WTF? Y not?
        print("S: Health state:" + elem.text)
        assert elem.text == expect_state

    def cluster_dashboard_get_count(self):
        rc = {}

        elm = self.web.find_element_by_xpath('//*[@id="clusterCoordinators"]')
        rc['coordinators'] = elm.text
        elm = self.web.find_element_by_xpath('//*[@id="clusterDBServers"]')
        rc['dbservers'] = elm.text
        print("S: health state: %s"% str(rc))
        return rc
