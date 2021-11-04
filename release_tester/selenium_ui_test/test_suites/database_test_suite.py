from selenium_ui_test.pages.user_page import UserPage
from selenium_ui_test.test_suites.base_test_suite import BaseTestSuite, testcase
from selenium_ui_test.pages.databasePage import DatabasePage


class DatabaseTestSuite(BaseTestSuite):
    @testcase
    def test_database(self):
        """testing database page"""
        print("---------DataBase Page Test Begin--------- \n")
        # login = LoginPage(self.webdriver)
        # login.login('root', '')

        user = UserPage(self.webdriver)
        user.user_tab()
        user.add_new_user("tester")
        user.add_new_user("tester01")

        db = DatabasePage(self.webdriver)
        db.create_new_db("Sharded", 0, self.is_cluster)  # 0 = sharded DB
        db.create_new_db("OneShard", 1, self.is_cluster)  # 1 = one shard DB

        db.test_database_expected_error(self.is_cluster)  # testing expected error condition for database creation

        print("Checking sorting databases to ascending and descending \n")
        db.sorting_db()

        print("Checking search database functionality \n")
        db.searching_db("Sharded")
        db.searching_db("OneShard")

        db.deleting_database("Sharded")
        db.deleting_database("OneShard")

        # need to add delete created user here
        user.user_tab()
        db.deleting_user("tester")
        db.deleting_user("tester01")

        # login.logout_button()
        del user
        del db
        print("---------DataBase Page Test Completed--------- \n")
