from loginPage import LoginPage
from userPage import UserPage
from baseSelenium import BaseSelenium
# import time


class Test(BaseSelenium):
    BaseSelenium.set_up_class()

    # shutdown the driver
    @staticmethod
    def teardown():
        BaseSelenium.tear_down()

    # testing login page
    def test_login(self):
        self.login = LoginPage(self.driver)
        self.login.login('root', 'aa')

    # testing creating new user
    def test_user(self):
        print("---------User Test Begin--------- \n")
        self.user = UserPage(self.driver)
        print("New user creation begins \n")
        self.user.new_user_tab()
        self.user.add_new_user()
        self.user.new_user_name('tester')
        self.user.naming_new_user('tester')
        self.user.new_user_password('tester')
        self.user.creating_new_user()
        print("New user creation completed \n")
        self.user.selecting_new_user()
        self.user.selecting_permission()
        print("Changing new user DB permission \n")
        self.user.changing_db_permission()
        self.driver.back()
        self.user.saving_user_cfg()
        print("Logout from the current user\n")
        self.login.logout_button()
        print("Changing new user DB permission completed. \n")

        # creating login page object to reuse it's methods for login with newly created user
        print("Re-Login begins with new user\n")
        self.login = LoginPage(self.driver)
        self.login.login('tester', 'tester')
        print("Re-Login begins with new user completed\n")

        # logout from the current user to get back to root
        self.login.logout_button()
        # login back with root user
        self.test_login()
        # fixme Deleting old user object
        del self.user
        self.user = UserPage(self.driver)
        self.user.new_user_tab()
        self.user.selecting_new_user()
        print("Deleting created user begins\n")
        self.user.delete_user_btn()
        self.user.confirm_delete_btn()
        print("Deleting created user completed \n")
        print("---------User Test Completed---------")


ui = Test()
ui.test_login()
ui.test_user()
ui.teardown()
