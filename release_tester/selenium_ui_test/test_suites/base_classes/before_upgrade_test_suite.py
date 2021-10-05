from selenium_ui_test.test_suites.base_test_suite import BaseTestSuite, testcase

from release_tester.selenium_ui_test.pages.navbar import NavigationBarPage


class AfterInstallTestSuite(BaseTestSuite):
    """test cases to check the integrity of the old system before the upgrade"""

    @testcase
    def check_version(self):
        """checks whether the UI has the version that cfg dictates"""
        ver = NavigationBarPage(self.webdriver).detect_version()
        self.progress(" %s ~= %s?" % (ver["version"].lower(), str(self.cfg.semver)))
        assert ver["version"].lower().startswith(str(self.cfg.semver)), "UI-Test: wrong version"
        if self.is_enterprise:
            assert ver["enterprise"] == "ENTERPRISE EDITION", "UI-Test: expected enterprise"
        else:
            assert ver["enterprise"] == "COMMUNITY EDITION", "UI-Test: expected community"
