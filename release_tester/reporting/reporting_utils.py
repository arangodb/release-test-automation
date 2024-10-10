""" utility functions/classes for allure reporting """

import platform
import sys
from pathlib import Path
from string import Template
from uuid import uuid4

import allure_commons
from allure_commons._allure import attach, StepContext
from allure_commons.logger import AllureFileLogger
from allure_commons.model2 import Status, Label
from allure_commons.types import AttachmentType, LabelType
from tabulate import tabulate

# pylint: disable=import-error
from reporting.helpers import AllureListener


TARBALL_LIMIT = 999999999
TARBALL_COUNT = 0
TARBALL_LIMIT_INITIALIZED = False


def init_archive_count_limit(limit_value: int):
    """set global variables to control the number of created archives during long runs"""
    # pylint: disable=global-statement
    global TARBALL_LIMIT, TARBALL_COUNT, TARBALL_LIMIT_INITIALIZED
    if not TARBALL_LIMIT_INITIALIZED:
        if limit_value == -1:
            limit_value = 999999999
        TARBALL_LIMIT = limit_value
        TARBALL_COUNT = 0
        TARBALL_LIMIT_INITIALIZED = True
    else:
        print("tarball limit must be set only once per run. doing nothing.", file=sys.stderr)


def attach_table(table, title="HTML table"):
    """attach a BeautifulTable to allure report"""
    template_str = """
    <html>
    <style>
        table {
          white-space: pre-line;
          border-collapse: collapse;
          font-family: Helvetica,Arial,sans-serif;
          font-size: 14px;
          margin: 8px 0;
          padding: 0; }
          table tr {
            border-top: 1px solid #cccccc;
            background-color: white;
            margin: 0;
            padding: 0; }
            table tr:nth-child(2n) {
              background-color: #f8f8f8; }
            table tr th {
              font-weight: bold;
              border: 1px solid #cccccc;
              text-align: left;
              margin: 0;
              padding: 3px 5px; }
            table tr td {
              border: 1px solid #cccccc;
              text-align: left;
              margin: 0;
              padding: 3px 5px; }
            table tr th :first-child, table tr td :first-child {
              margin-top: 0; }
            table tr th :last-child, table tr td :last-child {
              margin-bottom: 0; }
    </style>
    $html_table
    </html>
    """
    # pylint: disable=no-member
    template = Template(template_str)
    html_table = tabulate(table, headers=table.columns.header, tablefmt="html")
    attach(template.substitute(html_table=html_table), title, AttachmentType.HTML)


def attach_http_request_to_report(method: str, url: str, headers: dict, body: str):
    """attach HTTP request info to allure report"""
    request = f"""
    <html>
    <p><b>Method: </b>${method.upper()}</p>
    <p><b>URL: </b>${url}</p>
    <p><b>Headers: </b></p>
    <p>
    """
    for key in headers:
        request += f"<b>{key}: </b>{headers[key]}<br>"
    request += "</p>"
    request += f"<p><b>Body:<br></b>{body}</p>"
    request += "</html>"
    attach(request, "HTTP request", AttachmentType.HTML)


def attach_http_response_to_report(response):
    """attach HTTP response info to allure report"""
    response_html = f"""
    <html>
    <p><b>Status code:</b> {response.status_code}</p>
    <p><b>Headers:</b><br>
    """
    for key in response.headers:
        response_html += f"<b>{key}:</b> {response.headers[key]}<br>"
    response_html += "</p>"
    response_html += f"<p><b>Body: </b>{str(response.content)}</p>"
    response_html += "</html>"
    attach(response_html, f"HTTP response ({response.status_code})", AttachmentType.HTML)


def step(title, params=None):
    """init allure step"""
    if params is None:
        params = {}
    if callable(title):
        if title.__doc__:
            return StepContext(title.__doc__, params)(title)
        return StepContext(title.__name__, params)(title)
    return StepContext(title, params)


