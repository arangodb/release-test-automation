from selenium_ui_test.test_suites.base_test_suite import BaseTestSuite, testcase
from selenium_ui_test.pages.login_page import LoginPage


class LogInTestSuite(BaseTestSuite):
    @testcase
    def test_login(self):
        """testing login page"""
        print("Starting ", self.webdriver.title, "\n")
        login_page = LoginPage(self.webdriver)
        login_page.login("root", self.root_passvoid)
        collections_page = CollectionPage(self.webdriver)
        collections_page.log_out()
