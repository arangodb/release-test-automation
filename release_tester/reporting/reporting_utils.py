from string import Template
from uuid import uuid4

import allure_commons
import markdown
from allure_commons._allure import attach, StepContext
from allure_commons.logger import AllureFileLogger
from allure_commons.model2 import Status
from allure_commons.types import AttachmentType
from beautifultable import BeautifulTable

from .helpers import AllureListener, AllureTitleHelper


def configure_allure(results_dir, clean, enterprise, zip, new_version, old_version=None):
    if enterprise:
        edition = "Enterprise"
    else:
        edition = "Community"

    if zip:
        package_type = ".tar.gz"
    else:
        package_type = ".deb"
    if not old_version:
        test_suite_name = "Release Test Suite for ArangoDB v.{} ({}) {} package (clean install)".format(new_version, edition, package_type)
    else:
        test_suite_name = "Release Test Suite for ArangoDB v.{} ({}) {} package (upgrade from {})".format(new_version, edition,
                                                                                        package_type, old_version)
    test_listener = AllureListener(test_suite_name)
    allure_commons.plugin_manager.register(test_listener)

    file_logger = AllureFileLogger(results_dir, clean)
    allure_commons.plugin_manager.register(file_logger)

    title_helper = AllureTitleHelper()
    allure_commons.plugin_manager.register(title_helper)


def attach_table(table, title="HTML table"):
    """ attach a BeautifulTable to allure report """
    template_str = """
    <html>
    <style>
        table {
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
    table.set_style(BeautifulTable.STYLE_MARKDOWN)
    template = Template(template_str)
    html_table = markdown.markdown(str(table), extensions=['markdown.extensions.tables'])
    attach(template.substitute(html_table=html_table), title, AttachmentType.HTML)


def step(title):
    if callable(title):
        if title.__doc__:
            return StepContext(title.__doc__, {})(title)
        else:
            return StepContext(title.__name__, {})(title)
    else:
        return StepContext(title, {})


class RtaTestcase(object):
    def __init__(self, name):
        self.name = name
        self._uuid = str(uuid4())
        self.context = TestcaseContext()

    def __enter__(self):
        allure_commons.plugin_manager.hook.start_test(parent_uuid=None,
                                       uuid=self._uuid,
                                       name=self.name,
                                       parameters=None,
                                       context=self.context)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        allure_commons.plugin_manager.hook.stop_test(parent_uuid=None,
                                      uuid=self._uuid,
                                      name=self.name,
                                      context=self.context,
                                      exc_type=None,
                                      exc_val=None,
                                      exc_tb=None)


class TestcaseContext:
    def __init__(self, status):
        self.status = status

    def __init__(self):
       self.status = Status.UNKNOWN