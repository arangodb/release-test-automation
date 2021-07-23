from .logging import AllureLogInterceptor
import logging
import allure_commons
from allure_commons.model2 import TestStepResult, Parameter, TestResult, Status, Label, StatusDetails
from allure_commons.reporter import AllureReporter
from allure_commons.types import LabelType, AttachmentType
from allure_commons.utils import now, format_traceback, format_exception
from allure_commons.utils import uuid4


class AllureTitleHelper(object):
    @allure_commons.hookimpl
    def decorate_as_title(self, test_title):
        def decorator(func):
            func.__allure_display_name__ = test_title
            return func
        return decorator


class AllureTestHelper(object):

    @allure_commons.hookimpl
    def decorate_as_description(self, test_description):
        """Not implemented"""
        pass

    @allure_commons.hookimpl
    def decorate_as_description_html(self, test_description_html):
        """Not implemented"""
        pass

    @allure_commons.hookimpl
    def decorate_as_label(self, label_type, labels):
        """Not implemented"""
        pass

    @allure_commons.hookimpl
    def decorate_as_link(self, url, link_type, name):
        """Not implemented"""
        pass


class AllureListener(object):
    def __init__(self, default_test_suite_name=None):
        self.allure_logger = AllureReporter()
        self._cache = ItemCache()
        if default_test_suite_name:
            self.default_test_suite_name = default_test_suite_name
        else:
            self.default_test_suite_name = "Release test automation"

    @allure_commons.hookimpl
    def attach_data(self, body, name, attachment_type, extension):
        self.allure_logger.attach_data(uuid4(), body, name=name, attachment_type=attachment_type, extension=extension)

    @allure_commons.hookimpl
    def attach_file(self, source, name, attachment_type, extension):
        self.allure_logger.attach_file(uuid4(), source, name=name, attachment_type=attachment_type, extension=extension)

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
        parameters = [Parameter(name=name, value=value) for name, value in params.items()]
        step = TestStepResult(name=title, start=now(), parameters=parameters)
        self.allure_logger.start_step(None, uuid, step)

    @allure_commons.hookimpl
    def stop_step(self, uuid, exc_type, exc_val, exc_tb):
        self.allure_logger.stop_step(uuid,
                                     stop=now(),
                                     status=get_status(exc_val),
                                     statusDetails=get_status_details(exc_type, exc_val, exc_tb))

    @allure_commons.hookimpl
    def start_fixture(self, parent_uuid, uuid, name):
        after_fixture = TestAfterResult(name=name, start=now())
        self.allure_logger.start_after_fixture(parent_uuid, uuid, after_fixture)

    @allure_commons.hookimpl
    def stop_fixture(self, parent_uuid, uuid, name, exc_type, exc_val, exc_tb):
        self.allure_logger.stop_after_fixture(uuid,
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
        logger = logging.getLogger()
        log_captor = AllureLogInterceptor()
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(filename)s:%(lineno)d - %(message)s')
        ch = logging.StreamHandler(log_captor)
        ch.setLevel(logger.level)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        context.log_captor = log_captor

    @allure_commons.hookimpl
    def stop_test(self, uuid, context):
        test_result = self._cache.get(uuid)
        test_result.status = context.status
        test_result.stop = now()
        context.log_captor.save_logs()
        for step in test_result.steps:
            if step.status != Status.FAILED:
                continue
            else:
                test_result.status = Status.FAILED
                test_result.statusDetails = step.statusDetails
        self.allure_logger.close_test(uuid)


class ItemCache(object):

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
    else:
        return Status.PASSED


def get_status_details(exception_type, exception, exception_traceback):
    if exception:
        return StatusDetails(message=format_exception(exception_type, exception),
                             trace=format_traceback(exception_traceback))
    else:
        return None
