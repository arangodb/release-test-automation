#!/usr/bin/env python3
""" database testsuite """
from selenium_ui_test.pages.database_page import DatabasePage
from selenium_ui_test.pages.user_page import UserPage
from selenium_ui_test.test_suites.base_selenium_test_suite import BaseSeleniumTestSuite
from test_suites_core.base_test_suite import testcase
import traceback
import semver


class DatabaseTestSuite(BaseSeleniumTestSuite):
    """testing database page"""
    @testcase
    def test_database(self):
        """testing database page"""
        print("---------DataBase Page Test Begin--------- \n")
        # login = LoginPage(self.webdriver, self.cfg)
        # login.login('root', '')

        user = UserPage(self.webdriver, self.cfg)
        db = DatabasePage(self.webdriver, self.cfg)
        self.exception = False
        self.error = None
        assert user.current_user() == "ROOT", "current user is root?"
        assert user.current_database() == "_SYSTEM", "current database is _system?"

        try:
            user.user_tab()
            user.add_new_user("tester")
            user.add_new_user("tester01")

            
            db.create_new_db("Sharded", 0, self.is_cluster)  # 0 = sharded DB
            db.create_new_db("OneShard", 1, self.is_cluster)  # 1 = one shard DB

            if db.version_is_newer_than("3.11.99"):
                print("Skipped \n")
            else:
                if db.current_package_version() < semver.VersionInfo.parse("3.11.0"):
                    db.test_db_expected_error(self.is_cluster)  # testing expected error condition for database creation

                print("Checking sorting databases to ascending and descending \n")
                db.sorting_db()

                print("Checking search database functionality \n")
                db.searching_db("Sharded")
                db.searching_db("OneShard")

                # login.logout_button()
                assert user.current_user() == "ROOT", "current user is root?"
                assert user.current_database() == "_SYSTEM", "current database is _system?"

        except BaseException:
            print('x' * 45, "\nINFO: Error Occurred! Force Deletion Started\n", 'x' * 45)
            self.exception = True  # mark the exception as true
            self.error = traceback.format_exc()

        finally:
            print("Database deletion started.")
            db.deleting_database('Sharded')
            db.deleting_database('OneShard')
            # delete created user
            user.user_tab()
            db.deleting_user('tester')
            db.deleting_user('tester01')

            print("Database deletion completed.")
            del user
            del db
            print("---------DataBase Page Test Completed--------- \n")
            if self.exception:
                raise Exception(self.error)
