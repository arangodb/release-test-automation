#!/usr/bin/env python3
""" base class for all testsuites """

import traceback
from abc import ABC
from datetime import datetime
from allure_commons._allure import attach
from allure_commons.model2 import Status, Label, StatusDetails
from allure_commons.types import AttachmentType, LabelType
from reporting.reporting_utils import AllureTestSuiteContext, RtaTestcase

from semver import VersionInfo

from selenium.common.exceptions import InvalidSessionIdException

from selenium_ui_test.pages.navbar import NavigationBarPage
from selenium_ui_test.models import RtaTestResult

class BaseTestSuite(ABC):
    """base class for testsuites"""
    # pylint: disable=dangerous-default-value disable=too-many-instance-attributes
    def __init__(self, child_classes=[]):
        self.test_results = []
        self.child_classes = child_classes
        self.children = []
        for child_class in child_classes:
            self.children.append(self.init_child_class(child_class))
        self.results_dir = None
        self.clean_allure_dir = True
        self.enterprise = None
        self.zip_package = None
        self.new_version = None
        self.enc_at_rest = None
        self.old_version = None
        self.webdriver = None
        self.is_headless = False
        self.parent_test_suite_name = None
        self.auto_generate_parent_test_suite_name = None
        self.suite_name = None
        self.runner_type = None
        self.installer_type = None
        self.ssl = None
        self.use_subsuite = True

    # pylint: disable=no-self-use
    def init_child_class(self, child_class):
        """initialise the child class"""
        return child_class()

    def run(self):
        """execute the test"""
        self.setup_test_suite()
        for suite in self.children:
            self.test_results += suite.run()
        if self.has_own_testcases():
            with AllureTestSuiteContext(
                results_dir=None if not self.results_dir else self.results_dir,
                clean=self.clean_allure_dir,
                enterprise=None if not self.enterprise else self.enterprise,
                zip_package=None if not self.zip_package else self.zip_package,
                new_version=None if not self.new_version else self.new_version,
                enc_at_rest=None if not self.enc_at_rest else self.enc_at_rest,
                old_version=None if not self.old_version else self.old_version,
                parent_test_suite_name=None if not self.parent_test_suite_name else self.parent_test_suite_name,
                auto_generate_parent_test_suite_name=True
                if not hasattr(self, "auto_generate_parent_test_suite_name")
                else self.auto_generate_parent_test_suite_name,
                suite_name=None if not self.suite_name else self.suite_name,
                runner_type=None if not self.runner_type else self.runner_type,
                installer_type=None if not self.installer_type else self.installer_type,
                ssl=False if not self.ssl else self.ssl,
            ):
                self.test_results += self.run_own_testscases()
        self.tear_down_test_suite()
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

    def setup_test_suite(self):
        """prepare to run test suite"""

    def tear_down_test_suite(self):
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

def testcase(title=None, disable=False):
    """ base testcase class decorator """
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            # pylint: disable=broad-except
            name = None
            success = None
            message = None
            traceback_instance = None
            if callable(title):
                if title.__doc__:
                    name = title.__doc__
                else:
                    name = title.__name__
            else:
                if isinstance(title, str):
                    name = title
                else:
                    if func.__doc__:
                        name = func.__doc__
                    else:
                        name = func.__name__
            labels = []
            if self.use_subsuite:
                sub_suite_name = self.__doc__ if self.__doc__ else self.__class__.__name__
                labels.append(Label(name=LabelType.SUB_SUITE, value=sub_suite_name))
            with RtaTestcase(name, labels=labels) as my_testcase:
                if disable:
                    test_result = RtaTestResult(name, True, "test is skipped", None)
                    my_testcase.context.status = Status.SKIPPED
                    if isinstance(disable, str):
                        my_testcase.context.statusDetails = StatusDetails(message=disable)
                else:
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
                        self.add_crash_data_to_report()
                        my_testcase.context.status = Status.FAILED
                        my_testcase.context.statusDetails = StatusDetails(message=message, trace=traceback_instance)
                    finally:
                        self.teardown_testcase()
                    test_result = RtaTestResult(name, success, message, traceback_instance)
                return test_result

        wrapper.is_testcase = True
        wrapper.disable = disable
        return wrapper

    if callable(title):
        return decorator(title)
    return decorator
