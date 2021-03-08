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
        """ extracts the version in the lower right and compares it to a given version """
        elem = self.web.find_element_by_id("currentVersion")
        print("S: check_version (%s) ~= frontend version? (%s)" % (str(cfg.semver), elem.text))
        print(dir(elem))
        print(elem.text)
        print(str(cfg.semver))
        print(dir(cfg.semver))
        assert elem.text.lower().startswith(str(cfg.semver))
        # TODO: enterprise

    def navbar_goto(self, tag):
        """ click on any of the items in the 'navbar' """
        print("S: navbar goto %s"% tag)
        elem = self.web.find_element_by_id(tag)
        assert elem
        elem.click()

    def check_health_state(self, expect_state):
        """ xtracts the health state in the upper right corner """
        elem = self.web.find_element_by_xpath('/html/body/div[2]/div/div[1]/div/ul[1]/li[2]/a[2]')
        # self.web.find_element_by_class_name("state health-state") WTF? Y not?
        print("S: Health state:" + elem.text)
        assert elem.text == expect_state

    def cluster_dashboard_get_count(self):
        """ extracts the coordinator / dbserver count from the 'cluster' page """
        ret = {}

        elm = self.web.find_element_by_xpath('//*[@id="clusterCoordinators"]')
        ret['coordinators'] = elm.text
        elm = self.web.find_element_by_xpath('//*[@id="clusterDBServers"]')
        ret['dbservers'] = elm.text
        print("S: health state: %s"% str(ret))
        return ret

    def cluster_get_nodes_table(self):
        """ extracts the table of coordinators / dbservers from the 'nodes' page """
        table_coord_elm = self.web.find_element_by_class_name('pure-g.cluster-nodes.coords-nodes.pure-table.pure-table-body')
        table_dbsrv_elm = self.web.find_element_by_class_name('pure-g.cluster-nodes.dbs-nodes.pure-table.pure-table-body')
        column_names = ['name', 'url', 'version', 'date', 'state']
        table = []
        for elm in [table_coord_elm, table_dbsrv_elm]:
            for table_row_num in [1, 2, 3]:
                row ={}
                table.append(row)
                for table_column in [1, 2, 3, 4, 5]:
                    table_cell_elm = None
                    if table_column is 5:
                        table_cell_elm = elm.find_element_by_xpath('div[%d]/div[%d]/i'%(table_row_num, table_column))
                        row[column_names[table_column - 1]] = table_cell_elm.get_property('title')
                    else:
                        table_cell_elm = elm.find_element_by_xpath('div[%d]/div[%d]'%(table_row_num, table_column))
                        row[column_names[table_column - 1]] = table_cell_elm.text
        return table

    @abstractmethod
    def check_old(self, cfg):
        """ check the integrity of the old system before the upgrade """
