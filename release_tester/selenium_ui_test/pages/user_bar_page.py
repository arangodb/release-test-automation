#!/usr/bin/env python3
""" user bar page object """
from selenium_ui_test.pages.base_page import BasePage


class UserBarPage(BasePage):
    """Page object representing the user bar"""

    logout_button_id = "userLogoutIcon"

    def log_out(self):
        """click log out icon on the user bar and wait for"""
        logout_button_sitem = self.locator_finder_by_id(self.logout_button_id)
        logout_button_sitem.click()
        self.tprint("Logout from the current user\n")
        self.wait_for_ajax()

    def get_health_state(self):
        """extract the health state in the upper right corner"""
        elem = self.locator_finder_by_xpath("/html/body/div[2]/div/div[1]/div/ul[1]/li[2]/a[2]")
        # self.webdriver.find_element_by_class_name("state health-state") WTF? Y not?
        self.progress("Health state:" + elem.text)
        return elem.text
