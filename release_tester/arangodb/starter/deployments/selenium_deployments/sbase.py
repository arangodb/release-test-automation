#!/usr/bin/env python3
""" base class for arangodb starter deployment selenium frontend tests """
from abc import abstractmethod, ABC
import time
from selenium.webdriver.common.by import By

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, NoSuchElementException
class SeleniumRunner(ABC):
    "abstract base class for selenium UI testing"
    def __init__(self, webdriver):
        """ hi """
        self.web = webdriver
        self.original_window_handle = None
        print(dir(self.web.switch_to))

    def disconnect(self):
        """ byebye """
        print("S: Close!")
        self.web.close()

    def take_screenshot(self, filename='exception_screenshot.png'):
        """ *snap* """
        #self.set_window_size(1920, total_height)
        #time.sleep(2)
        self.web.save_screenshot(filename)

    def connect_server_new_tab(self, frontend_instance, database, cfg):
        """ login... """
        print("S: Opening page")
        print(frontend_instance[0].get_public_plain_url())
        self.original_window_handle = self.web.current_window_handle

        # Open a new window
        self.web.execute_script("window.open('');")
        self.web.switch_to.window(self.web.window_handles[1])
        self.web.get("http://" +
                     frontend_instance[0].get_public_plain_url() +
                     "/_db/_system/_admin/aardvark/index.html")

        self.login_webif(frontend_instance, database, cfg)

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
        print("S: Opening page")
        print(frontend_instance[0].get_public_plain_url())
        self.web.get("http://" +
                     frontend_instance[0].get_public_plain_url() +
                     "/_db/_system/_admin/aardvark/index.html")
        self.login_webif(frontend_instance, database, cfg)

    def login_webif(self, frontend_instance, database, cfg):
        """ log into an arangodb webinterface """
        try:
            assert "ArangoDB Web Interface" in self.web.title
            logname = WebDriverWait(self.web, 10).until(
                EC.presence_of_element_located((By.ID, "loginUsername"))
            )
            logname.clear()
            logname.send_keys("root")
            passvoid = self.web.find_element_by_id("loginPassword")
            passvoid.clear()
            passvoid.send_keys(frontend_instance[0].get_passvoid())
            passvoid.send_keys(Keys.RETURN)
            print("S: logging in")
            count = 0
            while True:
                count += 1
                elem = WebDriverWait(self.web, 15).until(
                    EC.presence_of_element_located((By.ID, "loginDatabase"))
                )
                txt = elem.text
                if txt.find('_system') < 0:
                    if count < 9:
                        self.take_screenshot()
                    print('S: _system not found in ' + txt + ' ; retrying!')
                    if count %10 == 0:
                        print('S: refreshing webpage.')
                        self.web.refresh()
                    if count > 100:
                        raise Exception('failed to locate "_system" in the login dialog')
                    time.sleep(2)
                else:
                    break
            elem = WebDriverWait(self.web, 15).until(
                EC.presence_of_element_located((By.ID, "goToDatabase"))
            )
            elem.click()
            print("S: we're in!")

            assert "No results found." not in self.web.page_source
        except TimeoutException as ex:
            self.take_screenshot()
            raise ex

    def detect_version(self):
        """ extracts the version in the lower right and compares it to a given version """
        while True:
            try:
                elem = self.web.find_element_by_id("currentVersion")
                enterprise_elem = self.web.find_element_by_class_name("logo.big")
                ret = {
                    'version': elem.text,
                    'enterprise': enterprise_elem.text
                }
                print("S: check_version (%s) (%s)" % (ret['version'], ret['enterprise']))
                if (len(ret['version']) > 0) and (len(ret['enterprise']) > 0):
                    return ret
                else:
                    print('S: retry version.')
                    continue
            except TimeoutException as ex:
                self.take_screenshot()
                raise ex

    def navbar_goto(self, tag):
        """ click on any of the items in the 'navbar' """
        count = 0
        print("S: navbar goto %s"% tag)
        while True:
            try:
                elem = self.web.find_element_by_id(tag)
                assert elem
                elem.click()
                self.web.find_element_by_class_name(tag + '-menu.active')
                print("S: goto current URL: " + self.web.current_url)
                if not self.web.current_url.endswith('#'+ tag):
                    # retry...
                    continue
                else:
                    return
            except NoSuchElementException:
                print('S: retrying to switch to ' + tag)
                time.sleep(1)
                count += 1
                if count %15 == 0:
                    print("S: reloading page!")
                    self.web.refresh()
                    time.sleep(1)
                continue
            except TimeoutException as ex:
                self.take_screenshot()
                raise ex

    def get_health_state(self):
        """ xtracts the health state in the upper right corner """
        try:
            elem = self.web.find_element_by_xpath('/html/body/div[2]/div/div[1]/div/ul[1]/li[2]/a[2]')
        except TimeoutException as ex:
            self.take_screenshot()
            raise ex
        # self.web.find_element_by_class_name("state health-state") WTF? Y not?
        print("S: Health state:" + elem.text)
        return elem.text

    def cluster_dashboard_get_count(self, timeout=10):
        """ extracts the coordinator / dbserver count from the 'cluster' page """
        ret = {}
        while True:
            try:
                elm = None
                elm_accepted = False
                while not elm_accepted:
                    elm = WebDriverWait(self.web, timeout).until(
                        EC.presence_of_element_located((By.XPATH, '//*[@id="clusterCoordinators"]'))
                    )
                    elm_accepted = len(elm.text) > 0
                # elm = self.web.find_element_by_xpath('//*[@id="clusterCoordinators"]')
                ret['coordinators'] = elm.text
                elm = self.web.find_element_by_xpath('//*[@id="clusterDBServers"]')
                ret['dbservers'] = elm.text
                print("S: health state: %s"% str(ret))
                return ret
            except StaleElementReferenceException:
                print('S: retrying after stale element')
                time.sleep(1)
                continue
            except TimeoutException as ex:
                self.take_screenshot()
                raise ex

    def cluster_get_nodes_table(self, timeout=20):
        """ extracts the table of coordinators / dbservers from the 'nodes' page """
        while True:
            try:
                table_coord_elm = WebDriverWait(self.web, timeout).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'pure-g.cluster-nodes.coords-nodes.pure-table.pure-table-body'))
                )
                table_dbsrv_elm = self.web.find_element_by_class_name('pure-g.cluster-nodes.dbs-nodes.pure-table.pure-table-body')
                column_names = ['name', 'url', 'version', 'date', 'state']
                table = []
                for elm in [table_coord_elm, table_dbsrv_elm]:
                    for table_row_num in [1, 2, 3]:
                        row ={}
                        table.append(row)
                        for table_column in [1, 2, 3, 4, 5]:
                            table_cell_elm = None
                            if table_column == 5:
                                table_cell_elm = elm.find_element_by_xpath('div[%d]/div[%d]/i'%(table_row_num, table_column))
                                row[column_names[table_column - 1]] = table_cell_elm.get_property('title')
                            else:
                                table_cell_elm = elm.find_element_by_xpath('div[%d]/div[%d]'%(table_row_num, table_column))
                                row[column_names[table_column - 1]] = table_cell_elm.text
                for row in table:
                    print('S: ' + str(row))
                return table
            except StaleElementReferenceException:
                print('S: retrying after stale element')
                time.sleep(1)
                continue
            except NoSuchElementException:
                print('S: retrying after no such element')
                time.sleep(1)
                continue
            except TimeoutException as ex:
                self.take_screenshot()
                raise ex

    def get_replication_screen(self, isLeader, timeout=20):
        """ fetch & parse the replication tab """
        retry_count = 0
        if isLeader:
            while True:
                try:
                    state_table = {}
                    table_elm = WebDriverWait(self.web, timeout).until(
                        EC.presence_of_element_located((By.CLASS_NAME, 'pure-g.cluster-values'))
                    )
                    # TODO: is it a bug that this id is info-mode-id?
                    #state_table['state'] = table_elm.find_element_by_xpath('div[1][@id="info-mode-id"]').text
                    #state_table['mode'] = table_elm.find_element_by_xpath('div[1][@id="info-mode-id"]').text
                    state_table['state'] = table_elm.find_element_by_xpath('div[1]/div[1]/div[1]').text
                    state_table['mode'] = table_elm.find_element_by_xpath('div[2]/div[1]/div[1]').text
                    state_table['role'] = table_elm.find_element_by_xpath('//*[@id="info-role-id"]').text
                    state_table['level'] = table_elm.find_element_by_xpath('//*[@id="info-level-id"]').text
                    state_table['health'] = table_elm.find_element_by_xpath('//*[@id="info-msg-id"]').text
                    state_table['tick'] = table_elm.find_element_by_xpath('//*[@id="logger-lastLogTick-id"]').text

                    follower_table = []
                    column_indices = [1,2,3,4,5]
                    more_lines = True
                    table_head = []
                    for i in column_indices:
                        table_head.append(self.web.find_element_by_xpath(
                            '//*[@id="repl-logger-clients"]//thead//th[%d]'%i).text)
                    follower_table.append(table_head)
                    count = 1
                    while more_lines:
                        try:
                            row_data = []
                            for i in column_indices:
                                cell = self.web.find_element_by_xpath(
                                    '//*[@id="repl-logger-clients"]//tr[%d]//td[%d]'%(
                                    count, i))
                                row_data.append(cell.text)
                            follower_table.append(row_data)
                        except Exception:
                            print('no more lines')
                            more_lines = False
                        count += 1
                    return {
                        'state_table': state_table,
                        'follower_table': follower_table,
                    }
                except NoSuchElementException:
                    print('S: retrying after element not found')
                    time.sleep(1)
                    retry_count += 1
                    continue
                except StaleElementReferenceException:
                    print('S: retrying after stale element')
                    time.sleep(1)
                    retry_count += 1
                    continue
                except TimeoutException as ex:
                    retry_count += 1
                    if retry_count < 5:
                        print('S: re-trying goto replication')
                        self.navbar_goto('replication')
                    elif retry_count > 20:
                        self.take_screenshot()
                        raise ex
                    else:
                        self.web.refresh()
                        time.sleep(1)
        else:
            while True:
                try:
                    state_table = {}
                    table_elm = WebDriverWait(self.web, timeout).until(
                        EC.presence_of_element_located((By.CLASS_NAME, 'pure-g.cluster-values'))
                    )
                    # TODO: is it a bug that this id is info-mode-id?
                    #state_table['state'] = table_elm.find_element_by_xpath('div[1][@id="info-mode-id"]').text
                    #state_table['mode'] = table_elm.find_element_by_xpath('div[1][@id="info-mode-id"]').text
                    state_table['state'] = table_elm.find_element_by_xpath('div[1]/div[1]/div[1]').text
                    state_table['mode'] = table_elm.find_element_by_xpath('div[2]/div[1]/div[1]').text
                    state_table['role'] = table_elm.find_element_by_xpath('//*[@id="info-role-id"]').text
                    state_table['level'] = table_elm.find_element_by_xpath('//*[@id="info-level-id"]').text
                    state_table['health'] = table_elm.find_element_by_xpath('//*[@id="info-msg-id"]').text
                    state_table['tick'] = table_elm.find_element_by_xpath('//*[@id="logger-lastLogTick-id"]').text

                    follower_table = []
                    column_indices = [1,2,3,4,5]
                    more_lines = True
                    th = []
                    for i in column_indices:
                        th.append(self.web.find_element_by_xpath(
                            '//*[@id="repl-follower-table"]//thead//th[%d]'%i).text)
                    follower_table.append(th)
                    count = 1
                    while more_lines:
                        try:
                            row_data = []
                            for i in column_indices:
                                cell = self.web.find_element_by_xpath(
                                    '//*[@id="repl-follower-table"]//tr[%d]//td[%d]'%(
                                    count, i))
                                row_data.append(cell.text)
                            follower_table.append(row_data)
                        except Exception:
                            print('no more lines')
                            more_lines = False
                        count += 1
                    return {
                        'state_table': state_table,
                        'follower_table': follower_table,
                    }
                except NoSuchElementException:
                    print('S: retrying after element not found')
                    time.sleep(1)
                    retry_count += 1
                    continue
                except StaleElementReferenceException:
                    print('S: retrying after stale element')
                    time.sleep(1)
                    retry_count += 1
                    continue
                except TimeoutException as ex:
                    retry_count += 1
                    if retry_count < 5:
                        print('S: re-trying goto replication')
                        self.navbar_goto('replication')
                    elif retry_count > 20:
                        self.take_screenshot()
                        raise ex
                    else:
                        self.web.refresh()
                        time.sleep(1)

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
