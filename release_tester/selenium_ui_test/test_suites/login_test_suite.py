from selenium_ui_test.test_suites.base_test_suite import BaseTestSuite, testcase
from selenium_ui_test.pages.login_page import LoginPage


class LogInTestSuite(BaseTestSuite):
    @testcase
    def test_login(self):
        """testing login page"""
        print("Starting ", self.webdriver.title, "\n")
        login_page = LoginPage(self.webdriver)
        login_page.log_out()

        login_page.login_webif("root", self.root_passvoid)
        login_page.log_out()
        login_page.login_webif("root", self.root_passvoid)
