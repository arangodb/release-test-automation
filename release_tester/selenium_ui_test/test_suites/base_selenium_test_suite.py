#!/usr/bin/env python3
""" base class for all selenium testsuites """
from datetime import datetime
from time import sleep

from allure_commons._allure import attach
from allure_commons.types import AttachmentType
from beautifultable import BeautifulTable
from selenium.common.exceptions import InvalidSessionIdException, WebDriverException
from selenium.webdriver.common.by import By
from semver import VersionInfo

from reporting.reporting_utils import attach_table, AllureTestSuiteContext, step
from selenium_ui_test.pages.base_page import BasePage
from selenium_ui_test.pages.login_page import LoginPage
from selenium_ui_test.pages.navbar import NavigationBarPage
from test_suites_core.base_test_suite import (
    BaseTestSuite,
    run_before_suite,
    run_after_suite,
    run_after_each_testcase,
    collect_crash_data,
)


class BaseSeleniumTestSuite(BaseTestSuite):
    """base class for all selenium testsuites"""

    # pylint: disable=too-many-instance-attributes
    def __init__(self, selenium_runner):
        self.selenium_runner = selenium_runner
        super().__init__()
        self.exception = False
        self.error = ""
        self.video_start_time = selenium_runner.video_start_time
        self.webdriver = selenium_runner.webdriver
        self.frontend = selenium_runner.ui_entrypoint_instance
        self.root_passvoid = self.frontend.get_passvoid()
        self.url = self.frontend.get_public_url()
        self.is_cluster = selenium_runner.is_cluster
        self.cfg = selenium_runner.cfg
        self.importer = selenium_runner.importer
        self.restore = selenium_runner.restorer
        self.ui_data_dir = selenium_runner.cfg.ui_data_dir.resolve()
        self.is_enterprise = selenium_runner.cfg.enterprise
        self.is_headless = selenium_runner.is_headless
        self.include_test_suites = selenium_runner.selenium_include_suites
        self.sub_suite_name = self.__doc__ or self.__class__.__name__
        if len(self.include_test_suites) > 0 and self.__class__.__name__ not in self.include_test_suites:
            self.run_own_test_cases = False

    def tprint(self, string):
        """print including timestamp relative to video start"""
        msg = f" {str(datetime.now() - self.video_start_time)} - {string}"
        print(msg)
        with step(msg):
            pass

    def _init_allure(self):
        self.test_suite_context = AllureTestSuiteContext(
            sub_suite_name=self.sub_suite_name, inherit_test_suite_name=True, inherit_parent_test_suite_name=True
        )

    def init_child_class(self, child_class):
        return child_class(self.selenium_runner)

    def ui_assert(self, conditionstate, message):
        """python assert sucks. fuckit."""
        if not conditionstate:
            # pylint: disable=no-member
            self.tprint(message)
            self.save_page_source()
            self.take_screenshot()
            assert False, message

    #    def connect_server_new_tab(self, cfg):
    #        """login..."""
    #        self.progress("Opening page")
    #        self.tprint(frontend_instance[0].get_public_plain_url())
    #        self.original_window_handle = self.webdriver.current_window_handle
    #
    #        # Open a new window
    #        self.webdriver.execute_script("window.open('');")
    #        self.webdriver.switch_to.window(self.webdriver.window_handles[1])
    #        self.webdriver.get(
    #            self.get_protocol()
    #            + "://"
    #            + self.frontend.get_public_plain_url()
    #            + "/_db/_system/_admin/aardvark/index.html"
    #        )
    #        login_page = LoginPage(self.webdriver, self.cfg, self.video_start_time)
    #        login_page.login_webif("root", frontend_instance[0].get_passvoid())
    #
    #    def close_tab_again(self):
    #        """close a tab, and return to main window"""
    #        self.webdriver.close()  # Switch back to the first tab with URL A
    #        # self.webdriver.switch_to.window(self.webdriver.window_handles[0])
    #        # self.tprint("Current Page Title is : %s" %self.webdriver.title)
    #        # self.webdriver.close()
    #        self.webdriver.switch_to.window(self.original_window_handle)
    #        self.original_window_handle = None
    #
    #    def connect_server(self, frontend_instance, database, cfg):
    #        """login..."""
    #        self.progress("Opening page")
    #        self.tprint(frontend_instance[0].get_public_plain_url())
    #        self.webdriver.get(
    #            self.get_protocol()
    #            + "://"
    #            + frontend_instance[0].get_public_plain_url()
    #            + "/_db/_system/_admin/aardvark/index.html"
    #        )
    #        login_page = LoginPage(self.webdriver, self.cfg, self.video_start_time)
    #        login_page.login_webif("root", frontend_instance[0].get_passvoid())

    def go_to_index_page(self):
        """Open index.html"""
        self.tprint("Open index.html")
        path = "/_db/_system/_admin/aardvark/index.html"
        self.goto_url_and_wait_until_loaded(path)
        if "#login" in self.webdriver.current_url:
            login_page = LoginPage(self.webdriver, self.cfg, self.video_start_time)
            login_page.login_webif("root", self.root_passvoid, "_system")
            self.goto_url_and_wait_until_loaded(path)

    def go_to_dashboard(self, username="root", database_name="_system"):
        """open the dashboard page"""
        path = "/_db/_system/_admin/aardvark/index.html#dashboard"
        self.webdriver.get(self.url + path)
        if not path in self.webdriver.current_url:
            login_page = LoginPage(self.webdriver, self.cfg, self.video_start_time)
            login_page.login_webif(username, self.root_passvoid, database_name)
            self.webdriver.get(self.url + path)

    def goto_url_and_wait_until_loaded(self, path):
        """goto & wait for loaded"""
        load_attempts, delay, counter = 10, 30, 0
        while counter < load_attempts:
            try:
                self.webdriver.get(self.url + path)
                break
            except WebDriverException as ex:
                print(f"'{type(ex).__name__}' is thrown - FE may not be ready yet...")
                sleep(delay)
            counter += 1
        else:
            raise Exception(f"FE at '{self.url + path}' still not ready after '{load_attempts * delay}' seconds")
        BasePage(self.webdriver, self.cfg, self.video_start_time).wait_for_ajax()

    @run_before_suite
    def prepare_to_run_tests(self):
        """prepare to run test cases"""
        self.go_to_index_page()

    @run_after_suite
    def after_test_suite(self):
        """clean up after test suite"""
        self.webdriver.delete_all_cookies()

    @run_after_each_testcase
    def after_testcase(self):
        """clean up after test case"""
        self.truncate_browser_log()

    def progress(self, arg):
        """state print todo"""
        self.tprint(arg)

    @collect_crash_data
    def save_browser_data(self):
        """save page source, screenshot and browser console log"""
        self.save_page_source()
        self.take_screenshot()
        self.save_browser_console_log()

    def truncate_browser_log(self):
        """truncate browser console log"""
        self.webdriver.get_log("browser")

    def save_browser_console_log(self):
        """attach browser console log to the allure report"""
        log_entries = self.webdriver.get_log("browser")
        if len(log_entries) > 0:
            table = BeautifulTable(maxwidth=160)
            table.columns.header = ["Level", "Source", "Timestamp", "Message"]
            for entry in log_entries:
                table.rows.append([entry["level"], entry["source"], entry["timestamp"], entry["message"]])
            attach_table(table, "Browser console log")
        else:
            attach("", "Browser console log is empty")

    def save_page_source(self):
        """save current page"""
        html = self.webdriver.page_source
        filename = datetime.now().strftime("%d-%m-%Y_%H:%M:%S.%f") + ".html"
        self.progress("Saving pagedump to file: %s" % filename)
        attach(html, name="Pagedump of ({fn})".format(fn=filename), attachment_type=AttachmentType.HTML)

    def take_screenshot(self):
        """*snap*"""
        # pylint: disable=broad-except
        filename = datetime.now().strftime("%d-%m-%Y_%H:%M:%S.%f") + ".png"
        self.progress("Taking screenshot from: %s " % self.webdriver.current_url)
        try:
            if self.is_headless:
                self.progress("taking full screenshot")
                elmnt = self.webdriver.find_element(By.TAG_NAME, "body")
                screenshot = elmnt.screenshot_as_png()
            else:
                self.progress("taking screenshot")
                screenshot = self.webdriver.get_screenshot_as_png()
        except InvalidSessionIdException:
            self.progress("Fatal: webdriver not connected!")
        except Exception as ex:
            self.progress("falling back to taking partial screenshot " + str(ex))
            screenshot = self.webdriver.get_screenshot_as_png()
        self.progress("Saving screenshot to file: %s" % filename)
        attach(screenshot, name="Screenshot ({fn})".format(fn=filename), attachment_type=AttachmentType.PNG)

    def check_version(self, expected_version: VersionInfo, is_enterprise: bool):
        """validate the version displayed in the UI"""
        ver = NavigationBarPage(self.webdriver, self.cfg, self.video_start_time).detect_version()
        self.progress(" %s ~= %s?" % (ver["version"].lower(), str(expected_version).lower()))
        assert ver["version"].lower().lower().startswith(str(expected_version)), (
            "UI-Test: wrong version: '" + str(ver["version"]).lower() + "' vs '" + str(expected_version).lower() + "'"
        )
        if is_enterprise:
            assert ver["enterprise"] == "ENTERPRISE EDITION", "UI-Test: expected enterprise"
        else:
            assert ver["enterprise"] == "COMMUNITY EDITION", "UI-Test: expected community"
