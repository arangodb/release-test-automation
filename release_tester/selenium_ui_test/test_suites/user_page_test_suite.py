#!/usr/bin/env python3
""" user page testsuite """
import semver
import traceback
from selenium_ui_test.test_suites.base_selenium_test_suite import BaseSeleniumTestSuite
from test_suites_core.base_test_suite import testcase

from selenium_ui_test.pages.user_page import UserPage
from selenium_ui_test.pages.login_page import LoginPage

from selenium_ui_test.pages.collection_page import CollectionPage
from selenium.common.exceptions import TimeoutException
import time

class UserPageTestSuite(BaseSeleniumTestSuite):
# pylint: disable=too-many-statements
    """ user page testsuite """
    @testcase
    def test_user(self):
        """testing user page"""
        self.tprint("---------User Test Begin--------- \n")
        login = LoginPage(self.webdriver, self.cfg, self.video_start_time)
        self.webdriver.refresh()
        user = UserPage(self.webdriver, self.cfg, self.video_start_time)
        collection_page = CollectionPage(self.webdriver, self.cfg, self.video_start_time)
        version_312 = user.version_is_newer_than("3.11.99")

        try:
            if user.version_is_newer_than("3.11.0"):
                if version_312:
                    self.tprint("skipped")
                else:
                    collection_page.create_new_collections('a_first', 0, self.is_cluster)
                    collection_page.create_new_collections('m_middle', 1, self.is_cluster)
                    collection_page.create_new_collections('z_last', 0, self.is_cluster)

                    collection_page.navbar_goto("users")

                    user.check_user_collection_sort()

                    collection_page.delete_collection("a_first", user.a_first_id, self.is_cluster)
                    collection_page.delete_collection("m_middle", user.m_middle_id, self.is_cluster)
                    collection_page.delete_collection("z_last", user.z_last_id, self.is_cluster)

            self.tprint("New user creation begins \n")
            user.user_tab()
            user.add_new_user("tester")

            self.tprint("Allow user Read Only access only to the _system DB test started \n")
            user.selecting_user_tester()
            user.selecting_permission_tab()
            self.tprint("Changing new user DB permission \n")
            user.changing_db_permission_read_only()
            self.webdriver.back()
            # user.selecting_general_tab()
            # user.saving_user_cfg()
            self.tprint("Changing new user DB permission completed. \n")
            if version_312:
                self.tprint("skipped")
            else:
                user.log_out()
                self.tprint("Re-Login begins with new user\n")
                # if version_312:
                #     login.login("tester", "tester")
                # else:
                login.login_webif("tester", "tester")
                self.tprint(
                    f"Re-Login begins with new user completed: {login.current_user()} / {login.current_database()}"
                )

                self.tprint("trying to create collection")
                user.create_sample_collection('access')
                self.tprint("Allow user Read Only access only to the current DB test completed \n")

                self.tprint("Allow user Read/Write access to the _system DB test started \n")
                self.tprint("Return back to user tab \n")

                # logout from the current user to get back to root
                user.log_out()
                # login back with root user
                login.login_webif("root", self.root_passvoid)
                self.tprint(f"Re-Login root user completed: {login.current_user()} / { login.current_database()}")

                user.user_tab()
                user.selecting_user_tester()
                user.selecting_permission_tab()
                user.changing_db_permission_read_write()
                self.webdriver.back()
                # user.saving_user_cfg()
                user.log_out()
                self.tprint("Re-Login begins with new user\n")
                # if version_312:
                #     login.login("tester", "tester")
                # else:
                login.login_webif("tester", "tester")
                self.tprint(
                    f"Re-Login begins with new user completed: {login.current_user()} = {login.current_database()}"
                )
                self.tprint("trying to create collection")
                collection_page.navbar_goto("collections")
                user.create_sample_collection('read/write')
                # TODO: we fail to remove this collection again.
                # collection_page.create_sample_collection("read/write")
                # collection_page.select_delete_collection()
                self.tprint("Allow user Read/Write access to the _system DB test Completed \n")

        except BaseException:
            self.tprint(f"{'x' * 45}\nINFO: Error Occurred! Force cleanup started\n{ 'x' * 45}")
            self.exception = True   # mark the exception as true
            self.error = traceback.format_exc()
        finally:
            # logout from the current user to get back to root
            self.webdriver.refresh()
            user.log_out()
            login.login_webif("root", self.root_passvoid)
            self.tprint(f"Re-Login root user completed:  {login.current_user()} = {login.current_database()}")

            self.webdriver.refresh()
            user.user_tab()
            user.selecting_new_user()
            self.tprint("Deleting created user begins\n")
            user.delete_user_btn()
            user.confirm_delete_btn()
            collection_page.delete_collection("TestDoc", user.test_doc_collection_id, self.is_cluster)

            self.tprint("Deleting created user completed \n")
            self.tprint("---------User Test Completed---------\n")

        if version_312:
            self.tprint("skipped")
        else:
            assert login.current_user() == "ROOT", "current user is root?"
            assert login.current_database() == "_SYSTEM", "current database is _system?"
