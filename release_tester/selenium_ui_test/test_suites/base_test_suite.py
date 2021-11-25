import traceback
from abc import ABC
from allure_commons.model2 import Status, Label, StatusDetails
from allure_commons.types import AttachmentType, LabelType
from reporting.reporting_utils import AllureTestSuiteContext, RtaTestcase
from selenium_ui_test.models import RtaTestResult


class BaseTestSuite(ABC):
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
        self.parent_test_suite_name = None
        self.auto_generate_parent_test_suite_name = None
        self.suite_name = None
        self.runner_type = None
        self.installer_type = None
        self.ssl = None
        self.use_subsuite = True

    def init_child_class(self, child_class):
        return child_class()

    def run(self):
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
        testcases = [getattr(self, attr) for attr in dir(self) if hasattr(getattr(self, attr), "is_testcase")]
        results = []
        for testcase in testcases:
            results.append(testcase(self))
        return results

    def has_own_testcases(self):
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
        pass

    def there_are_failed_tests(self):
        for result in self.test_results:
            if not result.success:
                return True
        return False


def testcase(title=None, disable=False):
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            name = None
            success = None
            message = None
            tb = None
            if callable(title):
                if title.__doc__:
                    name = title.__doc__
                else:
                    name = title.__name__
            else:
                if type(title) == str:
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
            with RtaTestcase(name, labels=labels) as testcase:
                if disable:
                    test_result = RtaTestResult(name, True, "test is skipped", None)
                    testcase.context.status = Status.SKIPPED
                    if type(disable) == str:
                        testcase.context.statusDetails = StatusDetails(message=disable)
                else:
                    try:
                        self.setup_testcase()
                        print('Running test case "%s"...' % name)
                        func(*args, **kwargs)
                        success = True
                        print('Test case "%s" passed!' % name)
                        testcase.context.status = Status.PASSED
                    except Exception as e:
                        success = False
                        print("Test failed!")
                        message = str(e)
                        tb = "".join(traceback.TracebackException.from_exception(e).format())
                        print(message)
                        print(tb)
                        self.add_crash_data_to_report()
                        testcase.context.status = Status.FAILED
                        testcase.context.statusDetails = StatusDetails(message=message, trace=tb)
                    finally:
                        self.teardown_testcase()
                    test_result = RtaTestResult(name, success, message, tb)
                return test_result

        wrapper.is_testcase = True
        wrapper.disable = disable
        return wrapper

    if callable(title):
        return decorator(title)
    else:
        return decorator
