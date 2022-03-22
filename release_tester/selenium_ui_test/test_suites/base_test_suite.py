#!/usr/bin/env python3
""" base class for all testsuites """

import sys
import traceback
from abc import ABC
from uuid import uuid4

from allure_commons.model2 import Status, Label, StatusDetails
from allure_commons.types import LabelType
#pylint: disable=import-error
from arangodb.installers import RunProperties
from reporting.reporting_utils import AllureTestSuiteContext, RtaTestcase, step
from selenium_ui_test.models import RtaTestResult


class BaseTestSuite(ABC):
    """base class for testsuites"""
    # pylint: disable=dangerous-default-value disable=too-many-instance-attributes
    def __init__(self, child_classes=[]):
        self.test_results = []
        self.child_classes = child_classes
        self.children = []
        self.parent = None
        self.child_classes=child_classes
        self.enterprise = False
        if not hasattr(self, "new_version"):
            self.new_version = None
        self.enc_at_rest = False
        if not hasattr(self, "old_version"):
            self.old_version = None
        if not hasattr(self, "parent_test_suite_name"):
            self.parent_test_suite_name = None
        if not hasattr(self, "auto_generate_parent_test_suite_name"):
            self.auto_generate_parent_test_suite_name = None
        if not hasattr(self, "suite_name"):
            self.suite_name = None
        self.runner_type = None
        self.installer_type = None
        self.ssl = False
        if not hasattr(self, "use_subsuite"):
            self.use_subsuite = True
        versions = []
        if self.old_version:
            versions.append(self.old_version)
        if self.new_version:
            versions.append(self.new_version)
        if hasattr(self, "generate_custom_suite_name"):
            #pylint: disable=no-member
            self.suite_name = self.generate_custom_suite_name()
        if self.use_subsuite:
            self.sub_suite_name = self.__doc__ if self.__doc__ else self.__class__.__name__
        else:
            self.sub_suite_name = None
        self.test_suite_context = AllureTestSuiteContext(
                properties=RunProperties(self.enterprise,
                                         self.enc_at_rest,
                                         self.ssl),
                versions=versions,
                parent_test_suite_name=None if not self.parent_test_suite_name else self.parent_test_suite_name,
                auto_generate_parent_test_suite_name=True
                if not hasattr(self, "auto_generate_parent_test_suite_name")
                else self.auto_generate_parent_test_suite_name,
                suite_name=None if not self.suite_name else self.suite_name,
                sub_suite_name=None if not self.sub_suite_name else self.sub_suite_name,
                runner_type=None if not self.runner_type else self.runner_type,
                installer_type=None if not self.installer_type else self.installer_type,
            )

    # pylint: disable=no-self-use
    def init_child_class(self, child_class):
        """initialise the child class"""
        return child_class()

    def run(self, parent_suite_setup_failed=False):
        """execute the test"""
        setup_failed = parent_suite_setup_failed
        if not setup_failed:
            try:
                self.setup_test_suite()
            except:
                setup_failed = True
                try:
                    self.add_crash_data_to_report()
                except:
                    pass
        if self.has_own_testcases():
            self.test_results += self.run_own_testscases(suite_is_broken=setup_failed)
        for suite_class in self.child_classes:
            suite=self.init_child_class(suite_class)
            suite.test_suite_context.test_listener.parent_test_listener = self.test_suite_context.test_listener
            self.children.append(suite)
            self.test_results += suite.run(parent_suite_setup_failed=setup_failed)
        tear_down_failed = False
        try:
            self.tear_down_test_suite()
        except:
            tear_down_failed = True
            try:
                self.add_crash_data_to_report()
            except:
                pass
        self.test_suite_context.destroy()
        return self.test_results

    def run_own_testscases(self, suite_is_broken=False):
        """ run all tests local to the derived class """
        testcases = [getattr(self, attr) for attr in dir(self) if hasattr(getattr(self, attr), "is_testcase")]
        results = []
        for one_testcase in testcases:
            results.append(one_testcase(self, suite_is_broken=suite_is_broken))
        return results

    def has_own_testcases(self):
        """ do we have own testcases? """
        testcases = [getattr(self, attr) for attr in dir(self) if hasattr(getattr(self, attr), "is_testcase")]
        return len(testcases) > 0

    def get_run_before_suite_methods(self):
        """ list methods that are marked to be ran before test suite """
        return [getattr(self, attr) for attr in dir(self) if hasattr(getattr(self, attr), "run_before_suite")]

    def get_run_after_suite_methods(self):
        """ list methods that are marked to be ran before test suite """
        return [getattr(self, attr) for attr in dir(self) if hasattr(getattr(self, attr), "run_after_suite")]

    def get_run_before_each_testcase_methods(self):
        """ list methods that are marked to be ran before test suite """
        return [getattr(self, attr) for attr in dir(self) if hasattr(getattr(self, attr), "run_before_each_testcase")]

    def get_run_after_each_testcase_methods(self):
        """ list methods that are marked to be ran before test suite """
        return [getattr(self, attr) for attr in dir(self) if hasattr(getattr(self, attr), "run_after_each_testcase")]

    def get_collect_crash_data_methods(self):
        """ list methods that are used to collect crash data in case a test failed"""
        return [getattr(self, attr) for attr in dir(self) if hasattr(getattr(self, attr), "collect_crash_data")]

    def run_before_fixtures(self, funcs):
        """run a set of fixtures before the test suite or test case"""
        for func in funcs:
            name = func.__doc__ if func.__doc__ else func.__name__
            with step(name):
                fixture_uuid = str(uuid4())
                self.test_suite_context.test_listener.start_before_fixture(fixture_uuid, name)
                exc_type = None
                exc_val = None
                exc_tb = None
                try:
                    func()
                #pylint: disable=bare-except
                except:
                    exc_type, exc_val, exc_tb = sys.exc_info()
            self.test_suite_context.test_listener.stop_before_fixture(fixture_uuid, exc_type,
                                                                      exc_val, exc_tb)
            if exc_val:
                raise Exception("Fixture failed.") from exc_val

    def run_after_fixtures(self, funcs):
        """run a set of fixtures after the test suite or test case"""
        fixture_failed = False
        for func in funcs:
            name = func.__doc__ if func.__doc__ else func.__name__
            with step(name):
                fixture_uuid = str(uuid4())
                self.test_suite_context.test_listener.start_after_fixture(fixture_uuid, name)
                exc_type = None
                exc_val = None
                exc_tb = None
                try:
                    func()
                # pylint: disable=bare-except
                except:
                    exc_type, exc_val, exc_tb = sys.exc_info()
            self.test_suite_context.test_listener.stop_after_fixture(fixture_uuid, exc_type,
                                                                     exc_val, exc_tb)
            if exc_val:
                fixture_failed = True
        if fixture_failed:
            raise Exception("Some fixture(s) failed")

    def setup_test_suite(self):
        """prepare to run test suite"""
        self.run_before_fixtures(self.get_run_before_suite_methods())

    def tear_down_test_suite(self):
        """clean up after test suite"""
        self.run_after_fixtures(self.get_run_after_suite_methods())

    def setup_testcase(self):
        """prepare to run test case"""
        self.run_before_fixtures(self.get_run_before_each_testcase_methods())

    def teardown_testcase(self):
        """clean up after test case"""
        self.run_after_fixtures(self.get_run_after_each_testcase_methods())

    def add_crash_data_to_report(self):
        """add eventual crash data"""
        self.run_after_fixtures(self.get_collect_crash_data_methods())

    def there_are_failed_tests(self):
        """check whether there are failed tests"""
        for result in self.test_results:
            if not result.success:
                return True
        return False

