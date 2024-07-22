#!/usr/bin/python3
"""page module for the login screen"""
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait

from selenium_ui_test.pages.base_page import BasePage
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException

# can't circumvent long lines..
# pylint: disable=line-too-long


class LoginPage(BasePage):
    """Login class for selenium UI testing"""

    def __init__(self, driver, cfg, video_start_time):
        """Login page initialization"""
        super().__init__(driver, cfg, video_start_time)
        self.username_textbox_id = "loginUsername"
        self.password_textbox_id = "loginPassword"
        self.login_button_id = "submitLogin"
        self.database_select = """//select[@id="loginDatabase"]"""
        # self.select_db_opt_id = "loginDatabase"
        self.select_db_btn_id = "goToDatabase"
        self.logout_button_id = "userLogoutIcon"

    def _login_wait_for_screen(self):
        """wait for the browser to show the login screen"""
        count = 0
        while True:
            count += 1
            elem = WebDriverWait(self.webdriver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "html")), message="UI-Test: page didn't load after 10s"
            )
            data = elem.text
            if len(data) < 0:
                self.progress("ArangoDB Web Interface not loaded yet, retrying")
                time.sleep(2)
            if count == 10:
                if elem is None:
                    self.progress(" locator has not been found.")
                    self.webdriver.refresh()
                    time.sleep(5)
                else:
                    assert "ArangoDB Web Interface" in self.webdriver.title, "webif title not found"
                    break
        return True

    def _login_fill_username(self, user, max_retries=3):
        """Fill in the username column with improved resilience."""
        for attempt in range(max_retries):
            try:
                self.webdriver.refresh()
                logname = self.locator_finder_by_id("loginUsername", 10, 2)

                logname.click()
                logname.clear()
                logname.send_keys(user)
                
                # Verify if the input was successful
                if logname.get_attribute("value") == user:
                    return True
                else:
                    self.progress(f"Attempt {attempt + 1}: Username not set correctly, retrying...")
            except (TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
                self.progress(f"Attempt {attempt + 1}: Exception occurred - {e}, retrying...")
            
            # Wait a bit before retrying
            time.sleep(2)
        
        # If all attempts fail
        self.progress("Failed to fill in the username after multiple attempts.")
        return False

    def _login_fill_passvoid(self, passvoid):
        """fill the passvoid and click login"""
        while True:
            passvoid_elm = self.locator_finder_by_id("loginPassword")
            txt = passvoid_elm.text
            self.tprint("UI-Test: xxxx [" + txt + "]")
            if len(txt) > 0:
                self.progress("something was in the passvoid field. retrying. " + txt)
                time.sleep(2)
                continue
            passvoid_elm.click()
            passvoid_elm.clear()
            passvoid_elm.send_keys(passvoid)
            self.progress("logging in")
            passvoid_elm.send_keys(Keys.RETURN)
            break
        return True

    def _login_choose_database(self, database_name):
        """choose the database from the second login screen"""
        select = Select(self.locator_finder_by_xpath(self.database_select))
        select.select_by_visible_text(database_name)
        return True
    
    def login_webif(self, user, passvoid, database="_system", recurse=0):
        """log into an arangodb webinterface"""
        self.tprint(f"Logging {user} into {database} with passvoid {passvoid}")
        if recurse > 10:
            raise Exception("UI-Test: 10 successless login attempts")
        self._login_wait_for_screen()
        if not self._login_fill_username(user):
            return False
        if not self._login_fill_passvoid(passvoid):
            return False
        if not self._login_choose_database(database):
            return False
        self.locator_finder_by_id(self.select_db_btn_id).click()
        self.progress("we're in!")
        self.wait_for_ajax()

        assert "No results found." not in self.webdriver.page_source, "no results found?"
        return False

    def log_out(self):
        """click log out icon on the user bar and wait for"""
        logout_button_sitem = self.locator_finder_by_id(self.logout_button_id)
        logout_button_sitem.click()
        self.tprint("Logout from the current user\n")
        self.wait_for_ajax()
