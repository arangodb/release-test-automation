#!/usr/bin/env python3
"""selenium code for testing the replication page"""
import time
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium_ui_test.pages.navbar import NavigationBarPage


# can't circumvent long lines.. nAttr nLines
# pylint: disable=C0301 disable=R0902 disable=R0915 disable=R0914


class ReplicationPage(NavigationBarPage):
    """Class for Replication page"""

    REPL_TABLE_LOC = {
        # TODO: is it a bug that this id is info-mode-id?
        # 'state': 'div[1][@id="info-mode-id"]',
        # 'mode' : 'div[1][@id="info-mode-id"]',
        "state": "div[1]/div[1]/div[1]",
        "mode": "div[2]/div[1]/div[1]",
        "role": '//*[@id="info-role-id"]',
        "level": '//*[@id="info-level-id"]',
        "health": '//*[@id="info-msg-id"]',
        "tick": '//*[@id="logger-lastLogTick-id"]',
    }

    REPL_LF_TABLES = {
        "leader": ['//*[@id="repl-logger-clients"]//thead//th[%d]', '//*[@id="repl-logger-clients"]//tr[%d]//td[%d]'],
        "follower": ['//*[@id="repl-follower-table"]//thead//th[%d]', '//*[@id="repl-follower-table"]//tr[%d]//td[%d]'],
    }

    def __init__(self, driver):
        """Replication page initialization"""
        super().__init__(driver)

    def _get_repl_page(self, which, timeout=30):
        """parse the complete replication state table"""
        state_table = self.get_state_table(timeout)

        follower_table = []
        column_indices = [1, 2, 3, 4, 5]
        more_lines = True
        table_head = []
        for i in column_indices:
            table_head.append(self.webdriver.find_element_by_xpath(self.REPL_LF_TABLES[which][0] % i).text)
        follower_table.append(table_head)
        count = 1
        while more_lines:
            try:
                row_data = []
                for i in column_indices:
                    cell = self.webdriver.find_element_by_xpath(self.REPL_LF_TABLES[which][1] % (count, i))
                    row_data.append(cell.text)
                follower_table.append(row_data)
            except NoSuchElementException:
                print("UI-Test: no more lines.")
                more_lines = False
            count += 1
        return {
            "state_table": state_table,
            "follower_table": follower_table,
        }

    def get_state_table(self, timeout=30):
        """extract the replication state table"""
        table_elm = WebDriverWait(self.webdriver, timeout).until(
            EC.presence_of_element_located((By.CLASS_NAME, "pure-g.cluster-values")),
            message="UI-Test: replication state table didn't arive on time %s " % timeout,
        )
        state_table = {}
        for key in self.REPL_TABLE_LOC:
            state_table[key] = table_elm.find_element_by_xpath(self.REPL_TABLE_LOC[key]).text
        return state_table

    def get_replication_screen(self, is_leader, timeout=20):
        """fetch & parse the replication tab"""
        retry_count = 0
        while True:
            try:
                return self._get_repl_page("leader" if is_leader else "follower", timeout)
            except NoSuchElementException:
                self.progress("retrying after element not found")
                time.sleep(1)
                retry_count += 1
                continue
            except StaleElementReferenceException:
                self.progress("retrying after stale element")
                time.sleep(1)
                retry_count += 1
                continue
            except TimeoutException as ex:
                retry_count += 1
                if retry_count < 5:
                    self.progress("re-trying goto replication")
                    NavigationBarPage(self.webdriver).navbar_goto("replication")
                elif retry_count > 20:
                    raise ex
                else:
                    self.webdriver.refresh()
                    time.sleep(1)