class RtaTestcase:
    """test case class for allure reporting"""

    def __init__(self, name, labels=None):
        if labels is None:
            labels = []
        self.name = name
        self._uuid = str(uuid4())
        self.context = TestcaseContext()
        for one_label in labels:
            self.add_label(one_label)

    def __enter__(self):
        allure_commons.plugin_manager.hook.start_test(
            parent_uuid=None,
            uuid=self._uuid,
            name=self.name,
            parameters=None,
            context=self.context,
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        allure_commons.plugin_manager.hook.stop_test(
            parent_uuid=None,
            uuid=self._uuid,
            name=self.name,
            context=self.context,
            exc_type=exc_type,
            exc_val=exc_val,
            exc_tb=exc_tb,
        )

    def add_label(self, label):
        """add label to allure test case"""
        self.context.labels.append(label)


# pylint: disable=too-few-public-methods disable=invalid-name
class TestcaseContext:
    """a class to store test case context"""

    def __init__(self, status=None, statusDetails=None):
        if status:
            self.status = status
        else:
            self.status = Status.UNKNOWN
        self.statusDetails = statusDetails
        self.labels = []


RESULTS_DIR = Path()
CLEAN_DIR = False
ZIP_PACKAGE = False


def init_allure(results_dir: Path, clean: bool, zip_package: bool):
    """globally init this module"""
    # pylint: disable=global-statement
    global RESULTS_DIR, CLEAN_DIR, ZIP_PACKAGE
    if not results_dir.exists():
        results_dir.mkdir(parents=True)

    RESULTS_DIR = results_dir
    CLEAN_DIR = clean
    ZIP_PACKAGE = zip_package


class AllureTestSuiteContext:
    """test suite class for allure reporting"""

    test_suite_count = 0

    # pylint: disable=too-many-locals disable=too-many-arguments
    def __init__(
        self,
        parent_test_suite_name=None,
        suite_name=None,
        sub_suite_name=None,
        labels=None,
        inherit_parent_test_suite_name=False,
        inherit_test_suite_name=False,
    ):
        self.labels = [] if labels is None else labels
        test_listeners = [p for p in allure_commons.plugin_manager.get_plugins() if isinstance(p, AllureListener)]
        self.previous_test_listener = None if len(test_listeners) == 0 else test_listeners[0]
        file_loggers = [l for l in allure_commons.plugin_manager.get_plugins() if isinstance(l, AllureFileLogger)]
        self.file_logger = None if len(file_loggers) == 0 else file_loggers[0]

        self.test_suite_name = suite_name
        if parent_test_suite_name:
            self.parent_test_suite_name = parent_test_suite_name
        else:
            self.parent_test_suite_name = None
        # Always add cpu architecture name to the suite name.
        # Otherwise test results of the same test ran on different platforms could be mixed in the united allure report.
        # Add cpu arch and OS name to tags for extra convenience.
        arch = platform.processor()
        os = sys.platform
        self.labels.append(Label(name=LabelType.TAG, value=arch))
        self.labels.append(Label(name=LabelType.TAG, value=os))
        if self.parent_test_suite_name:
            self.parent_test_suite_name += f" ({arch})"
        elif self.test_suite_name:
            self.test_suite_name += f" ({arch})"
        self.sub_suite_name = sub_suite_name

        # Simply copy suite name and parent suite name from the enveloping test suite,
        # if this is requested specifically.
        # This is a workaround for selenium test suites that run during main test flow.
        if inherit_parent_test_suite_name:
            self.parent_test_suite_name = self.previous_test_listener.default_parent_test_suite_name
        if inherit_test_suite_name:
            self.test_suite_name = self.previous_test_listener.default_test_suite_name

        if not self.file_logger:
            if AllureTestSuiteContext.test_suite_count == 0:
                self.file_logger = AllureFileLogger(RESULTS_DIR, CLEAN_DIR)
            else:
                self.file_logger = AllureFileLogger(RESULTS_DIR, False)
            allure_commons.plugin_manager.register(self.file_logger)

        if self.previous_test_listener:
            allure_commons.plugin_manager.unregister(self.previous_test_listener)
        self.test_listener = AllureListener(
            default_test_suite_name=self.test_suite_name,
            default_parent_test_suite_name=self.parent_test_suite_name,
            default_sub_suite_name=self.sub_suite_name,
            default_labels=self.labels,
        )
        allure_commons.plugin_manager.register(self.test_listener)
        self.test_listener.start_suite_container(self.generate_container_name())
        AllureTestSuiteContext.test_suite_count += 1

    def generate_container_name(self):
        """generate container name"""
        if self.sub_suite_name:
            return self.sub_suite_name
        if self.test_suite_name:
            return self.sub_suite_name
        if self.parent_test_suite_name:
            return self.parent_test_suite_name
        return "Container name is undefined"

    def destroy(self):
        """close test suite context"""
        self.__exit__(None, None, None)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.test_listener.stop_suite_container()
        if self.previous_test_listener:
            allure_commons.plugin_manager.unregister(self.test_listener)
            allure_commons.plugin_manager.register(self.previous_test_listener)
        else:
            allure_commons.plugin_manager.unregister(self.test_listener)
            allure_commons.plugin_manager.unregister(self.file_logger)
