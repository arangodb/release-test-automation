#!/usr/bin/env python3
""" base class for all testsuites """

import traceback
from abc import ABC

from allure_commons.model2 import Status, Label, StatusDetails
from allure_commons.types import LabelType

from reporting.reporting_utils import AllureTestSuiteContext, RtaTestcase
from selenium_ui_test.models import RtaTestResult
from arangodb.installers import RunProperties


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
        self.enterprise = False
        self.zip_package = None
        self.new_version = None
        self.enc_at_rest = False
        self.old_version = None
        self.parent_test_suite_name = None
        self.auto_generate_parent_test_suite_name = None
        self.suite_name = None
        self.runner_type = None
        self.installer_type = None
        self.ssl = False
        self.use_subsuite = True

    # pylint: disable=no-self-use
    def init_child_class(self, child_class):
        """initialise the child class"""
        return child_class()

    def run(self):
        """execute the test"""
        self.setup_test_suite()
        versions=[self.new_version]
        if self.old_version:
            versions.append(self.old_version)

        for suite in self.children:
            self.test_results += suite.run()
        if self.has_own_testcases():
            with AllureTestSuiteContext(
                results_dir=None if not self.results_dir else self.results_dir,
                clean=self.clean_allure_dir,
                properties=RunProperties(self.enterprise,
                                         self.enc_at_rest,
                                         self.ssl),
                zip_package=None if not self.zip_package else self.zip_package,
                versions=versions,
                parent_test_suite_name=None if not self.parent_test_suite_name else self.parent_test_suite_name,
                auto_generate_parent_test_suite_name=True
                if not hasattr(self, "auto_generate_parent_test_suite_name")
                else self.auto_generate_parent_test_suite_name,
                suite_name=None if not self.suite_name else self.suite_name,
                runner_type=None if not self.runner_type else self.runner_type,
                installer_type=None if not self.installer_type else self.installer_type,
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
        pass

    def tear_down_test_suite(self):
        """clean up after test suite"""
        pass

    def setup_testcase(self):
        """prepare to run test case"""
        pass

    def teardown_testcase(self):
        """clean up after test case"""
        pass

    def add_crash_data_to_report(self):
        """add eventual crash data"""
        pass

    def there_are_failed_tests(self):
        """check whether there are failed tests"""
        for result in self.test_results:
            if not result.success:
                return True
        return False


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
