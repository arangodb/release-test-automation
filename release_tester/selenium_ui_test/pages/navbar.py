from selenium.common.exceptions import NoSuchElementException
from selenium_ui_test.pages.base_page import BasePage
import time


class NavigationBarPage(BasePage):
    """Page object representing the navigation bar"""

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