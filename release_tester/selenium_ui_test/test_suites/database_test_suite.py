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
        db.create_new_db("Sharded", 0)  # 0 = sharded DB
        db.create_new_db("OneShard", 1)  # 1 = one shard DB

        db.test_database_expected_error()  # testing expected error condition for database creation

        print("Checking sorting databases to ascending and descending \n")
        db.sorting_db()

        print("Checking search database functionality \n")
        db.searching_db("Sharded")
        db.searching_db("OneShard")

        db.Deleting_database("Sharded")
        db.Deleting_database("OneShard")

        # login.logout_button()
        del user
        del db
        print("---------DataBase Page Test Completed--------- \n")