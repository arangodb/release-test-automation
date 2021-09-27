from selenium.common.exceptions import NoSuchElementException
from selenium_ui_test.pages.base_page import BasePage
import time

from selenium_ui_test.pages.user_bar_page import UserBarPage


class NavigationBarPage(UserBarPage):
    """Page object representing the navigation bar"""

    click_twitter_link_id = "//*[@id='navigationBar']/div[2]/p[1]/a"
    click_slack_link_id = "//*[@id='navigationBar']/div[2]/p[2]/a"
    click_stackoverflow_link_id = "//*[@id='navigationBar']/div[2]/p[3]/a"
    click_google_group_link_id = "//*[@id='navigationBar']/div[2]/p[4]/a"

    def __init__(self, driver):
        super().__init__(driver)

    def navbar_goto(self, tag):
        """ click on any of the items in the 'navbar' """
        count = 0
        print("navbar goto %s" % tag)
        while True:
            try:
                elem = self.driver.find_element_by_id(tag)
                assert elem, "navbar goto failed?"
                elem.click()
                self.driver.find_element_by_class_name(tag + '-menu.active')
                print("goto current URL: " + self.driver.current_url)
                if not self.driver.current_url.endswith('#' + tag):
                    # retry...
                    continue
                return
            except NoSuchElementException:
                print('retrying to switch to ' + tag)
                time.sleep(1)
                count += 1
                if count % 15 == 0:
                    print("reloading page!")
                    self.driver.refresh()
                    time.sleep(1)
                continue
            # except TimeoutException as ex:
            # self.take_screenshot()
            #    raise ex

    def click_twitter_link(self):
        """Clicking on twitter link on dashboard"""
        click_twitter_link_sitem = self.locator_finder_by_text_xpath(self.click_twitter_link_id)
        title = self.switch_tab(
            click_twitter_link_sitem)  # this method will call switch tab and close tab
        expected_title = "arangodb (@arangodb) / Twitter"
        assert title in expected_title, f"Expected page title {expected_title} but got {title}"

    def click_slack_link(self):
        """Clicking on twitter link on dashboard"""
        click_slack_link_sitem = self.locator_finder_by_text_xpath(self.click_slack_link_id)
        title = self.switch_tab(click_slack_link_sitem)
        expected_title = 'Join ArangoDB Community on Slack!'
        assert title in expected_title, f"Expected page title {expected_title} but got {title}"

    def click_stackoverflow_link(self):
        """Clicking on stack overflow link on dashboard"""
        click_stackoverflow_link_sitem = self.locator_finder_by_text_xpath(
            self.click_stackoverflow_link_id)
        title = self.switch_tab(click_stackoverflow_link_sitem)
        expected_title = "Newest 'arangodb' Questions - Stack Overflow"
        assert title in expected_title, f"Expected page title {expected_title} but got {title}"

    def click_google_group_link(self):
        """Clicking on Google group link on dashboard"""
        click_google_group_link_sitem = self.locator_finder_by_xpath(
            self.click_google_group_link_id)
        title = self.switch_tab(click_google_group_link_sitem)
        expected_title = "ArangoDB - Google Groups"
        assert title in expected_title, f"Expected page title {expected_title} but got {title}"
