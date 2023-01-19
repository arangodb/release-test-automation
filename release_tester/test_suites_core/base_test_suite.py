#!/usr/bin/env python3
""" base class for all testsuites """

import platform
import re
import sys
import traceback
from uuid import uuid4

import distro
from allure_commons.model2 import Status, StatusDetails

# pylint: disable=import-error
from arangodb.installers import RunProperties
from reporting.reporting_utils import AllureTestSuiteContext, RtaTestcase, step
from test_suites_core.models import RtaTestResult


class MetaTestSuite(type):
    def __new__(mcs, name, bases, dct):
        suite_class = super().__new__(mcs, name, bases, dct)
        suite_class.is_disabled = False
        suite_class.disable_reasons = []
        if "child_test_suites" not in dct.keys():
            suite_class.child_test_suites = []
        return suite_class


class BaseTestSuite(metaclass=MetaTestSuite):
    """base class for testsuites"""

    # pylint: disable=dangerous-default-value disable=too-many-instance-attributes
    def __init__(self):
        self.test_results = []
        self.child_classes = self.get_child_test_suite_classes()
        self.children = []
        self.parent_test_suite = None
        self.suite_name = self.__doc__ or self.__class__.__name__
        self.sub_suite_name = None
        self.test_suite_context = None
        self.parent_test_suite_name = None

    def _init_allure(self):
        self.test_suite_context = AllureTestSuiteContext(
            parent_test_suite_name=self.parent_test_suite_name,
            suite_name=self.suite_name,
            sub_suite_name=self.sub_suite_name,
        )

    @classmethod
    def _is_disabled(cls):
        # pylint: disable=no-member
        return cls.is_disabled

    @classmethod
    def _get_disable_reasons(cls):
        # pylint: disable=no-member
        return cls.disable_reasons

    @classmethod
    def get_child_test_suite_classes(cls):
        # pylint: disable=no-member
        return cls.child_test_suites

    def init_child_class(self, child_class):
        """initialise the child class"""
        return child_class()

    def run(self, parent_suite_setup_failed=False):
        """execute the test"""
        self._init_allure()
        if self._is_disabled():
            with RtaTestcase("test suite is skipped") as my_testcase:
                my_testcase.context.status = Status.SKIPPED
                if len(self._get_disable_reasons()) > 0:
                    message = "\n".join(self._get_disable_reasons())
                    my_testcase.context.statusDetails = StatusDetails(message=message)
            return self.test_results
        setup_failed = parent_suite_setup_failed
        if not setup_failed:
            try:
                self.setup_test_suite()
            # pylint: disable=bare-except
            except:
                setup_failed = True
                try:
                    self.add_crash_data_to_report()
                # pylint: disable=bare-except
                except:
                    pass
        if self.has_own_testcases():
            self.test_results += self.run_own_testscases(suite_is_broken=setup_failed)
        for suite_class in self.child_classes:
            suite = self.init_child_class(suite_class)
            self.children.append(suite)
            self.test_results += suite.run(parent_suite_setup_failed=setup_failed)
        tear_down_failed = False
        try:
            self.tear_down_test_suite()
        # pylint: disable=bare-except
        except:
            tear_down_failed = True
            try:
                self.add_crash_data_to_report()
            except:
                pass
        self.test_suite_context.destroy()
        return self.test_results

    def run_own_testscases(self, suite_is_broken=False):
        """run all tests local to the derived class"""
        testcases = [getattr(self, attr) for attr in dir(self) if hasattr(getattr(self, attr), "is_testcase")]
        results = []
        for one_testcase in testcases:
            results.extend(one_testcase(self, suite_is_broken=suite_is_broken))
        return results

    def has_own_testcases(self):
        """do we have own testcases?"""
        testcases = [getattr(self, attr) for attr in dir(self) if hasattr(getattr(self, attr), "is_testcase")]
        return len(testcases) > 0

    def get_run_before_suite_methods(self):
        """list methods that are marked to be ran before test suite"""
        return [getattr(self, attr) for attr in dir(self) if hasattr(getattr(self, attr), "run_before_suite")]

    def get_run_after_suite_methods(self):
        """list methods that are marked to be ran before test suite"""
        return [getattr(self, attr) for attr in dir(self) if hasattr(getattr(self, attr), "run_after_suite")]

    def get_run_before_each_testcase_methods(self):
        """list methods that are marked to be ran before test suite"""
        return [getattr(self, attr) for attr in dir(self) if hasattr(getattr(self, attr), "run_before_each_testcase")]

    def get_run_after_each_testcase_methods(self):
        """list methods that are marked to be ran before test suite"""
        return [getattr(self, attr) for attr in dir(self) if hasattr(getattr(self, attr), "run_after_each_testcase")]

    def get_collect_crash_data_methods(self):
        """list methods that are used to collect crash data in case a test failed"""
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
                # pylint: disable=bare-except
                except:
                    exc_type, exc_val, exc_tb = sys.exc_info()
            self.test_suite_context.test_listener.stop_before_fixture(fixture_uuid, exc_type, exc_val, exc_tb)
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
            self.test_suite_context.test_listener.stop_after_fixture(fixture_uuid, exc_type, exc_val, exc_tb)
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


