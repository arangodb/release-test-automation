#!/usr/bin/env python3
""" database testsuite """
import traceback
import semver
from selenium_ui_test.pages.database_page import DatabasePage
from selenium_ui_test.pages.user_page import UserPage
from selenium_ui_test.test_suites.base_selenium_test_suite import BaseSeleniumTestSuite
from test_suites_core.base_test_suite import testcase


class DatabaseTestSuite(BaseSeleniumTestSuite):
    """testing database page"""
    @testcase
    def test_database(self):
        """testing database page"""
        self.tprint("---------DataBase Page Test Begin--------- \n")
        # login = LoginPage(self.webdriver, self.cfg, self.video_start_time)
        # login.login('root', '')

        user = UserPage(self.webdriver, self.cfg, self.video_start_time)
        db = DatabasePage(self.webdriver, self.cfg, self.video_start_time)
        self.exception = False
        self.error = None
        assert user.current_user() == "ROOT", "current user is root?"
        assert user.current_database() == "_SYSTEM", "current database is _system?"

        try:
            user.user_tab()
            user.add_new_user("tester")
            user.add_new_user("tester01")
            db.create_new_db("Sharded", 0, self.is_cluster, self.is_enterprise)  # 0 = sharded DB
            db.create_new_db("OneShard", 1, self.is_cluster, self.is_enterprise)  # 1 = one shard DB

            if db.version_is_newer_than("3.10.99"):
                self.tprint("Skipped \n")
            else:
                if db.current_package_version() < semver.VersionInfo.parse("3.11.0"):
                    # testing expected error condition for database creation
                    db.test_database_expected_error(self.is_cluster)

                self.tprint("Checking sorting databases to ascending and descending \n")
                db.sorting_db()

                self.tprint("Checking search database functionality \n")
                db.searching_db("Sharded")
                db.searching_db("OneShard")

                # login.logout_button()
                assert user.current_user() == "ROOT", "current user is root?"
                assert user.current_database() == "_SYSTEM", "current database is _system?"

        except BaseException:
            self.tprint(f"{'x' * 45}\nINFO: Error Occurred! Force Deletion Started\n{'x' * 45}")
            self.exception = True  # mark the exception as true
            self.error = traceback.format_exc()

        finally:
            db.print_combined_performance_results()
            self.tprint("Database deletion started.")
            # db.deleting_database('Sharded')
            # db.deleting_database('OneShard')
            # self.tprint("delete created users \n")
            # user.user_tab()
            # db.deleting_user('tester')
            # db.deleting_user('tester01')

            self.tprint("Database deletion completed.")
            del user
            del db
            self.tprint("---------DataBase Page Test Completed--------- \n")
            if self.exception:
                raise Exception(self.error)
