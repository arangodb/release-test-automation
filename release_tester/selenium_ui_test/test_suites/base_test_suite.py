#!/usr/bin/env python3
""" base class for all testsuites """
from abc import ABC
from datetime import datetime
import logging
import traceback
from semver import VersionInfo

from allure_commons._allure import attach
from allure_commons.model2 import Status, Label, StatusDetails
from allure_commons.types import AttachmentType, LabelType
from reporting.reporting_utils import AllureTestSuiteContext, RtaTestcase

from selenium.common.exceptions import InvalidSessionIdException

from selenium_ui_test.models import RtaUiTestResult
from selenium_ui_test.pages.login_page import LoginPage
from selenium_ui_test.pages.base_page import BasePage
from selenium_ui_test.pages.navbar import NavigationBarPage


class BaseTestSuite(ABC):
    """ base class for all testsuites """
    # pylint: disable=dangerous-default-value disable=too-many-instance-attributes
    def __init__(self, selenium_runner, child_classes=[]):
        self.selenium_runner = selenium_runner
        self.webdriver = selenium_runner.webdriver
        self.frontend = selenium_runner.ui_entrypoint_instance
        self.root_passvoid = self.frontend.get_passvoid()
        self.url = self.frontend.get_public_url()
        self.is_cluster = selenium_runner.is_cluster
        self.cfg = selenium_runner.cfg
        self.importer = selenium_runner.importer
        self.restore = selenium_runner.restorer
        self.test_data_dir = selenium_runner.cfg.test_data_dir.resolve()
        self.is_enterprise = selenium_runner.cfg.enterprise
        self.is_headless = selenium_runner.is_headless
        self.test_results = []
        self.child_classes = child_classes
        self.children = []
        for suite in child_classes:
            self.children.append(suite(selenium_runner))

    def run(self):
        """ run all tests allure wrapper """
        self.setup()
        for suite in self.children:
            self.test_results += suite.run()
        if self.has_own_testcases():
            with AllureTestSuiteContext(
                None,
                False,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
            ):
                self.test_results += self.run_own_testscases()
        self.tear_down()
        return self.test_results

    def run_own_testscases(self):
        """ run all tests local to the derived class """
        testcases = [getattr(self, attr) for attr in dir(self) if hasattr(getattr(self, attr), "is_testcase")]
        results = []
        for one_testcase in testcases:
            results.append(one_testcase(self))
        return results

    def has_own_testcases(self):
        """ do we have own testcases? """
        testcases = [getattr(self, attr) for attr in dir(self) if hasattr(getattr(self, attr), "is_testcase")]
        return len(testcases) > 0

    def ui_assert(self, conditionstate, message):
        """python assert sucks. fuckit."""
        if not conditionstate:
            logging.error(message)
            self.take_screenshot()
            assert False, message

#    def connect_server_new_tab(self, cfg):
#        """login..."""
#        self.progress("Opening page")
#        print(frontend_instance[0].get_public_plain_url())
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
#        login_page = LoginPage(self.webdriver)
#        login_page.login_webif("root", frontend_instance[0].get_passvoid())

#    def close_tab_again(self):
#        """close a tab, and return to main window"""
#        self.webdriver.close()  # Switch back to the first tab with URL A
#        # self.webdriver.switch_to.window(self.webdriver.window_handles[0])
#        # print("Current Page Title is : %s" %self.webdriver.title)
#        # self.webdriver.close()
#        self.webdriver.switch_to.window(self.original_window_handle)
#        self.original_window_handle = None

