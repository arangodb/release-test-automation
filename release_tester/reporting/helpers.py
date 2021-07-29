import sys

import allure_commons
from allure_commons.model2 import (
    TestStepResult,
    Parameter,
    TestResult,
    Status,
    Label,
    StatusDetails
)
from allure_commons.reporter import AllureReporter
from allure_commons.types import LabelType, AttachmentType
from allure_commons.utils import now, format_traceback, format_exception, uuid4

from .logging import IoDuplicator


class StepData():
    system_stdout = sys.stdout
    system_stderr = sys.stderr

    def __init__(self):
        self.prev_stdout = sys.stdout
        self.prev_stderr = sys.stderr
        sys.stdout = IoDuplicator(StepData.system_stdout)
        sys.stderr = IoDuplicator(StepData.system_stderr)


class AllureTestHelper():

    @allure_commons.hookimpl
    def decorate_as_description(self, test_description):
        """Not implemented"""

    @allure_commons.hookimpl
    def decorate_as_description_html(self, test_description_html):
        """Not implemented"""

    @allure_commons.hookimpl
    def decorate_as_label(self, label_type, labels):
        """Not implemented"""

    @allure_commons.hookimpl
    def decorate_as_link(self, url, link_type, name):
        """Not implemented"""


class AllureListener():
    def __init__(self, default_test_suite_name=None):
        self.allure_logger = AllureReporter()
        self._cache = ItemCache()
        if default_test_suite_name:
            self.default_test_suite_name = default_test_suite_name
        else:
            self.default_test_suite_name = "Release test automation"

    @allure_commons.hookimpl
    def attach_data(self, body, name, attachment_type, extension):
        self.allure_logger.attach_data(uuid4(),
                                       body,
                                       name=name,
                                       attachment_type=attachment_type,
                                       extension=extension)

    @allure_commons.hookimpl
    def attach_file(self, source, name, attachment_type, extension):
        self.allure_logger.attach_file(uuid4(),
                                       source,
                                       name=name,
                                       attachment_type=attachment_type,
                                       extension=extension)

    @allure_commons.hookimpl
    def add_title(self, test_title):
        test_result = self.allure_logger.get_test(None)
        if test_result:
            test_result.name = test_title

    @allure_commons.hookimpl
    def add_description(self, test_description):
        test_result = self.allure_logger.get_test(None)
        if test_result:
            test_result.description = test_description

    @allure_commons.hookimpl
    def start_step(self, uuid, title, params):
        step_data = StepData()
        self._cache.push(step_data, uuid)
        parameters = [Parameter(name=name, value=value) for name, value in params.items()]
        step = TestStepResult(name=title, start=now(), parameters=parameters)
        self.allure_logger.start_step(None, uuid, step)

    @allure_commons.hookimpl
    def stop_step(self, uuid, exc_type, exc_val, exc_tb):
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
        self.allure_logger.stop_step(uuid,
                                     stop=now(),
                                     status=get_status(exc_val),
                                     statusDetails=get_status_details(exc_type, exc_val, exc_tb))

    @allure_commons.hookimpl
    def start_test(self, name, uuid, context):
        test_result = TestResult(name=name, uuid=uuid, start=now(), stop=now())
        test_result.status = context.status
        test_result.labels.append(Label(name=LabelType.SUITE, value=self.default_test_suite_name))
        test_result.labels.append(Label(name=LabelType.FRAMEWORK, value='ArangoDB Release Test Automation'))
        self.allure_logger.schedule_test(uuid, test_result)
        self._cache.push(test_result, uuid)
        # logger = logging.getLogger()
        # log_captor = AllureLogInterceptor()
        # formatter = logging.Formatter('%(asctime)s %(levelname)s %(filename)s:%(lineno)d - %(message)s')
        # ch = logging.StreamHandler(log_captor)
        # ch.setLevel(logger.level)
        # ch.setFormatter(formatter)
        # logger.addHandler(ch)
        # context.log_captor = log_captor

    @allure_commons.hookimpl
    def stop_test(self, uuid, context):
        test_result = self._cache.get(uuid)
        test_result.status = context.status
        test_result.stop = now()
        # context.log_captor.save_logs()
        for step in test_result.steps:
            if step.status == Status.FAILED:
                test_result.status = Status.FAILED
                test_result.statusDetails = step.statusDetails
        self.allure_logger.close_test(uuid)


class ItemCache():

    def __init__(self):
        self._items = dict()

    def get(self, uuid):
        return self._items.get(uuid)

    def push(self, _id):
        return self._items.setdefault(id(_id), uuid4())

    def push(self, _id, uuid):
        return self._items.setdefault(uuid, _id)

    def pop(self, uuid):
        return self._items.pop(uuid, None)


def get_status(exception):
    if exception:
        return Status.FAILED
    return Status.PASSED

def get_status_details(exception_type, exception, exception_traceback):
    if exception:
        return StatusDetails(message=format_exception(exception_type, exception),
                             trace=format_traceback(exception_traceback))
    return None
