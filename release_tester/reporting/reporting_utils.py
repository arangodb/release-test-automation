""" utility functions/classes for allure reporting """
from string import Template
from uuid import uuid4

import allure_commons
from allure_commons._allure import attach, StepContext
from allure_commons.logger import AllureFileLogger
from allure_commons.model2 import Status
from allure_commons.types import AttachmentType
from tabulate import tabulate
from reporting.helpers import AllureListener


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
    # pylint: disable=E1101
    template = Template(template_str)
    html_table = tabulate(table, headers=table.column_headers, tablefmt='html')
    attach(template.substitute(html_table=html_table), title, AttachmentType.HTML)


def step(title):
    """init allure step"""
    if callable(title):
        if title.__doc__:
            return StepContext(title.__doc__, {})(title)
        return StepContext(title.__name__, {})(title)
    return StepContext(title, {})


class RtaTestcase:
    """test case class for allure reporting"""

    def __init__(self, name):
        self.name = name
        self._uuid = str(uuid4())
        self.context = TestcaseContext()

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


# pylint: disable=R0903
class TestcaseContext:
    """a class to store test case context"""

    def __init__(self, status=None):
        if status:
            self.status = status
        else:
            self.status = Status.UNKNOWN
        self.labels = []


class AllureTestSuiteContext:
    """test suite class for allure reporting"""

    test_suite_count = 0
    # pylint: disable=R0913
    def __init__(
        self,
        results_dir,
        clean,
        enterprise,
        zip_package,
        new_version,
        old_version=None,
        suite_name=None,
    ):
        if suite_name:
            self.test_suite_name = suite_name
        else:
            if enterprise:
                edition = "Enterprise"
            else:
                edition = "Community"

            if zip_package:
                package_type = "universal binary archive"
            else:
                package_type = "deb/rpm/nsis/dmg"
            if not old_version:
                self.test_suite_name = """
Release Test Suite for ArangoDB v.{} ({}) {} package (clean install)
                    """.format(
                    new_version, edition, package_type
                )
            else:
                self.test_suite_name = """
                Release Test Suite for ArangoDB v.{} ({}) {} package (upgrade from {})
                """.format(
                    new_version, edition, package_type, old_version
                )

        self.test_listener = AllureListener(self.test_suite_name)
        allure_commons.plugin_manager.register(self.test_listener)

        if AllureTestSuiteContext.test_suite_count == 0:
            self.file_logger = AllureFileLogger(results_dir, clean)
        else:
            self.file_logger = AllureFileLogger(results_dir, False)

        allure_commons.plugin_manager.register(self.file_logger)
        AllureTestSuiteContext.test_suite_count += 1

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        allure_commons.plugin_manager.unregister(self.test_listener)
        allure_commons.plugin_manager.unregister(self.file_logger)


def configure_allure(results_dir, clean, enterprise, zip_package, new_version, old_version=None):
    """configure allure reporting"""
    # pylint: disable=R0913
    return AllureTestSuiteContext(results_dir, clean, enterprise, zip_package, new_version, old_version)