# pylint: disable=missing-function-docstring
def detect_linux_distro() -> str:
    return distro.linux_distribution(full_distribution_name=False)[0]


def os_is_debian_based() -> bool:
    return detect_linux_distro() in ["debian", "ubuntu"]


def os_is_mac() -> bool:
    return platform.mac_ver()[0] != ""


def os_is_win() -> bool:
    return platform.win32_ver()[0] != ""


def os_is_linux() -> bool:
    return sys.platform == "linux"


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


def disable(arg):
    if callable(arg):
        testcase_func = arg
        testcase_func.is_disabled = True
        return testcase_func
    else:
        reason = arg

        def set_disable_reason(func):
            func.is_disabled = True
            func.disable_reasons.append(reason)
            return func

    return set_disable_reason


def disable_for_windows(arg):
    if callable(arg):
        testcase_func = arg
        if os_is_win():
            testcase_func.is_disabled = True
            testcase_func.disable_reasons.append("This test case is disabled for Windows.")
        return testcase_func
    else:
        reason = arg

        def set_disable_reason(func):
            if os_is_win():
                func.is_disabled = True
                func.disable_reasons.append(reason)
            return func

    return set_disable_reason


def disable_for_mac(arg):
    if callable(arg):
        testcase_func = arg
        if os_is_mac():
            testcase_func.is_disabled = True
            testcase_func.disable_reasons.append("This test case is disabled for MacOS.")
        return testcase_func
    else:
        reason = arg

        def set_disable_reason(func):
            if os_is_mac():
                func.is_disabled = True
                func.disable_reasons.append(reason)
            return func

    return set_disable_reason


def disable_for_debian(arg):
    if callable(arg):
        testcase_func = arg
        if os_is_debian_based():
            testcase_func.is_disabled = True
            testcase_func.disable_reasons.append("This test case is disabled for Debian-based linux distros.")
        return testcase_func
    else:
        reason = arg

        def set_disable_reason(func):
            if os_is_debian_based():
                func.is_disabled = True
                func.disable_reasons.append(reason)
            return func

    return set_disable_reason


def disable_if_true(value, reason=None):
    def set_disable_reason(testcase_func):
        if value:
            testcase_func.is_disabled = True
            if reason:
                testcase_func.disable_reasons.append(reason)
        return testcase_func

    return set_disable_reason


def disable_if_returns_true_at_runtime(function, reason=None):
    def set_disable_func_and_reason(testcase_func):
        testcase_func.disable_functions.append((function, reason))
        return testcase_func

    return set_disable_func_and_reason


linux_only = disable_if_true(not os_is_linux(), reason="This testcase must run only on Linux.")
windows_only = disable_if_true(not os_is_win(), reason="This testcase must run only on Windows.")


def parameters(params):
    def wrapper(func):
        if not (func.is_testcase and callable(func)):
            raise Exception('The "parameters" decorator can only be applied to a testcase function!')
        func.is_parametrized = True
        func.parameters = params
        return func

    return wrapper


def testcase(title=None):
    """base testcase class decorator"""

    def resolve_params_in_name(name: str, params: dict):
        return name.format(**params)

    def decorator(func):
        def wrapper(self, *args, **kwargs):
            # pylint: disable=broad-except disable=too-many-branches
            name = None
            success = None
            message = ""
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
            for function, reason in wrapper.disable_functions:
                if function(self):
                    wrapper.is_disabled = True
                    if reason:
                        wrapper.disable_reasons.append(reason)
            test_results = []
            for test_params in wrapper.parameters:
                parametrized_testcase_name = resolve_params_in_name(name, test_params)
                with RtaTestcase(parametrized_testcase_name) as my_testcase:
                    if wrapper.is_disabled:
                        test_result = RtaTestResult(True, parametrized_testcase_name, "test is skipped", None)
                        my_testcase.context.status = Status.SKIPPED
                        if len(wrapper.disable_reasons) > 0:
                            message = "\n".join(wrapper.disable_reasons)
                            my_testcase.context.statusDetails = StatusDetails(message=message)
                    elif kwargs["suite_is_broken"]:
                        test_result = RtaTestResult(False, parametrized_testcase_name, "test suite is broken", None)
                        my_testcase.context.status = Status.BROKEN
                    else:
                        try:
                            self.setup_testcase()
                            print('Running test case "%s"...' % parametrized_testcase_name)
                            func(*args, **test_params)
                            success = True
                            print('Test case "%s" passed!' % parametrized_testcase_name)
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
                        test_result = RtaTestResult(success, parametrized_testcase_name, message, traceback_instance)
                    test_results.append(test_result)
            return test_results

        wrapper.is_testcase = True
        wrapper.is_disabled = False
        wrapper.disable_reasons = []
        wrapper.is_parametrized = False
        wrapper.parameters = [{}]

        # This list must contain pairs of functions and corresponding reasons.
        # The function must take one argument(the test suite object) and return a boolean value.
        # If this value is true, than the testcase is skipped and the corresponding reason will be seen in the report.
        wrapper.disable_functions = []

        return wrapper

    if callable(title):
        return decorator(title)
    return decorator
