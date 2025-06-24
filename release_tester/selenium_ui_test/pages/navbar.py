#!/usr/bin/env python3
""" navigation bar page object """
import time
from selenium_ui_test.pages.user_bar_page import UserBarPage
from selenium.common.exceptions import TimeoutException

# wtf navbar?
# pylint: disable=blacklisted-name


class NavigationBarPage(UserBarPage):
    """Page object representing the navigation bar"""

    # click_twitter_link_id = "//*[@id='navigationBar']/div[2]/p[1]/a"
    # click_slack_link_id = "//*[@id='navigationBar']/div[2]/p[2]/a"
    # click_stackoverflow_link_id = "//*[@id='navigationBar']/div[2]/p[3]/a"
    # click_google_group_link_id = "//*[@id='navigationBar']/div[2]/p[4]/a"
    navbar_id = "navigationBar"

    def navbar_goto(self, tag):
        """click on any of the items in the 'navbar'"""
        self.wait_for_ajax()
        self.locator_finder_by_id(self.navbar_id)
        item = self.locator_finder_by_id(tag)
        item.click()
        self.wait_for_ajax()

    def detect_version(self):
        """
        extracts the version in the lower right and
         compares it to a given version
        """
        count = 0
        while True:
            try:
                elem = self.locator_finder_by_id("currentVersion")
                enterprise_elem = self.locator_finder_by_class("logo.big")
                ret = {"version": elem.text, "enterprise": enterprise_elem.text}
                self.progress("check_version (%s) (%s)" % (ret["version"], ret["enterprise"]))
                if (len(ret["version"]) > 0) and (len(ret["enterprise"]) > 0):
                    return ret
                self.progress("retry version.")
                time.sleep(1)
                if count > 200:
                    raise TimeoutException("cannot detect version, found: %s " % str(ret))
                count += 1
            except TimeoutException as ex:
                raise ex