#    def connect_server(self, frontend_instance, database, cfg):
#        """login..."""
#        self.progress("Opening page")
#        print(frontend_instance[0].get_public_plain_url())
#        self.webdriver.get(
#            self.get_protocol()
#            + "://"
#            + frontend_instance[0].get_public_plain_url()
#            + "/_db/_system/_admin/aardvark/index.html"
#        )
#        login_page = LoginPage(self.webdriver)
#        login_page.login_webif("root", frontend_instance[0].get_passvoid())

    def go_to_index_page(self):
        """Open index.html"""
        self.progress("Open index.html")
        path = "/_db/_system/_admin/aardvark/index.html"
        self.goto_url_and_wait_until_loaded(path)
        if "#login" in self.webdriver.current_url:
            login_page = LoginPage(self.webdriver)
            login_page.login_webif("root", self.root_passvoid, "_system")
            self.goto_url_and_wait_until_loaded(path)

    def go_to_dashboard(self, username="root", database_name="_system"):
        """ open the dashboard page """
        path = "/_db/_system/_admin/aardvark/index.html#dashboard"
        self.webdriver.get(self.url + path)
        if not path in self.webdriver.current_url:
            login_page = LoginPage(self.webdriver)
            login_page.login_webif(username, self.root_passvoid, database_name)
            self.webdriver.get(self.url + path)

    def goto_url_and_wait_until_loaded(self, path):
        """open a new tab and wait for them to be fully loaded"""
        self.webdriver.get(self.url + path)
        BasePage(self.webdriver).wait_for_ajax()

    def setup(self):
        """prepare to run test cases"""
        self.go_to_index_page()

    def tear_down(self):
        """clean up after test suite"""
        self.webdriver.delete_all_cookies()

    # pylint: disable=no-self-use
    def progress(self, arg):
        """state print""" # todo
        print(arg)

    def take_screenshot(self):
        """*snap*"""
        # pylint: disable=broad-except
        filename = datetime.now().strftime("%d-%m-%Y_%H:%M:%S.%f") + ".png"
        self.progress("Taking screenshot from: %s " % self.webdriver.current_url)
        try:
            if self.is_headless:
                self.progress("taking full screenshot")
                elmnt = self.webdriver.find_element_by_tag_name("body")
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
        ver = NavigationBarPage(self.webdriver).detect_version()
        self.progress(" %s ~= %s?" % (ver["version"].lower(), str(expected_version).lower()))
        assert ver["version"].lower().lower().startswith(str(expected_version)), (
            "UI-Test: wrong version: '" + str(ver["version"]).lower() + "' vs '" + str(expected_version).lower() + "'"
        )
        if is_enterprise:
            assert ver["enterprise"] == "ENTERPRISE EDITION", "UI-Test: expected enterprise"
        else:
            assert ver["enterprise"] == "COMMUNITY EDITION", "UI-Test: expected community"


def testcase(title):
    """ base testcase class decorator """
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            # pylint: disable=broad-except
            name = None
            success = None
            message = None
            traceback_instance = None
            if not callable(title):
                name = title
            elif title.__doc__:
                name = title.__doc__
            else:
                name = title.__name__
            sub_suite_name = self.__doc__ if self.__doc__ else self.__class__.__name__
            with RtaTestcase(name, labels=[Label(name=LabelType.SUB_SUITE, value=sub_suite_name)]) as my_testcase:
                try:
                    print('Running test case "%s"...' % name)
                    func(*args, **kwargs)
                    success = True
                    print('Test case "%s" passed!' % name)
                    my_testcase.context.status = Status.PASSED
                except Exception as ex:
                    success = False
                    print("Test failed!")
                    message = str(ex)
                    traceback_instance = "".join(traceback.TracebackException.from_exception(ex).format())
                    print(message)
                    print(traceback_instance)
                    my_testcase.context.status = Status.FAILED
                    self.take_screenshot()
                    testcase.context.status = Status.FAILED
                    # self.save_browser_console_log()
                    my_testcase.context.statusDetails = StatusDetails(message=message, trace=traceback_instance)
                test_result = RtaUiTestResult(name, success, message, traceback_instance)
                return test_result

        wrapper.is_testcase = True
        return wrapper

    if callable(title):
        return decorator(title)
    return decorator