def run_before_suite(func):
    """mark method to be ran before test suite"""
    if callable(func):
        func.run_before_suite = True
        return func
    raise Exception("Only functions can be marked with @run_before_suite decorator")

def run_after_suite(func):
    """mark method to be ran after test suite"""
    if callable(func):
        func.run_after_suite = True
        return func
    raise Exception("Only functions can be marked with @run_after_suite decorator")

def run_before_each_testcase(func):
    """mark method to be ran before each testcase in its test suite"""
    if callable(func):
        func.run_before_each_testcase = True
        return func
    raise Exception("Only functions can be marked with @run_before_each_testcase decorator")

def run_after_each_testcase(func):
    """mark method to be ran before each testcase in its test suite"""
    if callable(func):
        func.run_after_each_testcase = True
        return func
    raise Exception("Only functions can be marked with @run_after_each_testcase decorator")

def collect_crash_data(func):
    """mark methods that are used to collect crash data in case a test failed"""
    if callable(func):
        func.collect_crash_data = True
        return func
    raise Exception("Only functions can be marked with @collect_crash_data decorator")

def testcase(title=None, disable=False):
    """ base testcase class decorator """

    def sanitize_kwargs_for_testcase(kwargs_dict):
        dict = kwargs_dict.copy()
        args_to_delete = ["suite_is_broken"]
        for arg in args_to_delete:
            if arg in dict:
                del dict[arg]
        return dict

    def decorator(func):
        def wrapper(self, *args, **kwargs):
            # pylint: disable=broad-except disable=too-many-branches
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
            with RtaTestcase(name) as my_testcase:
                if disable:
                    test_result = RtaTestResult(name, True, "test is skipped", None)
                    my_testcase.context.status = Status.SKIPPED
                    if isinstance(disable, str):
                        my_testcase.context.statusDetails = StatusDetails(message=disable)
                elif kwargs["suite_is_broken"]:
                    test_result = RtaTestResult(name, False, "test suite is broken", None)
                    my_testcase.context.status = Status.BROKEN
                else:
                    try:
                        self.setup_testcase()
                        print('Running test case "%s"...' % name)
                        func(*args, **sanitize_kwargs_for_testcase(kwargs))
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
                        try:
                            self.add_crash_data_to_report()
                        except:
                            pass
                        my_testcase.context.status = Status.FAILED
                        my_testcase.context.statusDetails = StatusDetails(message=message, trace=traceback_instance)
                    finally:
                        try:
                            self.teardown_testcase()
                        except:
                            pass
                    test_result = RtaTestResult(name, success, message, traceback_instance)
                return test_result

        wrapper.is_testcase = True
        wrapper.disable = disable
        return wrapper

    if callable(title):
        return decorator(title)
    return decorator
