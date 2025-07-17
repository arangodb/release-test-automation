#!/usr/bin/env python3
"""selenium code for testing the replication page"""
import time
from collections import namedtuple
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium_ui_test.pages.navbar import NavigationBarPage


# can't circumvent long lines.. nAttr nLines
# pylint: disable=line-too-long disable=too-many-instance-attributes disable=too-many-statements disable=too-many-locals


class ReplicationPage(NavigationBarPage):
    """Class for Replication page"""
    # pylint: disable=too-many-instance-attributes disable=too-many-public-methods
    def __init__(self, webdriver, cfg, video_start_time):
        super().__init__(webdriver, cfg, video_start_time)
        self.page_name = "replication"
        # enabling external page locators for replication page
        elements_dict = dict(self.elements_data[self.page_name])
        Elements = namedtuple("Elements", list(elements_dict.keys())) # pylint: disable=C0103
        self.elements = Elements(*list(elements_dict.values()))
        self.REPL_TABLE_LOC = {
            'state': self.elements.txt_state,
            'mode': self.elements.txt_mode,
            "role": self.elements.txt_role,
            "level": self.elements.txt_level,
            "health": self.elements.txt_health,
            "tick": self.elements.txt_tick,
        }
        self.REPL_LF_TABLES = {
            "leader": [self.elements.table_header_leader, self.elements.table_cell_leader],
            "follower": [self.elements.table_header_follower, self.elements.table_cell_follower],
        }

    def _get_repl_page(self, which, timeout=30):
        """parse the complete replication state table"""
        state_table = self.get_state_table(timeout)

        follower_table = []
        column_indices = [1, 2, 3, 4, 5]
        more_lines = True
        table_head = []
        for i in column_indices:
            table_head.append(self.webdriver.find_element(By.XPATH, self.REPL_LF_TABLES[which][0] % i).text)
        follower_table.append(table_head)
        count = 1
        while more_lines:
            try:
                row_data = []
                for i in column_indices:
                    cell = self.webdriver.find_element(By.XPATH, self.REPL_LF_TABLES[which][1] % (count, i))
                    row_data.append(cell.text)
                follower_table.append(row_data)
            except NoSuchElementException:
                self.tprint("UI-Test: no more lines.")
                more_lines = False
            count += 1
        return {
            "state_table": state_table,
            "follower_table": follower_table,
        }

    def get_state_table(self, timeout=30):
        """extract the replication state table"""
        table_elm = WebDriverWait(self.webdriver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, self.elements.table_replication_state)),
            message="UI-Test: replication state table didn't arrive on time %s " % timeout,
        )
        state_table = {}
        for key in self.REPL_TABLE_LOC.items():
            state_table[key[0]] = table_elm.find_element(By.CSS_SELECTOR, key[1]).text
        return state_table

    def get_replication_screen(self, is_leader, timeout=20):
        """fetch & parse the replication tab"""
        retry_count = 0
        while True:
            try:
                return self._get_repl_page("leader" if is_leader else "follower", timeout)
            except StaleElementReferenceException:
                self.progress("retrying after stale element")
                time.sleep(1)
                retry_count += 1
                continue
            except TimeoutException as ex:
                retry_count += 1
                if retry_count < 5:
                    self.progress("re-trying goto replication")
                    self.navbar_goto("replication")
                elif retry_count > 20:
                    raise ex
                else:
                    self.webdriver.refresh()
                    time.sleep(1)

    def get_replication_information(self):
        """checking replication information"""
        self.tprint("checking replication tab is available\n")
        replication_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.tab_replication)
        replication = replication_sitem.text
        time.sleep(1)
        assert replication == "REPLICATION", f"Expected REPLICATION but got {replication}"

        self.tprint("checking replication mode\n")
        replication_mode_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.txt_mode)
        replication_mode = replication_mode_sitem.text
        time.sleep(1)
        assert replication_mode == "Active Failover", f"Expected Active Failover but got {replication_mode}"

        ip_list = ["tcp://localhost:9529", "tcp://localhost:9629", "tcp://localhost:9729"]

        self.tprint("checking leader id\n")
        leader_id_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.txt_nodes_leader)
        leader = leader_id_sitem.text
        time.sleep(1)
        assert leader in ip_list, "Error occurred, Couldn't find expected leader ip"

        self.tprint("checking follower id\n")
        follower_id_sitem = self.locator_finder_by_xpath_or_css_selector(self.elements.txt_nodes_follower)
        follower = follower_id_sitem.text
        time.sleep(1)
        assert follower in ip_list, "Error occurred, Couldn't find expected follower ip"
