#!/usr/bin/env python3
""" database testsuite """
from selenium_ui_test.pages.database_page import DatabasePage
from selenium_ui_test.pages.user_page import UserPage
from selenium_ui_test.test_suites.base_selenium_test_suite import BaseSeleniumTestSuite
from selenium_ui_test.test_suites.base_test_suite import testcase


class DatabaseTestSuite(BaseSeleniumTestSuite):
    @testcase
    def test_database(self):
        """testing database page"""
        print("---------DataBase Page Test Begin--------- \n")
        # login = LoginPage(self.webdriver)
        # login.login('root', '')

        user = UserPage(self.webdriver)
        assert user.current_user() == "ROOT", "current user is root?"
        assert user.current_database() == "_SYSTEM", "current database is _system?"
        user.user_tab()
        user.add_new_user("tester")
        user.add_new_user("tester01")

        database = DatabasePage(self.webdriver)
        database.create_new_db("Sharded", 0, self.is_cluster)  # 0 = sharded DB
        database.create_new_db("OneShard", 1, self.is_cluster)  # 1 = one shard DB

        database.test_database_expected_error(self.is_cluster)  # testing expected error condition for database creation

        print("Checking sorting databases to ascending and descending \n")
        database.sorting_db()

        print("Checking search database functionality \n")
        database.searching_db("Sharded")
        database.searching_db("OneShard")

        database.deleting_database("Sharded")
        database.deleting_database("OneShard")

        # need to add delete created user here
        user.user_tab()
        database.deleting_user("tester")
        database.deleting_user("tester01")

        # login.logout_button()
        assert user.current_user() == "ROOT", "current user is root?"
        assert user.current_database() == "_SYSTEM", "current database is _system?"
        del user
        del database
        print("---------DataBase Page Test Completed--------- \n")
