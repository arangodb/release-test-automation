#!/usr/bin/env python3
""" base page object """
import time
import traceback
from datetime import datetime

import tools.interact as ti
import allure

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
from reporting.reporting_utils import step

# from webdriver_manager.chrome import ChromeDriverManager
# from webdriver_manager.firefox import GeckoDriverManager
# from webdriver_manager.microsoft import EdgeChromiumDriverManager
# from webdriver_manager.utils import ChromeType

# can't circumvent long lines.. nAttr nLines
# pylint: disable=line-too-long disable=too-many-instance-attributes disable=too-many-public-methods disable=too-many-statements


class BasePage:
    """Base class for page objects"""

    # Initialize the webdriver and a list to collect performance metrics
    driver: WebDriver
    collected_metrics = []

    def __init__(self, webdriver, cfg, video_start_time):
        """base initialization"""
        self.webdriver = webdriver
        self.video_start_time = video_start_time
        self.cfg = cfg
        self.query_execution_area = '//*[@id="aqlEditor"]'
        self.bindvalues_area = '//*[@id="bindParamAceEditor"]'
        self.locator = None
        self.select = None
        self.current = None

    def tprint(self, string):
        """print including timestamp relative to video start"""
        msg = f" {str(datetime.now() - self.video_start_time)} - {string}"
        print(msg)
        with step(msg):
            pass

    @classmethod
    def set_up_class(cls):
        """This method will be used for the basic driver setup"""

        # browser_list = ['1 = chrome', '2 = firefox', '3 = edge', '4 = chromium']
        # self.tprint(f"{str(*browser_list)} sep=\n")
        # cls.browser_name = None

        # while cls.browser_name not in {1, 2, 3, 4}:
        #     cls.browser_name = int(input('Choose your browser: '))
        #
        #     if cls.browser_name == 1:
        #         self.tprint("You have chosen: Chrome browser \n")
        #         cls.driver = webdriver.Chrome(ChromeDriverManager().install())
        #     elif cls.browser_name == 2:
        #         self.tprint("You have chosen: Firefox browser \n")
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
        #         self.tprint("You have chosen: Edge browser \n")
        #         cls.driver = webdriver.Edge(EdgeChromiumDriverManager().install())
        #     elif cls.browser_name == 4:
        #         self.tprint("You have chosen: Chromium browser \n")
        #         cls.driver = webdriver.Chrome(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
        #     else:
        #         self.tprint("Kindly provide a specific browser name from the list. \n")

        # cls.driver.set_window_size(1250, 1000)  # custom window size
        # cls.driver.get("http://127.0.0.1:8529/_db/_system/_admin/aardvark/index.html#login")

    @classmethod
    def tear_down(cls):
        """This method will be used for teardown the driver instance"""
        time.sleep(5)
        # cls.driver.close()
        self.tprint("\n--------Now Quiting--------\n")
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
            wait.until(
                lambda driver: driver.execute_script("return (typeof jQuery !== 'undefined') && jQuery.active") == 0
            )
            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
        except TimeoutException:
            pass

    def get_performance_metrics(self, driver):
        """Execute JavaScript to get performance data"""
        navigation_timing = driver.execute_script("return window.performance.timing")

        # Calculate performance metrics
        metrics = {
            'load_time': navigation_timing['loadEventEnd'] - navigation_timing['navigationStart'],
            'dom_content_loaded': navigation_timing['domContentLoadedEventEnd'] - navigation_timing['navigationStart'],
            'response_time': navigation_timing['responseEnd'] - navigation_timing['requestStart'],
            'connect_time': navigation_timing['connectEnd'] - navigation_timing['connectStart'],
            'dom_interactive': navigation_timing['domInteractive'] - navigation_timing['navigationStart'],
        }

        return metrics

    def evaluate_performance_metrics(self, metrics):
        """Evaluate performance metrics against thresholds in milliseconds"""
        thresholds = {
            'load_time': 2000,
            'dom_content_loaded': 1000,
            'response_time': 200,
            'connect_time': 100,
            'dom_interactive': 1000
        }

        evaluations = {}
        for key, threshold in thresholds.items():
            value = metrics.get(key, None)
            if value is None:
                evaluations[key] = 'Metric not available'
            else:
                evaluations[key] = 'Good' if value < threshold else 'Poor'
        
        return evaluations

    def aggregate_metrics(self):
        """Aggregate collected metrics and return average values"""
        if not self.collected_metrics:
            return {}

        # Initialize an empty dictionary to store aggregated metrics
        aggregated_metrics = {}
        # Iterate over each key (metric name) in the first collected metrics dictionary
        for key in self.collected_metrics[0]:
            # Calculate the average value for each metric
            aggregated_metrics[key] = sum(metrics[key] for metrics in self.collected_metrics) / len(self.collected_metrics)
        
        # Return the dictionary containing aggregated (average) metrics
        return aggregated_metrics

    def print_combined_performance_results(self):
        """Print combined performance results after all tests"""
        # Aggregate the collected metrics
        aggregated_metrics = self.aggregate_metrics()
        # Evaluate the aggregated metrics
        aggregated_evaluations = self.evaluate_performance_metrics(aggregated_metrics)
        
        # Print the combined performance results
        self.tprint(f"Combined performance metrics: {aggregated_metrics}")
        self.tprint(f"Combined performance results: {aggregated_evaluations}")
        
        # Format the metrics and evaluations as HTML tables
        metrics_html = "<h2>Combined Performance Metrics</h2><table border='1'><tr><th>Metric</th><th>Value</th></tr>"
        for key, value in aggregated_metrics.items():
            metrics_html += f"<tr><td>{key}</td><td>{value}</td></tr>"
        metrics_html += "</table>"

        evaluations_html = "<h2>Combined Performance Results</h2><table border='1'><tr><th>Metric</th><th>Result</th></tr>"
        for key, value in aggregated_evaluations.items():
            evaluations_html += f"<tr><td>{key}</td><td>{value}</td></tr>"
        evaluations_html += "</table>"

        # Add results to Allure report
        with allure.step("Combined Performance Metrics"):
            allure.attach(
                metrics_html,
                name="Combined Performance Metrics",
                attachment_type=allure.attachment_type.HTML
            )
        
        with allure.step("Combined Performance Results"):
            allure.attach(
                evaluations_html,
                name="Combined Performance Results",
                attachment_type=allure.attachment_type.HTML
            )

    def clear_all_text(self, locator=None):
        """This method will select all text and clean it"""
        self.tprint("Cleaning input field \n")
        if locator is not None:
            locator = self.locator_finder_by_xpath(locator)

        self.tprint("Cleaning input field \n")
        actions = ActionChains(self.webdriver)
        actions.click(locator)
        actions.key_down(Keys.CONTROL)
        actions.send_keys("a")
        actions.send_keys(Keys.DELETE)
        actions.key_up(Keys.CONTROL)
        actions.perform()

    def check_ui_responsiveness(self):
        """Checking LOG tab causes unresponsive UI (found in 3.8 server package"""
        self.tprint("\n")
        self.tprint("Clicking on Log tab \n")
        log = "logs"
        log = self.locator_finder_by_id(log)
        log.click()

        self.tprint("Try to tap on Log Level drop down button \n")
        log_level = "logLevelSelection"
        log_level = self.locator_finder_by_id(log_level)
        log_level.click()

        time.sleep(3)

        self.tprint("Close the Log Level button \n")
        log_level01 = "closeFilter"
        log_level01 = self.locator_finder_by_id(log_level01)
        log_level01.click()

        self.tprint("Quickly tap on to Collection Tab")
        collection = "collections"
        collection = self.locator_finder_by_id(collection)
        collection.click()

        self.tprint("Waiting for few seconds \n")
        time.sleep(3)

        self.tprint("Return back to Log tab again \n")
        log01 = "logs"
        log01 = self.locator_finder_by_id(log01)
        log01.click()

        self.tprint("Trying to tap on Log Level once again \n")
        try:
            log_level = "logLevelSelection"
            log_level = self.locator_finder_by_id(log_level)
            log_level.click()
            assert "Level" in log_level.text, "********UI become unresponsive******"
            if log_level.text == "Level":
                self.tprint("Ui is responsive and working as usual\n")
        except TimeoutException:
            self.tprint("********Dashboard responsiveness check failed********")

        time.sleep(2)
        self.tprint("UI responsiveness test completed \n")
        self.tprint("Back to Dashboard again \n")
        self.webdriver.refresh()
        dash = "dashboard"
        dash = self.locator_finder_by_id(dash)
        dash.click()
        time.sleep(2)

    def select_query_execution_area(self):
        """This method will select the query execution area take a
        string and adjacent locator argument of ace-editor and execute the query
        locator set to none for < v3.12x"""
        self.tprint("Selecting query execution area \n")
        if self.current_package_version() > semver.VersionInfo.parse("3.11.100"):
            self.webdriver.refresh()
            # to unify ace_locator class attribute has been used
            query = "//*[text()='Saved Queries']"
            ace_locator = self.locator_finder_by_xpath(query)
            # Set x and y offset positions of adjacent element
            xOffset = 100
            yOffset = 100
            # Performs mouse move action onto the element
            actions = ActionChains(self.webdriver).move_to_element_with_offset(ace_locator, xOffset, yOffset)
            actions.click()
            actions.key_down(Keys.CONTROL).send_keys("a").send_keys(Keys.BACKSPACE).key_up(Keys.CONTROL).perform()
            time.sleep(1)
        else:
            try:
                query = '//*[@id="aqlEditor"]'
                query = self.locator_finder_by_xpath(query)
                query.click()
                time.sleep(2)
            except TimeoutException:
                self.tprint("Can't find the query execution area \n")

    def select_bindvalue_json_area(self):
        """This method will select the query execution area"""
        try:
            query_sitem = self.locator_finder_by_xpath(self.bindvalues_area)
            query_sitem.click()
            time.sleep(2)
        except TimeoutException:
            self.tprint("Can't find the query execution area \n")

    def query_execution_btn(self):
        """Clicking execute query button"""
        if self.current_package_version() >= semver.VersionInfo.parse("3.11.0"):
            execute = "//*[text()='Execute']"
            execute = self.locator_finder_by_xpath(execute)
        else:
            execute = "executeQuery"
            execute = self.locator_finder_by_id(execute)
        execute.click()
        time.sleep(2)

    def send_key_action(self, key):
        """This method will send dummy data to the textfield as necessary"""
        actions = ActionChains(self.webdriver)
        actions.send_keys(key)
        actions.perform()

    def clear_textfield(self):
        """This method will clear the textfield as necessary"""
        actions = ActionChains(self.webdriver)
        actions.key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL).send_keys(Keys.DELETE).perform()

    def clear_text_field(self, locator):
        """This method will be used for clear all the text in single text field if .clear() does not work"""
        locator.send_keys(Keys.CONTROL + "a", Keys.BACKSPACE)

        if self.locator is None:
            raise Exception("UI-Test: ", locator, " locator was not found.")
        return self.locator

    def switch_tab(self, locator):
        """This method will change tab and close it and finally return to origin tab"""
        self.tprint("switching tab method \n")
        self.locator = locator
        self.locator.send_keys(Keys.CONTROL, Keys.RETURN)  # this will open new tab on top of current
        self.webdriver.switch_to.window(self.webdriver.window_handles[1])  # switch to new tab according to index value
        time.sleep(8)
        title = self.webdriver.title
        self.tprint(f"Current page title: {title}\n")
        time.sleep(10)
        self.webdriver.close()  # closes the browser active window
        self.webdriver.switch_to.window(self.webdriver.window_handles[0])
        return title

    def check_version_is_newer(self, compare_version):
        """check whether the version in the ui is the expected"""
        ui_version_str = self.locator_finder_by_id("currentVersion").text
        self.tprint(f"Package Version: {str(ui_version_str)}")
        ui_version = semver.VersionInfo.parse(ui_version_str)
        compare_version = semver.VersionInfo.parse(compare_version)
        return ui_version >= compare_version

    def current_package_version(self):
        """checking current package version from the dashboard"""
        package_version = "currentVersion"
        package_version = self.locator_finder_by_id(package_version).text
        self.tprint(f"Package Version: {str(package_version)}")
        return semver.VersionInfo.parse(package_version)

    def version_is_newer_than(self, version_str):
        """Check if the current package version is newer than the specified version."""
        current_version = self.current_package_version()
        specified_version = semver.VersionInfo.parse(version_str)
        return current_version > specified_version

    def version_is_older_than(self, version_str):
        """Check if the current package version is older than the specified version."""
        current_version = self.current_package_version()
        specified_version = semver.VersionInfo.parse(version_str)
        return current_version < specified_version

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
            self.tprint("")
            time.sleep(3)
        else:
            time.sleep(5)
            self.webdriver.find_element(BY.TAG_NAME, "html").send_keys(Keys.HOME)
        # self.webdriver.execute_script("window.scrollTo(0,500)")

    def locator_finder_by_idx(self, locator_name, timeout=10):
        """This method will used for finding all the locators by their id"""
        self.tprint(locator_name)
        self.locator = WebDriverWait(self.webdriver, timeout).until(
            EC.presence_of_element_located((BY.ID, locator_name)),
            message="UI-Test: " + locator_name + " locator was not found.",
        )
        if self.locator is None:
            raise Exception(locator_name, " locator was not found.")
        return self.locator

    def locator_finder_by_id(self, locator_name, timeout=20, poll_frequency=1, max_retries=1, expec_fail=False, benchmark=False):
        """This method finds locators by their ID using Fluent Wait with retry."""
        if benchmark:
            # Get performance metrics before finding the locator
            metrics_before = self.get_performance_metrics(self.webdriver)

        for attempt in range(max_retries + 1):
            try:
                # Attempt to find the locator using WebDriverWait
                self.locator = WebDriverWait(self.webdriver, timeout, poll_frequency=poll_frequency).until(
                    EC.element_to_be_clickable((BY.ID, locator_name)),
                    message=f"UI-Test: {locator_name} locator was not found.",
                )

                if benchmark:
                    # Get performance metrics after finding the locator
                    metrics_after = self.get_performance_metrics(self.webdriver)
                    self.collected_metrics.append(metrics_after)

                    # Evaluate and print performance metrics
                    evaluations_before = self.evaluate_performance_metrics(metrics_before)
                    evaluations_after = self.evaluate_performance_metrics(metrics_after)
                    
                    self.tprint(f"Performance metrics: {metrics_before}")
                    self.tprint(f"Performance before finding locator {locator_name}: {evaluations_before}")

                    self.tprint(f"Performance metrics: {metrics_after}")
                    self.tprint(f"Performance after finding locator {locator_name}: {evaluations_after}")

                return self.locator
            except TimeoutException as ex:
                if expec_fail or attempt == max_retries:
                    raise ex
                ti.prompt_user(
                    self.cfg,
                    "ERROR " * 10
                    + f"\nError while waiting for web element (Attempt {attempt + 1} of {max_retries + 1}):"
                    f"\n{str(ex)}\n{''.join(traceback.format_stack(ex.__traceback__.tb_frame))}",
                )

        raise Exception(f"UI-Test: {locator_name} locator was not found after {max_retries + 1} attempts.")


    def locator_finder_by_xpath(self, locator_name, timeout=20, poll_frequency=1, max_retries=1, expec_fail=False, benchmark=False):
        """This method finds locators by their xpath using Fluent Wait with retry."""
        if benchmark:
            metrics_before = self.get_performance_metrics(self.webdriver)

        for attempt in range(max_retries + 1):
            try:
                self.locator = WebDriverWait(self.webdriver, timeout, poll_frequency=poll_frequency).until(
                    EC.element_to_be_clickable((BY.XPATH, locator_name)),
                    message=f"UI-Test: {locator_name} locator was not found.",
                )

                if benchmark:
                    metrics_after = self.get_performance_metrics(self.webdriver)
                    self.collected_metrics.append(metrics_after)

                    evaluations_before = self.evaluate_performance_metrics(metrics_before)
                    evaluations_after = self.evaluate_performance_metrics(metrics_after)
                    
                    self.tprint(f"Performance metrics: {metrics_before}")
                    self.tprint(f"Performance before finding locator {locator_name}: {evaluations_before}")

                    self.tprint(f"Performance metrics: {metrics_after}")
                    self.tprint(f"Performance after finding locator {locator_name}: {evaluations_after}")

                return self.locator
            except TimeoutException as ex:
                if expec_fail or attempt == max_retries:
                    raise ex
                ti.prompt_user(
                    self.cfg,
                    "ERROR " * 10
                    + f"\nError while waiting for web element (Attempt {attempt + 1} of {max_retries + 1}):"
                    f"\n{str(ex)}\n{''.join(traceback.format_stack(ex.__traceback__.tb_frame))}",
                )

        raise Exception(f"UI-Test: {locator_name} locator was not found after {max_retries + 1} attempts.")

    def locator_finder_by_link_text(self, locator_name):
        """This method will be used for finding all the locators by their xpath"""
        self.locator = WebDriverWait(self.webdriver, 10).until(EC.element_to_be_clickable((BY.LINK_TEXT, locator_name)))
        if self.locator is None:
            self.tprint(f"UI-Test:  {locator_name} locator has not found.")
            return None
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
            self.tprint(f"UI-Test: {locator_name} locator has not found.")
        return self.select

    def locator_finder_by_class(self, locator_name):
        """This method will used for finding all the locators by their id"""
        self.locator = WebDriverWait(self.webdriver, 10).until(
            EC.element_to_be_clickable((BY.CLASS_NAME, locator_name))
        )
        if self.locator is None:
            self.tprint(f"{locator_name} - locator has not found.")
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
        self.tprint("zooming in now\n")
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
        # self.tprint(f'len: {str(len(name_error))}')
        while i < len(error_input):  # error_input list will hold a list of error inputs from the users
            self.tprint(
                print_statement[i]
            )  # print_statement will hold a list of all general print statements for the test
            locators = locators_id  # locator id of the input placeholder where testing will take place
            # if div_id is not None:
            locator_sitem = self.locator_finder_by_xpath(locators)
            locator_sitem.click()
            locator_sitem.clear()
            locator_sitem.send_keys(error_input[i])
            time.sleep(2)
            locator_sitem.send_keys(Keys.TAB)
            time.sleep(2)

            if self.current_package_version() >= semver.VersionInfo.parse("3.11.0"):
                create_btn = "//*[text()='Create']"
            else:
                create_btn = '//*[@id="modal-content-add-analyzer"]/div[3]/button[2]'
            create_btn_sitem = self.locator_finder_by_xpath(create_btn)
            create_btn_sitem.click()
            time.sleep(2)

            try:
                # placeholder's error message id
                error_sitem = BasePage.locator_finder_by_xpath(error_message_id).text
                self.tprint(f"Expected error found: {error_sitem}\n")
                time.sleep(2)
                error_sitem = self.locator_finder_by_xpath(error_message_id).text
                # error_message list will hold expected error messages
                assert (
                    error_sitem == error_message[i]
                ), f"FAIL: Expected error message {error_message[i]} but got {error_sitem}"

                self.tprint("x" * (len(error_sitem) + 29))
                self.tprint(f"OK: Expected error found: {error_sitem}")
                self.tprint("x" * (len(error_sitem) + 29) + "\n")
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
            self.tprint(
                print_statement[i]
            )  # print_statement will hold a list of all general print statements for the test
            locators = locators_id  # locator id of the input placeholder where testing will take place
            locator_sitem = self.locator_finder_by_id(locators)
            locator_sitem.click()
            locator_sitem.clear()
            locator_sitem.send_keys(error_input[i])
            time.sleep(2)

            if (
                semver.VersionInfo.parse("3.8.0")
                <= self.current_package_version()
                <= semver.VersionInfo.parse("3.8.100")
            ):
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

                self.tprint("x" * (len(error_sitem) + 29))
                self.tprint(f"OK: Expected error found: {error_sitem}")
                self.tprint("x" * (len(error_sitem) + 29) + "\n")
                time.sleep(2)

                # getting out from the db creation for the next check
                if value is False and self.current_package_version() >= semver.VersionInfo.parse("3.9.0"):
                    self.webdriver.refresh()
                    self.locator_finder_by_id("createDatabase").click()
                    time.sleep(1)

            except TimeoutException as ex:
                raise Exception("*****-->Error occurred. Manual inspection required<--***** \n") from ex

            i = i + 1

    def check_expected_error_messages_for_views(
        self, error_input, print_statement, error_message, locators_id, error_message_id
    ):
        """This method will take three lists and check for expected error condition against user's inputs"""
        # looping through all the error scenario for test
        i = 0
        while i < len(error_input):  # error_input list will hold a list of error inputs from the users
            self.tprint(
                print_statement[i]
            )  # print_statement will hold a list of all general print statements for the test
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
                assert (
                    error_sitem == error_message[i]
                ), f"FAIL: Expected error message {error_message[i]} but got {error_sitem}"

                self.tprint("x" * (len(error_sitem) + 29))
                self.tprint(f"OK: Expected error found: {error_sitem}")
                self.tprint("x" * (len(error_sitem) + 29) + "\n")
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
            self.tprint("This is not a Community server package.\n")

        try:
            package = self.locator_finder_by_id("enterpriseLabel").text
            return package
        except TimeoutException:
            self.tprint("This is not a Enterprise server package.\n")
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
        """state print"""  # todo
        try:
            self.tprint(arg)
        except Exception as ex:
            print("eeeeeee")
            print(ex)

    def xpath(self, path):
        """shortcut xpath"""
        return self.webdriver.find_element(BY.XPATH, path)

    def by_class(self, classname):
        """shortcut class-id"""
        return self.webdriver.find_element(BY.CLASS_NAME, classname)

    def handle_red_bar(self):
        """It will check for any red bar error notification"""
        try:
            notification = "noty_body"
            notification = self.locator_finder_by_class(notification)
            time.sleep(2)
            self.tprint("*" * 100)
            self.tprint(notification.text)
            self.tprint("*" * 100)
            return notification.text
        except TimeoutException:
            self.tprint("No error/warning found!")
            return None
