from selenium_ui_test.test_suites.base_test_suite import BaseTestSuite, testcase
from selenium_ui_test.pages.user_page import UserPage
from selenium_ui_test.pages.login_page import LoginPage

from selenium_ui_test.pages.collection_page import CollectionPage
from selenium.common.exceptions import TimeoutException

class UserPageTestSuite(BaseTestSuite):
    @testcase
    def test_user(self):
        """testing user page"""
        print("---------User Test Begin--------- \n")
        login = LoginPage(self.webdriver)
        # login.login('root', self.self.root_passvoid)
        self.webdriver.refresh()
        user = UserPage(self.webdriver)
        try:
            print("New user creation begins \n")
            user.user_tab()
            user.add_new_user("tester")

            print("Allow user Read Only access only to the _system DB test started \n")
            user.selecting_user_tester()
            user.selecting_permission_tab()
            print("Changing new user DB permission \n")
            user.changing_db_permission_read_only()
            user.selecting_general_tab()
            user.saving_user_cfg()
            print("Changing new user DB permission completed. \n")
            user.log_out()
            print("Re-Login begins with new user\n")
            login.login_webif("tester", "tester")
            print("Re-Login begins with new user completed: %s / %s\n" % (
                login.current_user(), login.current_database()))

            print("trying to create collection")
            collection_page = CollectionPage(self.webdriver)
            collection_page.navbar_goto("collections")
            collection_page.create_sample_collection("access")
            try:
                collection_page.select_delete_collection()
                raise Exception("must not be able to select deleting collections here!")
            except TimeoutException:
                pass
            print("Allow user Read Only access only to the current DB test completed \n")

            print("Allow user Read/Write access to the _system DB test started \n")
            print("Return back to user tab \n")

            # logout from the current user to get back to root
            user.log_out()
            # login back with root user
            login.login_webif("root", self.root_passvoid)
            print("Re-Login root user completed: %s / %s\n" % (
                login.current_user(), login.current_database()))

            user.user_tab()
            user.selecting_user_tester()
            user.selecting_permission_tab()
            user.changing_db_permission_read_write()
            user.selecting_general_tab()
            user.saving_user_cfg()
            user.log_out()
            print("Re-Login begins with new user\n")
            login.login_webif("tester", "tester")
            print("Re-Login begins with new user completed: %s / %s\n" % (
                login.current_user(), login.current_database()))
            print("trying to create collection")
            collection_page.navbar_goto("collections")
            # TODO: we fail to remove this collection again. 
            #collection_page.create_sample_collection("read/write")
            #collection_page.select_delete_collection()
            print("Allow user Read/Write access to the _system DB test Completed \n")
        finally:
            # logout from the current user to get back to root
            self.webdriver.refresh()
            user.log_out()
            login.login_webif("root", self.root_passvoid)
            print("Re-Login root user completed: %s / %s\n" % (
                login.current_user(), login.current_database()))

            self.webdriver.refresh()
            user.user_tab()
            user.selecting_new_user()
            print("Deleting created user begins\n")
            user.delete_user_btn()
            user.confirm_delete_btn()
        print("Deleting created user completed \n")
        print("---------User Test Completed---------\n")

        assert login.current_user() == "ROOT", "current user is root?"
        assert login.current_database() == "_SYSTEM", "current database is _system?"
