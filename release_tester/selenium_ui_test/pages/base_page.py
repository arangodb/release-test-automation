#!/usr/bin/env python3
""" base page object """
import time
import traceback

import tools.interact as ti
# from selenium import webdriver

from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By as BY
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import (
    # InvalidSessionIdException,
    # StaleElementReferenceException,
    TimeoutException,
    # NoSuchElementException,
)
import semver


# from webdriver_manager.chrome import ChromeDriverManager
# from webdriver_manager.firefox import GeckoDriverManager
# from webdriver_manager.microsoft import EdgeChromiumDriverManager
# from webdriver_manager.utils import ChromeType

# can't circumvent long lines.. nAttr nLines
# pylint: disable=line-too-long disable=too-many-instance-attributes disable=too-many-public-methods disable=too-many-statements


class BasePage:
    """Base class for page objects"""

    driver: WebDriver

    def __init__(self, webdriver, cfg):
        """base initialization"""
        self.webdriver = webdriver
        self.cfg = cfg
        self.query_execution_area = '//*[@id="aqlEditor"]'
        self.bindvalues_area = '//*[@id="bindParamAceEditor"]'
        self.locator = None
        self.select = None
        self.current = None

    @classmethod
    def set_up_class(cls):
        """This method will be used for the basic driver setup"""

        # browser_list = ['1 = chrome', '2 = firefox', '3 = edge', '4 = chromium']
        # print(*browser_list, sep="\n")
        # cls.browser_name = None

        # while cls.browser_name not in {1, 2, 3, 4}:
        #     cls.browser_name = int(input('Choose your browser: '))
        #
        #     if cls.browser_name == 1:
        #         print("You have chosen: Chrome browser \n")
        #         cls.driver = webdriver.Chrome(ChromeDriverManager().install())
        #     elif cls.browser_name == 2:
        #         print("You have chosen: Firefox browser \n")
        #
        #         # This preference will disappear download bar for firefox
        #         profile = webdriver.FirefoxProfile()
        #         profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/json, text/csv")  # mime
        #         profile.set_preference("browser.download.manager.showWhenStarting", False)
        #         profile.set_preference("browser.download.dir", "C:\\Users\\rearf\\Downloads")
        #         profile.set_preference("browser.download.folderList", 2)
        #         profile.set_preference("pdfjs.disabled", True)
        #
        #         cls.driver = webdriver.Firefox(executable_path=GeckoDriverManager().install(), firefox_profile=profile)
        #
        #     elif cls.browser_name == 3:
        #         print("You have chosen: Edge browser \n")
        #         cls.driver = webdriver.Edge(EdgeChromiumDriverManager().install())
        #     elif cls.browser_name == 4:
        #         print("You have chosen: Chromium browser \n")
        #         cls.driver = webdriver.Chrome(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
        #     else:
        #         print("Kindly provide a specific browser name from the list. \n")

        # cls.driver.set_window_size(1250, 1000)  # custom window size
        # cls.driver.get("http://127.0.0.1:8529/_db/_system/_admin/aardvark/index.html#login")

    @classmethod
    def tear_down(cls):
        """This method will be used for teardown the driver instance"""
        time.sleep(5)
        # cls.driver.close()
        print("\n--------Now Quiting--------\n")
        # cls.driver.quit()

    def switch_to_iframe(self, iframe_id):
        """This method will switch to IFrame window"""
        self.webdriver.switch_to.frame(self.webdriver.find_element(BY.XPATH, iframe_id))
        time.sleep(1)

    def switch_back_to_origin_window(self):
        """This method will switch back to origin window"""
        self.webdriver.switch_to.default_content()
        time.sleep(1)

    def wait_for_ajax(self):
        """wait for jquery to finish..."""
        wait = WebDriverWait(self.webdriver, 15)
        try:
            wait.until(lambda driver: driver.execute_script("return (typeof jQuery !== 'undefined') && jQuery.active") == 0)
            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
        except TimeoutException:
            pass

    def clear_all_text(self, locator=None):
        """This method will select all text and clean it"""
        print("Cleaning input field \n")
        if locator is not None:
            locator = self.locator_finder_by_xpath(locator)

        print("Cleaning input field \n")
        actions = ActionChains(self.webdriver)
        actions.click(locator)
        actions.key_down(Keys.CONTROL)
        actions.send_keys("a")
        actions.send_keys(Keys.DELETE)
        actions.key_up(Keys.CONTROL)
        actions.perform()

    def check_ui_responsiveness(self):
        """Checking LOG tab causes unresponsive UI (found in 3.8 server package"""
        print("\n")
        print("Clicking on Log tab \n")
        log = "logs"
        log = self.locator_finder_by_id(log)
        log.click()

        print("Try to tap on Log Level drop down button \n")
        log_level = "logLevelSelection"
        log_level = self.locator_finder_by_id(log_level)
        log_level.click()

        time.sleep(3)

        print("Close the Log Level button \n")
        log_level01 = "closeFilter"
        log_level01 = self.locator_finder_by_id(log_level01)
        log_level01.click()

        print("Quickly tap on to Collection Tab")
        collection = "collections"
        collection = self.locator_finder_by_id(collection)
        collection.click()

        print("Waiting for few seconds \n")
        time.sleep(3)

        print("Return back to Log tab again \n")
        log01 = "logs"
        log01 = self.locator_finder_by_id(log01)
        log01.click()

        print("Trying to tap on Log Level once again \n")
        try:
            log_level = "logLevelSelection"
            log_level = self.locator_finder_by_id(log_level)
            log_level.click()
            assert "Level" in log_level.text, "********UI become unresponsive******"
            if log_level.text == "Level":
                print("Ui is responsive and working as usual\n")
        except TimeoutException:
            print("********Dashboard responsiveness check failed********")

        time.sleep(2)
        print("UI responsiveness test completed \n")
        print("Back to Dashboard again \n")
        self.webdriver.refresh()
        dash = "dashboard"
        dash = self.locator_finder_by_id(dash)
        dash.click()
        time.sleep(2)

    def select_query_execution_area(self):
        """This method will select the query execution area"""
        try:
            query_sitem = self.locator_finder_by_xpath(self.query_execution_area)
            query_sitem.click()
            time.sleep(2)
        except TimeoutException:
            print("Can't find the query execution area \n")

    def select_bindvalue_json_area(self):
        """This method will select the query execution area"""
        try:
            query_sitem = self.locator_finder_by_xpath(self.bindvalues_area)
            query_sitem.click()
            time.sleep(2)
        except TimeoutException:
            print("Can't find the query execution area \n")

    def query_execution_btn(self):
        """Clicking execute query button"""
        execute = "executeQuery"
        execute = self.locator_finder_by_id(execute)
        execute.click()
        time.sleep(2)

    def send_key_action(self, key):
        """This method will send dummy data to the textfield as necessary"""
        actions = ActionChains(self.webdriver)
        actions.send_keys(key)
        actions.perform()

    def clear_text_field(self, locator):
        """This method will be used for clear all the text in single text field if .clear() does not work"""
        locator.send_keys(Keys.CONTROL + "a", Keys.BACKSPACE)

        if self.locator is None:
            raise Exception("UI-Test: ", locator, " locator was not found.")
        return self.locator

    def switch_tab(self, locator):
        """This method will change tab and close it and finally return to origin tab"""
        print("switching tab method \n")
        self.locator = locator
        self.locator.send_keys(Keys.CONTROL, Keys.RETURN)  # this will open new tab on top of current
        self.webdriver.switch_to.window(self.webdriver.window_handles[1])  # switch to new tab according to index value
        title = self.webdriver.title
        print("Current page title: ", title, "\n")
        time.sleep(15)
        self.webdriver.close()  # closes the browser active window
        self.webdriver.switch_to.window(self.webdriver.window_handles[0])
        return title

    def check_version_is_newer(self, compare_version):
        """ check whether the version in the ui is the expected """
        ui_version_str = self.locator_finder_by_id("currentVersion").text
        print("Package Version: ", ui_version_str)
        ui_version = semver.VersionInfo.parse(ui_version_str)
        compare_version = semver.VersionInfo.parse(compare_version)
        return ui_version >= compare_version

    def current_package_version(self):
        """checking current package version from the dashboard"""
        package_version = "currentVersion"
        package_version = self.locator_finder_by_id(package_version).text
        print("Package Version: ", package_version)
        return semver.VersionInfo.parse(package_version)

    def current_user(self):
        """get the currently logged in user from the page upper middle"""
        self.wait_for_ajax()
        userbar_sitem = self.locator_finder_by_id("userBar")
        return str(userbar_sitem.find_element(BY.CLASS_NAME, "toggle").text)

    def current_database(self):
        """get the currently used database from the page upper middle"""
        self.wait_for_ajax()
        database_sitem = self.locator_finder_by_id("dbStatus")
        return database_sitem.find_element(BY.CLASS_NAME, "state").text

    def scroll(self, down=0):
        """This method will be used to scroll up and down to any page"""
        # TODO: do this instead of sleep?
        # https://sqa.stackexchange.com/questions/35589/how-to-wait-for-javascript-scroll-action-to-finish-in-selenium
        if down == 1:
            self.webdriver.find_element(BY.TAG_NAME, "html").send_keys(Keys.END)
            print("")
            time.sleep(3)
        else:
            time.sleep(5)
            self.webdriver.find_element(BY.TAG_NAME, "html").send_keys(Keys.HOME)
        # self.webdriver.execute_script("window.scrollTo(0,500)")

    def locator_finder_by_idx(self, locator_name, timeout=10):
        """This method will used for finding all the locators by their id"""
        print(locator_name)
        self.locator = WebDriverWait(self.webdriver, timeout).until(
            EC.presence_of_element_located((BY.ID, locator_name)),
            message="UI-Test: " + locator_name + " locator was not found.",
        )
        if self.locator is None:
            raise Exception(locator_name, " locator was not found.")
        return self.locator

    def locator_finder_by_id(self, locator_name, timeout=10):
        """This method will used for finding all the locators by their id"""
        print(locator_name)
        self.locator = WebDriverWait(self.webdriver, timeout).until(
            EC.element_to_be_clickable((BY.ID, locator_name)),
            message="UI-Test: " + str(locator_name) + " locator was not found.",
        )
        if self.locator is None:
            raise Exception(str(locator_name), " locator was not found.")
        return self.locator

    def locator_finder_by_xpath(self, locator_name, timeout=10, expec_fail=False):
        """This method will used for finding all the locators by their xpath"""
        try:
            self.locator = WebDriverWait(self.webdriver, timeout).until(
                EC.element_to_be_clickable((BY.XPATH, locator_name)),
                message="UI-Test: " + locator_name + " locator was not found.",
            )
        except Exception as ex:
            if expec_fail:
                raise ex
            ti.prompt_user(self.cfg,
                           "ERROR " * 10 +
                           "\nError while wating for web element:\n" +
                           str(ex) + "\n" +
                           "".join(traceback.format_stack(ex.__traceback__.tb_frame))
                           )
            raise ex
        if self.locator is None:
            raise Exception("UI-Test: ", locator_name, " locator was not found.")
        return self.locator
    
    def locator_finder_by_link_text(self, locator_name):
        """This method will be used for finding all the locators by their xpath"""
        self.locator = WebDriverWait(self.webdriver, 10).until(
            EC.element_to_be_clickable((BY.LINK_TEXT, locator_name))
        )
        if self.locator is None:
            print("UI-Test: ", locator_name, " locator has not found.")
        else:
            return self.locator

    def locator_finder_by_select(self, locator_name, value):
        """This method will used for finding all the locators in drop down menu with options"""
        self.select = Select(self.webdriver.find_element(BY.ID, locator_name))
        self.select.select_by_index(value)
        if self.select is None:
            raise Exception("UI-Test: ", locator_name, " locator was not found.")
        return self.select

    def select_value(self, locator_name, value):
        """Select given value in drop down menu"""
        self.select = Select(self.webdriver.find_element(BY.ID, locator_name))
        if self.select is None:
            raise Exception("UI-Test: ", locator_name, " locator was not found.")
        self.select.select_by_value(value)

    def locator_finder_by_select_using_xpath(self, locator_name, value):
        """This method will used for finding all the locators in drop down menu with options using xpath"""
        self.select = Select(self.webdriver.find_element(BY.XPATH, locator_name))
        self.select.select_by_index(value)
        if self.select is None:
            print("UI-Test: ", locator_name, " locator has not found.")
        return self.select

    def locator_finder_by_class(self, locator_name):
        """This method will used for finding all the locators by their id"""
        self.locator = WebDriverWait(self.webdriver, 10).until(
            EC.element_to_be_clickable((BY.CLASS_NAME, locator_name))
        )
        if self.locator is None:
            print(locator_name, " locator has not found.")
        return self.locator

    def locator_finder_by_hover_item_id(self, locator):
        """This method will used for finding all the locators and hover the mouse by id"""
        item = self.webdriver.find_element(BY.ID, locator)
        action = ActionChains(self.webdriver)
        action.move_to_element(item).click().perform()
        time.sleep(1)
        return action

    def zoom(self):
        """This method will used for zoom in/out on any perspective window"""
        print("zooming in now\n")
        self.webdriver.execute_script("document.body.style.zoom='80%'")

    def locator_finder_by_hover_item(self, locator):
        """This method will used for finding all the locators and hover the mouse by xpath"""
        item = self.webdriver.find_element(BY.XPATH, locator)
        action = ActionChains(self.webdriver)
        action.move_to_element(item).click().perform()
        time.sleep(1)
        return action

    def locator_finder_by_css_selectors(self, locator_name, timeout=10):
        """This method will used for finding all the locators text using CSS Selector"""
        self.locator = WebDriverWait(self.webdriver, timeout).until(
            EC.element_to_be_clickable((BY.CSS_SELECTOR, locator_name)),
            message="UI-Test: " + locator_name + " locator was not found.",
        )
        self.locator = self.locator.text
        if self.locator is None:
            raise Exception("UI-Test: ", locator_name, " locator was not found.")
        return self.locator

    # pylint: disable=too-many-arguments
    def check_expected_error_messages_for_analyzer(
        self, error_input, print_statement, error_message, locators_id, error_message_id
    ):
        """This method will take three lists and check for expected error condition against user's inputs"""
        i = 0
        # looping through all the error scenario for test
        # print('len: ', len(name_error))
        while i < len(error_input):  # error_input list will hold a list of error inputs from the users
            print(print_statement[i])  # print_statement will hold a list of all general print statements for the test
            locators = locators_id  # locator id of the input placeholder where testing will take place
            # if div_id is not None:
            locator_sitem = self.locator_finder_by_xpath(self, locators)
            locator_sitem.click()
            locator_sitem.clear()
            locator_sitem.send_keys(error_input[i])
            time.sleep(2)
            locator_sitem.send_keys(Keys.TAB)
            time.sleep(2)
            
            create_btn = '//*[@id="modal-content-add-analyzer"]/div[3]/button[2]'
            create_btn_sitem = self.locator_finder_by_xpath(self, create_btn)
            create_btn_sitem.click()
            time.sleep(2)

            try:
                # placeholder's error message id
                error_sitem = BasePage.locator_finder_by_xpath(self, error_message_id).text
                print("Expected error found: ", error_sitem, "\n")
                time.sleep(2)
                error_sitem = self.locator_finder_by_xpath(error_message_id).text
                # error_message list will hold expected error messages
                assert (
                    error_sitem == error_message[i]
                ), f"FAIL: Expected error message {error_message[i]} but got {error_sitem}"

                print("x" * (len(error_sitem) + 29))
                print("OK: Expected error found: ", error_sitem)
                print("x" * (len(error_sitem) + 29), "\n")
                time.sleep(2)

            except TimeoutException as ex:
                raise Exception("*****-->Error occurred. Manual inspection required<--***** \n") from ex

            i = i + 1

    # pylint: disable=too-many-arguments
    def check_expected_error_messages_for_database(
        self, error_input, print_statement, error_message, locators_id, error_message_id, value=False
    ):
        """This method will take three lists and check for expected error condition against user's inputs"""
        # value represent true because cluster rf and write concern has different wat to catch the error
        i = 0
        # looping through all the error scenario for test
        while i < len(error_input):  # error_input list will hold a list of error inputs from the users
            print(print_statement[i])  # print_statement will hold a list of all general print statements for the test
            locators = locators_id  # locator id of the input placeholder where testing will take place
            locator_sitem = self.locator_finder_by_id(locators)
            locator_sitem.click()
            locator_sitem.clear()
            locator_sitem.send_keys(error_input[i])
            time.sleep(2)

            if semver.VersionInfo.parse("3.8.0") <= self.current_package_version() <= semver.VersionInfo.parse("3.8.100"):
                locator_sitem.send_keys(Keys.TAB)
                time.sleep(2)
            try:
                # trying to create the db for >= v3.9.x
                if value is False and self.current_package_version() >= semver.VersionInfo.parse("3.9.0"):
                    self.locator_finder_by_xpath('//*[@id="modalButton1"]').click()
                    time.sleep(2)
                    # placeholder's error message id for 3.9
                    error_sitem = self.locator_finder_by_xpath(error_message_id).text
                elif value is False and self.current_package_version() == semver.VersionInfo.parse("3.8.0"):
                    error_sitem = self.locator_finder_by_xpath(error_message_id).text
                else:
                    error_sitem = self.locator_finder_by_xpath(error_message_id).text

                # error_message list will hold expected error messages
                assert (
                    error_sitem == error_message[i]
                ), f"FAIL: Expected error message {error_message[i]} but got {error_sitem}"

                print("x" * (len(error_sitem) + 29))
                print("OK: Expected error found: ", error_sitem)
                print("x" * (len(error_sitem) + 29), "\n")
                time.sleep(2)

                # getting out from the db creation for the next check
                if value is False and self.current_package_version() >= semver.VersionInfo.parse("3.9.0"):
                    self.webdriver.refresh()
                    self.locator_finder_by_id("createDatabase").click()
                    time.sleep(1)

            except TimeoutException as ex:
                raise Exception("*****-->Error occurred. Manual inspection required<--***** \n") from ex

            i = i + 1
    
    def check_expected_error_messages_for_views(self,
                                                error_input,
                                                print_statement,
                                                error_message,
                                                locators_id,
                                                error_message_id):
        """This method will take three lists and check for expected error condition against user's inputs"""
        # looping through all the error scenario for test
        i = 0
        while i < len(error_input):  # error_input list will hold a list of error inputs from the users
            print(print_statement[i])  # print_statement will hold a list of all general print statements for the test
            # locator id of the input placeholder where testing will take place
            locator_sitem = self.locator_finder_by_xpath(locators_id)
            locator_sitem.click()
            locator_sitem.clear()
            locator_sitem.send_keys(error_input[i])
            time.sleep(2)

            if self.current_package_version() >= semver.VersionInfo.parse("3.8.0"):
                locator_sitem.send_keys(Keys.TAB)
                time.sleep(2)
            try:
                # trying to create the views
                error_sitem = self.locator_finder_by_xpath(error_message_id).text

                # error_message list will hold expected error messages
                assert error_sitem == error_message[i], \
                    f"FAIL: Expected error message {error_message[i]} but got {error_sitem}"

                print('x' * (len(error_sitem) + 29))
                print('OK: Expected error found: ', error_sitem)
                print('x' * (len(error_sitem) + 29), '\n')
                time.sleep(2)

            except TimeoutException as ex:
                raise Exception("*****-->Error occurred. Manual inspection required<--***** \n") from ex

            i = i + 1


    def check_server_package(self):
        """This will determine the current server package type"""
        try:
            package = self.locator_finder_by_id("communityLabel").text
            return package
        except TimeoutException:
            print("This is not a Community server package.\n")

        try:
            package = self.locator_finder_by_id("enterpriseLabel").text
            return package
        except TimeoutException:
            print("This is not a Enterprise server package.\n")
        return "package not found"

    def choose_item_from_a_dropdown_menu(self, element: WebElement, item_text: str):
        """Given a drop-down menu element,
        click on it to open the menu and then click on an item with given text."""
        element.click()
        item_locator = """//ul[@class="select2-results"]/li/div[text()='%s']""" % item_text
        item_element = self.locator_finder_by_xpath(item_locator)
        item_element.click()

    def click_submenu_entry(self, text):
        """click submenu"""
        locator = """//li[contains(@class, 'subMenuEntry')]/a[text()='%s']""" % text
        self.locator_finder_by_xpath(locator).click()

    def progress(self, arg):
        """state print""" # todo
        print(arg)

    def xpath(self, path):
        """shortcut xpath"""
        return self.webdriver.find_element(BY.XPATH, path)

    def by_class(self, classname):
        """shortcut class-id"""
        return self.webdriver.find_element(BY.CLASS_NAME, classname)

    def handle_red_bar(self):
        """It will check for any red bar error notification"""
        try:
            notification = 'noty_body'
            notification = (self.locator_finder_by_class(notification))
            time.sleep(2)
            print("*" * 100)
            print(notification.text)
            print("*" * 100)
            return notification.text
        except TimeoutException:
            print('No error/warning found!')
            return None
