from selenium.common.exceptions import NoSuchElementException
from selenium_ui_test.pages.base_page import BasePage
import time


class UserBarPage(BasePage):
    """Page object representing the user bar"""

    logout_button_id = "userLogoutIcon"

    def __init__(self, driver):
        super().__init__(driver)

    def log_out(self):
        """ click log out icon on the user bar and wait for"""
        logout_button_sitem = self.locator_finder_by_text_id(self.logout_button_id)
        logout_button_sitem.click()
        print("Logout from the current user\n")
        self.wait_for_ajax()