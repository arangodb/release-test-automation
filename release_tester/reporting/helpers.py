""" classes for allure integration """
import sys

import allure_commons
from allure_commons.model2 import (
    TestStepResult,
    Parameter,
    TestResult,
    Status,
    Label,
    StatusDetails,
    TestResultContainer,
    TestBeforeResult,
    TestAfterResult,
)
from allure_commons.reporter import AllureReporter
from allure_commons.types import LabelType, AttachmentType
from allure_commons.utils import now, format_traceback, format_exception, uuid4

# pylint: disable=import-error
from reporting.logging import IoDuplicator


# pylint: disable=too-few-public-methods
class StepData:
    """a class to store step context"""

    system_stdout = sys.stdout
    system_stderr = sys.stderr

    def __init__(self):
        self.prev_stdout = sys.stdout
        self.prev_stderr = sys.stderr
        new_stdout = IoDuplicator(StepData.system_stdout)
        new_stderr = IoDuplicator(StepData.system_stderr)
        sys.stdout = new_stdout
        sys.stderr = new_stderr


# pylint: disable=too-many-instance-attributes
class AllureListener:
    """allure plugin implementation"""

    def __init__(
        self,
        default_test_suite_name=None,
        default_parent_test_suite_name=None,
        default_sub_suite_name=None,
        default_labels=None,
    ):
        if default_labels is None:
            default_labels = []
        self.allure_logger = AllureReporter()
        self._cache = ItemCache()
        self.default_test_suite_name = default_test_suite_name
        self.default_parent_test_suite_name = default_parent_test_suite_name
        self.default_sub_suite_name = default_sub_suite_name
        self.container_uuid = str(uuid4())
        self.current_testcase_container_uuid = None
        self.parent_test_listener = None
        self.default_labels = default_labels

    @allure_commons.hookimpl
    def attach_data(self, body, name, attachment_type, extension):
        """attach data to allure report"""
        self.allure_logger.attach_data(
            uuid4(),
            body,
            name=name,
            attachment_type=attachment_type,
            extension=extension,
        )

    @allure_commons.hookimpl
    def attach_file(self, source, name, attachment_type, extension):
        """attach file to allure report"""
        self.allure_logger.attach_file(
            uuid4(),
            source,
            name=name,
            attachment_type=attachment_type,
            extension=extension,
        )

    @allure_commons.hookimpl
    def add_title(self, test_title):
        """add title to current allure report item"""
        test_result = self.allure_logger.get_test(None)
        if test_result:
            test_result.name = test_title

    @allure_commons.hookimpl
    def add_description(self, test_description):
        """add description to current allure report item"""
        test_result = self.allure_logger.get_test(None)
        if test_result:
            test_result.description = test_description

    @allure_commons.hookimpl
    def start_step(self, uuid, title, params):
        """start step"""
        step_data = StepData()
        self._cache.push(step_data, uuid)
        parameters = [Parameter(name=name, value=value) for name, value in params.items()]
        step = TestStepResult(name=title, start=now(), parameters=parameters)
        self.allure_logger.start_step(None, uuid, step)

    @allure_commons.hookimpl
    def stop_step(self, uuid, exc_type, exc_val, exc_tb):
        """stop step"""
        step_data = self._cache.get(uuid)
        out = sys.stdout.getvalue()
        sys.stdout.close()
        if len(out) != 0:
            self.attach_data(out, "STDOUT", AttachmentType.TEXT, "txt")
        sys.stdout = step_data.prev_stdout
        err = sys.stderr.getvalue()
        sys.stderr.close()
        if len(err) != 0:
            self.attach_data(err, "STDERR", AttachmentType.TEXT, "txt")
        sys.stderr = step_data.prev_stderr
        self.allure_logger.stop_step(
            uuid,
            stop=now(),
            status=get_status(exc_val),
            statusDetails=get_status_details(exc_type, exc_val, exc_tb),
        )

    @allure_commons.hookimpl
    def start_test(self, name, uuid, context):
        """start test"""
        test_result = TestResult(name=name, uuid=uuid, start=now(), stop=now())
        test_result.status = context.status
        if self.default_test_suite_name:
            test_result.labels.append(Label(name=LabelType.SUITE, value=self.default_test_suite_name))
        if self.default_parent_test_suite_name:
            test_result.labels.append(Label(name=LabelType.PARENT_SUITE, value=self.default_parent_test_suite_name))
        if self.default_sub_suite_name:
            test_result.labels.append(Label(name=LabelType.SUB_SUITE, value=self.default_sub_suite_name))
        test_result.labels.append(Label(name=LabelType.FRAMEWORK, value="ArangoDB Release Test Automation"))
        self.allure_logger.schedule_test(uuid, test_result)
        self._cache.push(test_result, uuid)
        for label in self.default_labels + context.labels:
            test_result.labels.append(label)
        self.allure_logger.update_group(self.container_uuid, children=uuid)
        parent = self.parent_test_listener
        while parent:
            parent.allure_logger.update_group(parent.container_uuid, children=uuid)
            parent = parent.parent_test_listener
        self.current_testcase_container_uuid = str(uuid4())
        container = TestResultContainer(uuid=self.current_testcase_container_uuid, name=name)
        self._cache.push(container, self.current_testcase_container_uuid)
        self.allure_logger.start_group(self.current_testcase_container_uuid, container)
        self.allure_logger.update_group(self.current_testcase_container_uuid, start=now())
        self.allure_logger.update_group(self.current_testcase_container_uuid, children=uuid)

    # pylint: disable=too-many-arguments
    @allure_commons.hookimpl
    def stop_test(self, uuid, context, exc_type, exc_val, exc_tb):
        """stop test"""
        test_result = self._cache.get(uuid)
        test_result.status = context.status
        if context.statusDetails:
            test_result.statusDetails = context.statusDetails
        test_result.stop = now()
        if exc_type or exc_val or exc_tb:
            test_result.status = get_status(exc_val)
            test_result.statusDetails = get_status_details(exc_type, exc_val, exc_tb)
        for step in test_result.steps:
            if step.status == Status.FAILED:
                test_result.status = Status.FAILED
                test_result.statusDetails = step.statusDetails

        for label in context.labels:
            if label not in test_result.labels:
                test_result.labels.append(label)
        self.allure_logger.close_test(uuid)
        self.allure_logger.stop_group(self.current_testcase_container_uuid)
        self.current_testcase_container_uuid = None

    def start_suite_container(self, suite_name):
        """start a test suite"""
        container = TestResultContainer(uuid=self.container_uuid, name=suite_name)
        self._cache.push(container, self.container_uuid)
        self.allure_logger.start_group(self.container_uuid, container)
        self.allure_logger.update_group(self.container_uuid, start=now())

    def stop_suite_container(self):
        """stop running test suite"""
        self.allure_logger.stop_group(self.container_uuid)

    def start_before_fixture(self, uuid, name):
        """start a fixture that is ran before a test case or test suite"""
        container_uuid = (
            self.current_testcase_container_uuid if self.current_testcase_container_uuid else self.container_uuid
        )
        fixture = TestBeforeResult(name=name, start=now(), parameters={})
        self.allure_logger.start_before_fixture(container_uuid, uuid, fixture)

    def stop_before_fixture(self, uuid, exc_type, exc_val, exc_tb):
        """stop a fixture that is ran before a test case or test suite"""
        self.allure_logger.stop_before_fixture(
            uuid=uuid,
            stop=now(),
            status=get_status(exc_val),
            statusDetails=get_status_details(exc_type, exc_val, exc_tb),
        )

    def start_after_fixture(self, uuid, name):
        """start a fixture that is ran after a test case or test suite"""
        container_uuid = (
            self.current_testcase_container_uuid if self.current_testcase_container_uuid else self.container_uuid
        )
        fixture = TestAfterResult(name=name, start=now(), parameters={})
        self.allure_logger.start_after_fixture(container_uuid, uuid, fixture)

    def stop_after_fixture(self, uuid, exc_type, exc_val, exc_tb):
        """stop a fixture that is ran after a test case or test suite"""
        self.allure_logger.stop_after_fixture(
            uuid=uuid,
            stop=now(),
            status=get_status(exc_val),
            statusDetails=get_status_details(exc_type, exc_val, exc_tb),
        )


class ItemCache:
    """a class to store allure report objects before writing to output"""

    def __init__(self):
        self._items = {}

    def get(self, uuid):
        """get item from cache by uuid"""
        return self._items.get(uuid)

    def push(self, _id, uuid):
        """add item to cache with predefined uuid"""
        return self._items.setdefault(uuid, _id)

    def pop(self, uuid):
        """pop item from cache"""
        return self._items.pop(uuid, None)


def get_status(exception):
    """define step status"""
    if exception:
        return Status.FAILED
    return Status.PASSED


def get_status_details(exception_type, exception, exception_traceback):
    """define test status details"""
    if exception:
        return StatusDetails(
            message=format_exception(exception_type, exception),
            trace=format_traceback(exception_traceback),
        )
    return None
