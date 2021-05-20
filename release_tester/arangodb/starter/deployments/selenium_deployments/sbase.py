#!/usr/bin/env python3
""" base class for arangodb starter deployment selenium frontend tests """
from abc import abstractmethod, ABC
import logging
import re
import time

from beautifultable import BeautifulTable
from selenium.webdriver.common.by import By

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    InvalidSessionIdException,
    StaleElementReferenceException,
    TimeoutException,
    NoSuchElementException
)

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
    def __init__(self, webdriver,
                 is_headless: bool,
                 testrun_name: str):
        """ hi """
        self.is_headless = is_headless
        self.testrun_name = testrun_name
        self.web = webdriver
        self.original_window_handle = None
        self.state = ""
        time.sleep(3)
        self.web.set_window_size(1920, 2048)
        time.sleep(3)

    def progress(self, msg):
        """ add something to the state... """
        logging.info("UI-Test: " + msg)
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

    def disconnect(self):
        """ byebye """
        self.progress("Close!")
        self.web.close()

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
        slurped_logs = self.web.get_log('browser')
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
            try:
                #add browser log to python log
                browserlog.handle(rec)
                self.progress(entry['message'])
            except:
                print(entry)

    def take_screenshot(self, filename=None):
        """ *snap* """
        if filename is None:
            filename = '%s_%s_exception_screenshot.png' % (
                FNRX.sub('', self.testrun_name),
                self.__class__.__name__
            )

        self.progress("Taking screenshot from: %s " %
                      self.web.current_url)
        try:
            if self.is_headless:
                self.progress("taking full screenshot")
                el = self.web.find_element_by_tag_name('body')
                el.screenshot(filename)
            else:
                self.progress("taking screenshot")
                self.web.save_screenshot(filename)
        except InvalidSessionIdException:
            self.progress("Fatal: webdriver not connected!")
        except Exception as ex:
            self.progress("falling back to taking partial screenshot " + str(ex))
            self.web.save_screenshot(filename)
        self.get_browser_log_entries()

    def ui_assert(self, conditionstate, message):
        """ python assert sucks. fuckit. """
        if not conditionstate:
            logging.error(message)
            self.take_screenshot()
            assert False, message

    def connect_server_new_tab(self, frontend_instance, database, cfg):
        """ login... """
        self.progress("Opening page")
        print(frontend_instance[0].get_public_plain_url())
        self.original_window_handle = self.web.current_window_handle

        # Open a new window
        self.web.execute_script("window.open('');")
        self.web.switch_to.window(self.web.window_handles[1])
        self.web.get("http://" +
                     frontend_instance[0].get_public_plain_url() +
                     "/_db/_system/_admin/aardvark/index.html")

        self.login_webif(frontend_instance, database, cfg)

    def xpath(self, path):
        """ shortcut xpath """
        return self.web.find_element_by_xpath(path)

    def by_class(self, classname):
        """ shortcut class-id """
        return self.web.find_element_by_class_name(classname)

    def close_tab_again(self):
        """ close a tab, and return to main window """
        self.web.close()# Switch back to the first tab with URL A
        # self.web.switch_to.window(self.web.window_handles[0])
        # print("Current Page Title is : %s" %self.web.title)
        # self.web.close()
        self.web.switch_to.window(self.original_window_handle)
        self.original_window_handle = None

    def connect_server(self, frontend_instance, database, cfg):
        """ login... """
        self.progress("Opening page")
        print(frontend_instance[0].get_public_plain_url())
        self.web.get("http://" +
                     frontend_instance[0].get_public_plain_url() +
                     "/_db/_system/_admin/aardvark/index.html")
        self.login_webif(frontend_instance, database, cfg)

    def login_webif(self, frontend_instance, database, cfg, recurse=0):
        """ log into an arangodb webinterface """
        if recurse > 10:
            raise Exception("UI-Test: 10 successless login attempts")
        try:
            try:
                count = 0
                while True:
                    count += 1
                    elem = WebDriverWait(self.web, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "html")),
                        message="UI-Test: page didn't load after 10s"
                    )
                    data = elem.text
                    if len(data) < 0:
                        self.progress(
                            'ArangoDB Web Interface not loaded yet, retrying')
                        time.sleep(2)
                    if count == 10:
                        if elem is None:
                            self.progress(elem, " locator has not been found.")
                            self.web.refresh()
                            time.sleep(5)
                        else:
                            assert "ArangoDB Web Interface" in self.web.title, \
                                "webif title not found"
                            break
            except TimeoutException as ex:
                self.take_screenshot()
                raise ex
            try:
                logname = WebDriverWait(self.web, 10).until(
                    EC.element_to_be_clickable((By.ID, "loginUsername")),
                    message="UI-Test: loginUsername didn't become clickeable on time. 10s"
                )
                logname.click()
                logname.clear()
                logname.send_keys("root")

                if logname is None:
                    self.progress("locator loginUsername has not found.")

            except StaleElementReferenceException as ex:
                self.progress("stale element, force reloading with sleep: " +
                              str(ex))
                self.web.refresh()
                time.sleep(5)
                return self.login_webif(frontend_instance,
                                        database,
                                        cfg,
                                        recurse + 1)

            count = 0
            while True:
                passvoid = self.web.find_element_by_id("loginPassword")
                txt = passvoid.text
                print("UI-Test: xxxx [" + txt + "]")
                if len(txt) > 0:
                    self.progress(
                        'something was in the passvoid field. retrying. ' +
                        txt)
                    time.sleep(2)
                    continue
                passvoid.click()
                passvoid.clear()
                passvoid.send_keys(frontend_instance[0].get_passvoid())
                passvoid.send_keys(Keys.RETURN)
                break
            self.progress("logging in")
            count = 0
            while True:
                count += 1
                elem = WebDriverWait(self.web, 15).until(
                    EC.presence_of_element_located((By.ID, "loginDatabase")),
                    message="UI-Test: loginDatabase didn't become clickeable on time 15s"
                )
                txt = elem.text
                if txt.find('_system') < 0:
                    if count < 9:
                        self.take_screenshot()
                    self.progress('_system not found in ' +
                                  txt +
                                  ' ; retrying!')
                    if count == 10:
                        self.progress('refreshing webpage and retrying...')
                        self.web.refresh()
                        time.sleep(5)
                        return self.login_webif(frontend_instance,
                                                database,
                                                cfg,
                                                recurse + 1)
                    time.sleep(2)
                else:
                    break
            elem = WebDriverWait(self.web, 15).until(
                EC.element_to_be_clickable((By.ID, "goToDatabase")),
                message="UI-Test: choosing database didn't become clickeable on time 15s"
            )
            elem.click()
            self.progress("we're in!")

            assert "No results found." not in self.web.page_source, \
                "no results found?"
        except TimeoutException as ex:
            self.take_screenshot()
            raise ex

    def detect_version(self):
        """
        extracts the version in the lower right and
         compares it to a given version
        """
        count = 0
        while True:
            try:
                elem = self.web.find_element_by_id("currentVersion")
                enterprise_elem = self.web.find_element_by_class_name(
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

    def navbar_goto(self, tag):
        """ click on any of the items in the 'navbar' """
        count = 0
        self.progress("navbar goto %s"% tag)
        while True:
            try:
                elem = self.web.find_element_by_id(tag)
                assert elem, "navbar goto failed?"
                elem.click()
                self.web.find_element_by_class_name(tag + '-menu.active')
                self.progress("goto current URL: " + self.web.current_url)
                if not self.web.current_url.endswith('#'+ tag):
                    # retry...
                    continue
                return
            except NoSuchElementException:
                self.progress('retrying to switch to ' + tag)
                time.sleep(1)
                count += 1
                if count %15 == 0:
                    self.progress("reloading page!")
                    self.web.refresh()
                    time.sleep(1)
                continue
            except TimeoutException as ex:
                self.take_screenshot()
                raise ex

    def get_health_state(self):
        """ xtracts the health state in the upper right corner """
        try:
            elem = self.xpath(
                '/html/body/div[2]/div/div[1]/div/ul[1]/li[2]/a[2]')
        except TimeoutException as ex:
            self.take_screenshot()
            raise ex
        # self.web.find_element_by_class_name("state health-state") WTF? Y not?
        self.progress("Health state:" + elem.text)
        return elem.text

    def cluster_dashboard_get_count(self, timeout=10):
        """
         extracts the coordinator / dbserver count from the 'cluster' page
        """
        ret = {}
        while True:
            try:
                elm = None
                elm_accepted = False
                while not elm_accepted:
                    elm = WebDriverWait(self.web, timeout).until(
                        EC.presence_of_element_located((
                            By.XPATH,
                            '//*[@id="clusterCoordinators"]')),
                        message="UI-Test: coordinators path didn't arive on time %ds" % timeout
                    )
                    elm_accepted = len(elm.text) > 0
                # elm = self.web.find_element_by_xpath(
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

    def cluster_get_nodes_table(self, timeout=20):
        """
        extracts the table of coordinators / dbservers from the 'nodes' page
        """
        while True:
            try:
                table_coord_elm = WebDriverWait(
                    self.web,
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
                                except Exception:
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
        table_elm = WebDriverWait(self.web, timeout).until(
            EC.presence_of_element_located((By.CLASS_NAME,
                                            'pure-g.cluster-values')),
            message="UI-Test: replication state table didn't arive on time %s " % timeout
        )
        state_table = {}
        for key in REPL_TABLE_LOC:
            state_table[key] = table_elm.find_element_by_xpath(
                REPL_TABLE_LOC[key]).text
        return state_table

    def get_repl_page(self, which, timeout):
        """ parse the complete replication state table """
        state_table = self.get_state_table(timeout)

        follower_table = []
        column_indices = [1,2,3,4,5]
        more_lines = True
        th = []
        for i in column_indices:
            th.append(self.web.find_element_by_xpath(
                REPL_LF_TABLES[which][0] % i).text)
        follower_table.append(th)
        count = 1
        while more_lines:
            try:
                row_data = []
                for i in column_indices:
                    cell = self.web.find_element_by_xpath(
                        REPL_LF_TABLES[which][1]%(
                        count, i))
                    row_data.append(cell.text)
                follower_table.append(row_data)
            except Exception:
                print('UI-Test: no more lines')
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
                return self.get_repl_page(
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
                    self.navbar_goto('replication')
                elif retry_count > 20:
                    self.take_screenshot()
                    raise ex
                else:
                    self.web.refresh()
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

    @abstractmethod
    def check_old(self, cfg, leader_follower=True):
        """ check the integrity of the old system before the upgrade """
    @abstractmethod
    def upgrade_deployment(self, old_cfg, new_cfg):
        """ check the upgrade whether the versions in the table switch etc. """
    @abstractmethod
    def jam_step_1(self, cfg):
        """ check the integrity of the old system before the upgrade """
    @abstractmethod
    def jam_step_2(self, cfg):
        """ check the integrity of the old system before the upgrade """
