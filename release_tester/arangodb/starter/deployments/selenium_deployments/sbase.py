#!/usr/bin/env python3
""" base class for arangodb starter deployment selenium frontend tests """
from abc import abstractmethod, ABC
import logging
import re
import time

from allure_commons._allure import attach
from allure_commons.types import AttachmentType
from beautifultable import BeautifulTable

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    InvalidSessionIdException,
    StaleElementReferenceException,
    TimeoutException,
    NoSuchElementException
)

from selenium_ui_test.main import BaseTest as UITest
from selenium_ui_test.pages.navbar import NavigationBarPage
from selenium_ui_test.pages.login_page import LoginPage

from reporting.reporting_utils import step, attach_table

FNRX = re.compile("[\n@]*")


REPL_TABLE_LOC = {
    # TODO: is it a bug that this id is info-mode-id?
    #'state': 'div[1][@id="info-mode-id"]',
    # 'mode' : 'div[1][@id="info-mode-id"]',
    'state': 'div[1]/div[1]/div[1]',
    'mode': 'div[2]/div[1]/div[1]',
    'role': '//*[@id="info-role-id"]',
    'level': '//*[@id="info-level-id"]',
    'health': '//*[@id="info-msg-id"]',
    'tick':'//*[@id="logger-lastLogTick-id"]'
}

