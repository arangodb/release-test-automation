#!/usr/bin/env python3
""" nodes page object """
import time

from beautifultable import BeautifulTable

from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium_ui_test.pages.navbar import NavigationBarPage

from reporting.reporting_utils import attach_table


class NodesPage(NavigationBarPage):
    """Class for Nodes page"""

    def cluster_get_nodes_table(self, timeout=20, cluster_nodes=5):
        """
        extract the table of coordinators / dbservers from the 'nodes' page
        """
        while True:
            table = self._get_nodes_table(timeout, cluster_nodes)
            try:
                return table
            except StaleElementReferenceException:
                self.progress("retrying after stale element")
                time.sleep(1)
                continue
            except NoSuchElementException:
                self.progress("retrying after no such element")
                time.sleep(1)
                continue
            except TimeoutException as ex:
                raise ex

    def _get_nodes_table(self, timeout, cluster_nodes):
        """repeatable inner func"""
        table_coord_elm = WebDriverWait(self.webdriver, timeout).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, "pure-g.cluster-nodes.coords-nodes.pure-table.pure-table-body")
            ),
            message="UI-Test: Cluster nodes table didn't become available on time %s" % timeout,
        )
        table_dbsrv_elm = self.by_class("pure-g.cluster-nodes.dbs-nodes.pure-table.pure-table-body")
        column_names = ["name", "url", "version", "date", "state"]
        table = []
        try:
            for elm in [table_coord_elm, table_dbsrv_elm]:
                for table_row_num in [1, 2, 3]:
                    row = {}
                    table.append(row)
                    for table_column in range(1, cluster_nodes):
                        table_cell_elm = None
                        if table_column == 5:
                            table_cell_elm = elm.find_element_by_xpath(
                                "div[%d]/div[%d]/i" % (table_row_num, table_column),
                                timeout=timeout)
                            try:
                                row[column_names[table_column - 1]] = table_cell_elm.get_attribute("data-original-title")
                            except NoSuchElementException:
                                row[column_names[table_column - 1]] = None
                            if row[column_names[table_column - 1]] is None:
                                row[column_names[table_column - 1]] = table_cell_elm.get_property("title")
                        else:
                            table_cell_elm = elm.find_element_by_xpath("div[%d]/div[%d]" % (table_row_num, table_column))
                            row[column_names[table_column - 1]] = table_cell_elm.text
        except Exception as ex:
            raise Exception(f"table incomplete, already got: {table}") from ex
        pretty_table = BeautifulTable(maxwidth=160)
        for row in table:
            pretty_table.rows.append([row["name"], row["url"], row["version"], row["date"], row["state"]])
        pretty_table.columns.header = ["Name", "URL", "Ver", "Date", "State"]
        self.progress("\n" + str(pretty_table))
        attach_table(pretty_table, "Cluster nodes table")
        return table
