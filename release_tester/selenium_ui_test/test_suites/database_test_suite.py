#!/usr/bin/env python3
""" database testsuite """
from selenium_ui_test.pages.database_page import DatabasePage
from selenium_ui_test.pages.user_page import UserPage
from selenium_ui_test.test_suites.base_selenium_test_suite import BaseSeleniumTestSuite
from test_suites_core.base_test_suite import testcase
import traceback


class DatabaseTestSuite(BaseSeleniumTestSuite):
    """testing database page"""
    @testcase
    def test_database(self):
        """testing database page"""
        print("---------DataBase Page Test Begin--------- \n")
        # login = LoginPage(self.webdriver, self.cfg)
        # login.login('root', '')

        user = UserPage(self.webdriver, self.cfg)
        database = DatabasePage(self.webdriver, self.cfg)
        self.exception = False
        self.error = None
        assert user.current_user() == "ROOT", "current user is root?"
        assert user.current_database() == "_SYSTEM", "current database is _system?"

        try:
            user.user_tab()
            user.add_new_user("tester")
            user.add_new_user("tester01")

            
            database.create_new_db("Sharded", 0, self.is_cluster)  # 0 = sharded DB
            database.create_new_db("OneShard", 1, self.is_cluster)  # 1 = one shard DB

            database.test_database_expected_error(self.is_cluster)  # testing expected error condition for database creation

            print("Checking sorting databases to ascending and descending \n")
            database.sorting_db()

            print("Checking search database functionality \n")
            database.searching_db("Sharded")
            database.searching_db("OneShard")

            # login.logout_button()
            assert user.current_user() == "ROOT", "current user is root?"
            assert user.current_database() == "_SYSTEM", "current database is _system?"

        except BaseException:
            print('x' * 45, "\nINFO: Error Occurred! Force Deletion Started\n", 'x' * 45)
            self.exception = True  # mark the exception as true
            self.error = traceback.format_exc()

        finally:
            print("Database deletion started.")
            database.deleting_database('Sharded')
            database.deleting_database('OneShard')
            # need to delete created user
            user.user_tab()
            database.deleting_user('tester')
            database.deleting_user('tester01')

            print("Database deletion completed.")
            del user
            del database
            print("---------DataBase Page Test Completed--------- \n")
            if self.exception:
                raise Exception(self.error)