REPL_LF_TABLES = {
    'leader': [
        '//*[@id="repl-logger-clients"]//thead//th[%d]',
        '//*[@id="repl-logger-clients"]//tr[%d]//td[%d]'
    ],
    'follower': [
        '//*[@id="repl-follower-table"]//thead//th[%d]',
        '//*[@id="repl-follower-table"]//tr[%d]//td[%d]'
    ]
}
class SeleniumRunner(ABC):
    "abstract base class for selenium UI testing"
    # pylint: disable=C0301 disable=R0904
    def __init__(self, webdriver,
                 is_headless: bool,
                 testrun_name: str,
                 ssl: bool):
        """ hi """
        self.ssl = ssl
        self.is_headless = is_headless
        self.testrun_name = testrun_name
        self.webdriver = webdriver
        self.original_window_handle = None
        self.state = ""
        time.sleep(3)
        self.web.set_window_size(1920, 1080)
        time.sleep(3)
        self.importer = None
        self.restorer = None
        self.cfg = None
        self.is_cluster = False
        self.test_results = []

    def set_instances(self, cfg, importer, restorer):
        """ change the used frontend instance """
        self.cfg = cfg
        self.importer = importer
        self.restorer = restorer


    def progress(self, msg):
        """ add something to the state... """
        logging.info("UI-Test: " + msg)
        with step("UI test progress: " + msg):
            pass
        if len(self.state) > 0:
            self.state += "\n"
        self.state += "UI: " + msg

    def reset_progress(self):
        """ done with one test. Flush status buffer. """
        self.state = ""

    def get_progress(self):
        """ extract the current progress buffer """
        ret = self.state + "\n"
        self.reset_progress()
        return ret

    @step
    def disconnect(self):
        """ byebye """
        self.progress("Close!")
        self.webdriver.close()

    @step
    def get_browser_log_entries(self):
        """get log entreies from selenium and add to python logger before returning"""
        print('B'*80)
        loglevels = { 'NOTSET':   0,
                      'DEBUG':   10,
                      'INFO':    20,
                      'WARNING': 30,
                      'ERROR':   40,
                      'SEVERE':  40,
                      'CRITICAL':50}
        slurped_logs = self.webdriver.get_log('browser')
        browserlog = logging.getLogger('browser')
        for entry in slurped_logs:
            print(entry['message'])
            #convert broswer log to python log format
            rec = browserlog.makeRecord("%s.%s"%(
                browserlog.name,entry['source']
            ),
                                        loglevels.get('WARNING'), # always log it as warn...
                                        # loglevels.get(entry['level']),
                                        '.',
                                        0,
                                        entry['message'],
                                        None,
                                        None)
            rec.created = entry['timestamp'] /1000 # log using original timestamp.. us -> ms
            # pylint: disable=W0703
            try:
                #add browser log to python log
                browserlog.handle(rec)
                self.progress(entry['message'])
            except Exception as ex:
                print("caught exception during transfering browser logs: " + str(ex))
                print(entry)

    @step
    def take_screenshot(self, filename=None):
        """ *snap* """
        if filename is None:
            filename = '%s_%s_exception_screenshot.png' % (
                FNRX.sub('', self.testrun_name),
                self.__class__.__name__
            )

        self.progress("Taking screenshot from: %s " %
                      self.webdriver.current_url)
        # pylint: disable=W0703
        try:
            if self.is_headless:
                self.progress("taking full screenshot")
                elmnt = self.webdriver.find_element_by_tag_name('body')
                screenshot = elmnt.screenshot_as_png()
            else:
                self.progress("taking screenshot")
                screenshot = self.webdriver.get_screenshot_as_png()
        except InvalidSessionIdException:
            self.progress("Fatal: webdriver not connected!")
        except Exception as ex:
            self.progress("falling back to taking partial screenshot " + str(ex))
            screenshot = self.webdriver.get_screenshot_as_png()
        self.get_browser_log_entries()
        self.progress("Saving screenshot to file: %s" % filename)
        with open(filename, "wb") as file:
            file.write(screenshot)

        attach(screenshot, name="Screenshot ({fn})".format(fn=filename), attachment_type=AttachmentType.PNG)

    @step
    def ui_assert(self, conditionstate, message):
        """ python assert sucks. fuckit. """
        if not conditionstate:
            logging.error(message)
            self.take_screenshot()
            assert False, message

    @step
    def connect_server_new_tab(self, frontend_instance, database, cfg):
        """ login... """
        self.progress("Opening page")
        print(frontend_instance[0].get_public_plain_url())
        self.original_window_handle = self.webdriver.current_window_handle

        # Open a new window
        self.webdriver.execute_script("window.open('');")
        self.webdriver.switch_to.window(self.webdriver.window_handles[1])
        self.webdriver.get(self.get_protocol() + "://" +
                           frontend_instance[0].get_public_plain_url() +
                     "/_db/_system/_admin/aardvark/index.html")
        login_page = LoginPage(self.webdriver)
        login_page.login_webif(cfg, "root", frontend_instance[0].get_passvoid())

    def xpath(self, path):
        """ shortcut xpath """
        return self.webdriver.find_element_by_xpath(path)

    def by_class(self, classname):
        """ shortcut class-id """
        return self.webdriver.find_element_by_class_name(classname)
    @step
    def close_tab_again(self):
        """ close a tab, and return to main window """
        self.webdriver.close()# Switch back to the first tab with URL A
        # self.webdriver.switch_to.window(self.webdriver.window_handles[0])
        # print("Current Page Title is : %s" %self.webdriver.title)
        # self.webdriver.close()
        self.webdriver.switch_to.window(self.original_window_handle)
        self.original_window_handle = None

    @step
    def connect_server(self, frontend_instance, database, cfg):
        """ login... """
        self.progress("Opening page")
        print(frontend_instance[0].get_public_plain_url())
        self.webdriver.get(self.get_protocol() + "://" +
                           frontend_instance[0].get_public_plain_url() +
                     "/_db/_system/_admin/aardvark/index.html")
        login_page = LoginPage(self.webdriver)
        login_page.login_webif(cfg, 'root', frontend_instance[0].get_passvoid())

    @step
    def detect_version(self):
        """
        extracts the version in the lower right and
         compares it to a given version
        """
        count = 0
        while True:
            try:
                elem = self.webdriver.find_element_by_id("currentVersion")
                enterprise_elem = self.webdriver.find_element_by_class_name(
                    "logo.big")
                ret = {
                    'version': elem.text,
                    'enterprise': enterprise_elem.text
                }
                self.progress("check_version (%s) (%s)" % (
                    ret['version'], ret['enterprise']))
                if (len(ret['version']) > 0) and (len(ret['enterprise']) > 0):
                    return ret
                self.progress('retry version.')
                time.sleep(1)
                if count > 200:
                    raise TimeoutException("canot detect version, found: %s " %str(ret))
                count += 1
            except TimeoutException as ex:
                self.take_screenshot()
                raise ex

    @step
    def get_health_state(self):
        """ extract the health state in the upper right corner """
        try:
            elem = self.xpath(
                '/html/body/div[2]/div/div[1]/div/ul[1]/li[2]/a[2]')
        except TimeoutException as ex:
            self.take_screenshot()
            raise ex
        # self.webdriver.find_element_by_class_name("state health-state") WTF? Y not?
        self.progress("Health state:" + elem.text)
        return elem.text

    @step
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
                        EC.presence_of_element_located((
                            By.XPATH,
                            '//*[@id="clusterCoordinators"]')),
                        message="UI-Test: [CLUSTER tab] coordinators path didn't arive " +
                        "on time %ds inspect screenshot!" % timeout
                    )
                    elm_accepted = len(elm.text) > 0
                # elm = self.webdriver.find_element_by_xpath(
                #   '//*[@id="clusterCoordinators"]')
                ret['coordinators'] = elm.text
                elm = self.xpath('//*[@id="clusterDBServers"]')
                ret['dbservers'] = elm.text
                self.progress("health state: %s"% str(ret))
                return ret
            except StaleElementReferenceException:
                self.progress('retrying after stale element')
                time.sleep(1)
                continue
            except TimeoutException as ex:
                self.take_screenshot()
                raise ex

    def _cluster_get_nodes_table(self, timeout):
        """ repeatable inner func """
        table_coord_elm = WebDriverWait(
            self.webdriver,
            timeout).until(
                EC.presence_of_element_located((
                    By.CLASS_NAME,
                    'pure-g.cluster-nodes.coords-nodes.pure-table.pure-table-body')),
                message="UI-Test: Cluster nodes table didn't become available on time %s" % timeout
        )
        table_dbsrv_elm = self.by_class(
            'pure-g.cluster-nodes.dbs-nodes.pure-table.pure-table-body')
        column_names = ['name', 'url', 'version', 'date', 'state']
        table = []
        for elm in [table_coord_elm, table_dbsrv_elm]:
            for table_row_num in [1, 2, 3]:
                row ={}
                table.append(row)
                for table_column in [1, 2, 3, 4, 5]:
                    table_cell_elm = None
                    if table_column == 5:
                        table_cell_elm = elm.find_element_by_xpath(
                            'div[%d]/div[%d]/i'%(
                                table_row_num,
                                table_column))
                        try:
                            row[column_names[table_column - 1]
                                ] = table_cell_elm.get_attribute(
                                    'data-original-title')
                        except NoSuchElementException:
                            row[column_names[table_column - 1]] = None
                        if row[column_names[table_column - 1]] is None:
                            row[column_names[table_column - 1]
                                ] = table_cell_elm.get_property(
                                    'title')
                    else:
                        table_cell_elm = elm.find_element_by_xpath(
                            'div[%d]/div[%d]'%(
                                table_row_num,
                                table_column))
                        row[column_names[table_column - 1]] = table_cell_elm.text
        pretty_table = BeautifulTable(maxwidth=160)
        for row in table:
            pretty_table.rows.append([
                row['name'],
                row['url'],
                row['version'],
                row['date'],
                row['state']
                ])
        pretty_table.columns.header = [
            "Name", "URL", "Ver", "Date", "State"]
        self.progress('\n' + str(pretty_table))
        attach_table(pretty_table, "Cluster nodes table")
        return table

    @step
    def cluster_get_nodes_table(self, timeout=20):
        """
        extract the table of coordinators / dbservers from the 'nodes' page
        """
        while True:
            try:
                table = self._cluster_get_nodes_table(timeout)
                return table
            except StaleElementReferenceException:
                self.progress('retrying after stale element')
                time.sleep(1)
                continue
            except NoSuchElementException:
                self.progress('retrying after no such element')
                time.sleep(1)
                continue
            except TimeoutException as ex:
                self.take_screenshot()
                raise ex

    def get_state_table(self, timeout):
        """ extract the replication state table """
        table_elm = WebDriverWait(self.webdriver, timeout).until(
            EC.presence_of_element_located((By.CLASS_NAME,
                                            'pure-g.cluster-values')),
            message="UI-Test: replication state table didn't arive on time %s " % timeout
        )
        state_table = {}
        for key in REPL_TABLE_LOC:
            state_table[key] = table_elm.find_element_by_xpath(
                REPL_TABLE_LOC[key]).text
        return state_table

    def _get_repl_page(self, which, timeout):
        """ parse the complete replication state table """
        state_table = self.get_state_table(timeout)

        follower_table = []
        column_indices = [1,2,3,4,5]
        more_lines = True
        table_head = []
        for i in column_indices:
            table_head.append(
                self.webdriver.find_element_by_xpath(
                REPL_LF_TABLES[which][0] % i).text)
        follower_table.append(table_head)
        count = 1
        while more_lines:
            try:
                row_data = []
                for i in column_indices:
                    cell = self.webdriver.find_element_by_xpath(
                        REPL_LF_TABLES[which][1]%(
                        count, i))
                    row_data.append(cell.text)
                follower_table.append(row_data)
            except NoSuchElementException:
                print('UI-Test: no more lines.')
                more_lines = False
            count += 1
        return {
            'state_table': state_table,
            'follower_table': follower_table,
        }

    def get_replication_screen(self, is_leader, timeout=20):
        """ fetch & parse the replication tab """
        retry_count = 0
        while True:
            try:
                return self._get_repl_page(
                    'leader' if is_leader else 'follower',
                    timeout)
            except NoSuchElementException:
                self.progress('retrying after element not found')
                time.sleep(1)
                retry_count += 1
                continue
            except StaleElementReferenceException:
                self.progress('retrying after stale element')
                time.sleep(1)
                retry_count += 1
                continue
            except TimeoutException as ex:
                retry_count += 1
                if retry_count < 5:
                    self.progress('re-trying goto replication')
                    NavigationBarPage(self.webdriver).navbar_goto('replication')
                elif retry_count > 20:
                    self.take_screenshot()
                    raise ex
                else:
                    self.webdriver.refresh()
                    time.sleep(1)

    def check_version(self, cfg):
        """ checks whether the UI has the version that cfg dictates """
        ver = self.detect_version()
        self.progress(' %s ~= %s?'% (ver['version'].lower(), str(cfg.semver)))

        assert ver['version'].lower().startswith(str(cfg.semver)), "UI-Test: wrong version"

        if cfg.enterprise:
            assert ver['enterprise'] == 'ENTERPRISE EDITION', "UI-Test: expected enterprise"
        else:
            assert ver['enterprise'] == 'COMMUNITY EDITION', "UI-Test: expected community"

    # pylint: disable=R1705
    def get_protocol(self):
        """get HTTP protocol for this runner(http/https)"""
        if self.ssl:
            return "https"
        else:
            return "http"

    @abstractmethod
    def check_old(self, cfg, leader_follower=False, expect_follower_count=2, retry_count=10):
        """ check the integrity of the old system before the upgrade """
    @abstractmethod
    def upgrade_deployment(self, old_cfg, new_cfg, timeout):
        """ check the upgrade whether the versions in the table switch etc. """
    @abstractmethod
    def jam_step_1(self, cfg, frontend_instance):
        """ check the integrity of the system before testing the resillience """
    @abstractmethod
    def jam_step_2(self, cfg):
        """ check the integrity of the system after testing the resillience """

    def check_empty_ui(self):
        """ run all tests that expect the server to be empty """

    def check_full_ui(self, root_passvoid, frontend_instance):
        """ run all tests that work with data """
        # frontend = frontend_instance[0]
        # ui_test = UITest(frontend.get_passvoid(), frontend.get_endpoint(), self.web)
        ui_test = UITest(root_passvoid, '', self.webdriver)
        NavigationBarPage(self.webdriver).navbar_goto("users")
        ui_test.test_user(self.cfg, frontend_instance[0].get_passvoid())
        ui_test.test_collection(self.cfg.test_data_dir.resolve(), self.is_cluster)
        ui_test.test_dashboard(self.cfg.enterprise, self.is_cluster)
        ui_test.test_views(self.is_cluster)
        print('i'*80)
        print(self.cfg.test_data_dir)
        print(str(self.cfg.test_data_dir))
        print(self.cfg.test_data_dir.resolve())
        print('g'*80)
        NavigationBarPage(self.webdriver).navbar_goto('graphs')
        ui_test.test_graph(self.cfg, self.importer, self.cfg.test_data_dir.resolve())
        print('u'*80)
        ui_test.test_query(self.cfg,
                           self.is_cluster,
                           self.restorer,
                           self.importer,
                           self.cfg.test_data_dir.resolve())
        # ui_test.test_support()
        self.test_results += ui_test.test_results


    def clear_ui (self):
        """ go all through the ui, flush all data (graphs, users, databases, collections) """
