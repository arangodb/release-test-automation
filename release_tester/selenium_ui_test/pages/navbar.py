#!/usr/bin/env python3
""" navigation bar page object """
import time
from selenium_ui_test.pages.user_bar_page import UserBarPage
from selenium.common.exceptions import TimeoutException
import semver

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

    def click_twitter_link(self):
        """Clicking on twitter link on dashboard"""
        if self.current_package_version() >= semver.VersionInfo.parse("3.11.100"):
            click_twitter_link_id = '//*[@id="navigationBar"]/div/p[1]/a'
        else:
            click_twitter_link_id = "//*[@id='navigationBar']/div[2]/p[1]/a"

        click_twitter_link_id_sitem = self.locator_finder_by_xpath(
            click_twitter_link_id
        )
        
        title = self.switch_tab(click_twitter_link_id_sitem)  # This method will call switch tab and close tab

        # List of valid expected titles
        expected_titles = [
            "ArangoDB (@arangodb) / X",
            "Profile / X"
        ]

        # Check if the actual title is in the list of expected titles
        assert (
            title in expected_titles
        ), f"Expected page title to be one of {expected_titles} but got {title}"


    def click_slack_link(self):
        """Clicking on twitter link on dashboard"""
        if self.current_package_version() >= semver.VersionInfo.parse("3.11.100"):
            click_slack_link_id = '//*[@id="navigationBar"]/div/p[2]/a'
        else:
            click_slack_link_id = "//*[@id='navigationBar']/div[2]/p[2]/a"

        click_slack_link_id_sitem = self.locator_finder_by_xpath(click_slack_link_id)
        title = self.switch_tab(click_slack_link_id_sitem)
        expected_title = "Join ArangoDB Community on Slack!"
        assert (
            title in expected_title
        ), f"Expected page title {expected_title} but got {title}"

    def click_stackoverflow_link(self):
        """Clicking on stack overflow link on dashboard"""
        if self.current_package_version() >= semver.VersionInfo.parse("3.11.100"):
            click_stackoverflow_link_id = '//*[@id="navigationBar"]/div/p[3]/a'
        else:
            click_stackoverflow_link_id = "//*[@id='navigationBar']/div[2]/p[3]/a"

        click_stackoverflow_link_id_sitem = self.locator_finder_by_xpath(
            click_stackoverflow_link_id
        )
        title = self.switch_tab(click_stackoverflow_link_id_sitem)
        expected_title = "Newest 'arangodb' Questions - Stack Overflow"
        assert (
            title in expected_title
        ), f"Expected page title {expected_title} but got {title}"

    def click_google_group_link(self):
        """Clicking on Google group link on dashboard"""
        if self.current_package_version() >= semver.VersionInfo.parse("3.11.100"):
            click_google_group_link_id = '//*[@id="navigationBar"]/div/p[4]/a'
        else:
            click_google_group_link_id = "//*[@id='navigationBar']/div[2]/p[4]/a"

        click_google_group_link_id_sitem = self.locator_finder_by_xpath(
            click_google_group_link_id
        )
        title = self.switch_tab(click_google_group_link_id_sitem)
        expected_title = "ArangoDB - Google Groups"
        assert (
            title in expected_title
        ), f"Expected page title {expected_title} but got {title}"


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
                    raise TimeoutException("canot detect version, found: %s " % str(ret))
                count += 1
            except TimeoutException as ex:
                raise ex
