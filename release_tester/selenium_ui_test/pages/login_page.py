#!/usr/bin/env python
"""
login to the UI
"""
import time

from selenium_ui_test.pages.base_page import BasePage

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    StaleElementReferenceException
)

# can't circumvent long lines..
# pylint: disable=C0301

class LoginPage(BasePage):
    """Login class for selenium UI testing"""

    def __init__(self, driver):
        """Login page initialization"""
        super().__init__(driver)
        self.username_textbox_id = "loginUsername"
        self.password_textbox_id = "loginPassword"
        self.login_button_id = "submitLogin"
        self.select_db_opt_id = "loginDatabase"
        self.select_db_btn_id = "goToDatabase"

    def progress(self, arg):
        """ state print todo """
        print(arg)

    def _login_wait_for_screen(self):
        """ wait for the browser to show the login screen """
        count = 0
        while True:
            count += 1
            elem = WebDriverWait(self.driver, 10).until(
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
                    self.progress(" locator has not been found.")
                    self.driver.refresh()
                    time.sleep(5)
                else:
                    assert "ArangoDB Web Interface" in self.driver.title, \
                        "webif title not found"
                    break
        return True

    def _login_fill_username(self, cfg, user, passvoid, database, recurse=0):
        """ fill in the username column """
        try:
            logname = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "loginUsername")),
                message="UI-Test: loginUsername didn't become clickeable on time. 10s"
            )
            logname.click()
            logname.clear()
            logname.send_keys(user)

            if logname is None:
                self.progress("locator loginUsername has not found.")
                return False

        except StaleElementReferenceException as ex:
            self.progress("stale element, force reloading with sleep: " +
                          str(ex))
            self.driver.refresh()
            time.sleep(5)
            return self.login_webif(cfg,
                                    user,
                                    passvoid,
                                    database, 
                                    recurse + 1)
        return True

    def _login_fill_passvoid(self, passvoid):
        """ fill the passvoid and click login """
        while True:
            passvoid_elm = self.driver.find_element_by_id("loginPassword")
            txt = passvoid_elm.text
            print("UI-Test: xxxx [" + txt + "]")
            if len(txt) > 0:
                self.progress(
                    'something was in the passvoid field. retrying. ' +
                    txt)
                time.sleep(2)
                continue
            passvoid_elm.click()
            passvoid_elm.clear()
            passvoid_elm.send_keys(passvoid)
            self.progress("logging in")
            passvoid_elm.send_keys(Keys.RETURN)
            break
        return True

    def _login_choose_database(self, cfg, user, passvoid, database, recurse=0):
        """ choose the database from the second login screen """
        count = 0
        while True:
            count += 1
            elem = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.ID, "loginDatabase")),
                message="UI-Test: loginDatabase didn't become clickeable on time 15s"
            )
            txt = elem.text
            if txt.find(database) < 0:
                self.progress(database + ' not found in ' +
                              txt +
                              ' ; retrying!')
                if count == 10:
                    self.progress('refreshing webpage and retrying...')
                    self.driver.refresh()
                    time.sleep(5)
                    return self.login_webif(cfg,
                                            user,
                                            passvoid,
                                            database,
                                            recurse + 1)
                time.sleep(2)
            else:
                break
        elem = WebDriverWait(self.driver, 15).until(
            EC.element_to_be_clickable((By.ID, "goToDatabase")),
            message="UI-Test: choosing database didn't become clickeable on time 15s"
        )
        elem.click()
        return True

    def login_webif(self, cfg, user, passvoid, database="_system", recurse=0):
        """ log into an arangodb webinterface """
        print("Logging %s into %s with passvoid %s" %(user, database, passvoid))
        if recurse > 10:
            raise Exception("UI-Test: 10 successless login attempts")
        self._login_wait_for_screen()
        if not self._login_fill_username(cfg, user, passvoid, database, recurse):
            return False
        if not self._login_fill_passvoid(passvoid):
            return False
        if not self._login_choose_database(cfg, user, passvoid, database, recurse):
            return False
        self.progress("we're in!")
        self.wait_for_ajax()

        assert "No results found." not in self.driver.page_source, \
            "no results found?"
        return False
