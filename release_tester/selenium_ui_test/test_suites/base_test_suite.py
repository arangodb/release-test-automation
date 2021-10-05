import traceback
import logging
from abc import ABC

from allure_commons._allure import attach
from allure_commons.types import AttachmentType
from selenium.common.exceptions import InvalidSessionIdException
from selenium_ui_test.models import RtaUiTestResult
from selenium_ui_test.pages.login_page import LoginPage
from selenium_ui_test.pages.base_page import BasePage
from datetime import datetime

from reporting.reporting_utils import step


class BaseTestSuite(ABC):
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
        name = self.__doc__ if self.__doc__ else self.__class__.__name__
        with step('Run UI test suite "%s"' % name):
            self.setup()
            for suite in self.children:
                self.test_results += suite.run()
            self.test_results += self.run_own_testscases()
            self.tear_down()
            return self.test_results

    def run_own_testscases(self):
        testcases = [getattr(self, attr) for attr in dir(self) if hasattr(getattr(self, attr), "is_testcase")]
        results = []
        for testcase in testcases:
            results.append(testcase())
        return results

    def ui_assert(self, conditionstate, message):
        """python assert sucks. fuckit."""
        if not conditionstate:
            logging.error(message)
            self.take_screenshot()
            assert False, message

    def connect_server_new_tab(self, cfg):
        """login..."""
        self.progress("Opening page")
        print(frontend_instance[0].get_public_plain_url())
        self.original_window_handle = self.webdriver.current_window_handle

        # Open a new window
        self.webdriver.execute_script("window.open('');")
        self.webdriver.switch_to.window(self.webdriver.window_handles[1])
        self.webdriver.get(
            self.get_protocol()
            + "://"
            + self.frontend.get_public_plain_url()
            + "/_db/_system/_admin/aardvark/index.html"
        )
        login_page = LoginPage(self.webdriver)
        login_page.login_webif("root", frontend_instance[0].get_passvoid())

    def close_tab_again(self):
        """close a tab, and return to main window"""
        self.webdriver.close()  # Switch back to the first tab with URL A
        # self.webdriver.switch_to.window(self.webdriver.window_handles[0])
        # print("Current Page Title is : %s" %self.webdriver.title)
        # self.webdriver.close()
        self.webdriver.switch_to.window(self.original_window_handle)
        self.original_window_handle = None

    def connect_server(self, frontend_instance, database, cfg):
        """login..."""
        self.progress("Opening page")
        print(frontend_instance[0].get_public_plain_url())
        self.webdriver.get(
            self.get_protocol()
            + "://"
            + frontend_instance[0].get_public_plain_url()
            + "/_db/_system/_admin/aardvark/index.html"
        )
        login_page = LoginPage(self.webdriver)
        login_page.login_webif("root", frontend_instance[0].get_passvoid())

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
        path = "/_db/_system/_admin/aardvark/index.html#dashboard"
        self.webdriver.get(self.url + path)
        if not path in self.webdriver.current_url:
            login_page = LoginPage(self.webdriver)
            login_page.login_webif(username, self.root_passvoid, database_name)
            self.webdriver.get(self.url + path)

    def goto_url_and_wait_until_loaded(self, path):
        self.webdriver.get(self.url + path)
        BasePage(self.webdriver).wait_for_ajax()

    def setup(self):
        """prepare to run test cases"""
        self.go_to_index_page()

    def tear_down(self):
        """clean up after test suite"""
        self.webdriver.delete_all_cookies()

    def progress(self, arg):
        """state print todo"""
        print(arg)

    def take_screenshot(self):
        """*snap*"""
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


def testcase(title):
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            name = None
            success = None
            message = None
            tb = None
            if not callable(title):
                name = title
            elif title.__doc__:
                name = title.__doc__
            else:
                name = title.__name__
            with step('Running UI test case "%s"' % name):
                try:
                    print('Running test case "%s"...' % name)
                    func(self, *args, **kwargs)
                    success = True
                    print('Test case "%s" passed!' % name)
                except Exception as e:
                    success = False
                    print("Test failed!")
                    message = str(e)
                    tb = "".join(traceback.TracebackException.from_exception(e).format())
                    print(message)
                    print(tb)
                    self.take_screenshot()
                test_result = RtaUiTestResult(name, success, message, tb)
                return test_result

        wrapper.is_testcase = True
        return wrapper

    if callable(title):
        return decorator(title)
    else:
        return decorator
