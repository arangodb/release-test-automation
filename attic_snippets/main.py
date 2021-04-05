from loginPage import LoginPage
from userPage import UserPage
from baseSelenium import BaseSelenium
import time


class Test(BaseSelenium):
    BaseSelenium.set_up_class()

    # testing login page
    def test_login(self):
        print("Login begin \n")
        self.login = LoginPage(self.driver)
        self.login.enter_username('root')
        self.login.enter_password('aa')
        self.login.login_btn()
        self.login.select_db()
        print("Login completed \n")

    # testing creating new user
    def test_user(self):
        self.user = UserPage(self.driver)
        print("New user creation begins. \n")
        self.user.new_user_tab()
        self.user.add_new_user()
        self.user.new_user_name('tester')
        self.user.naming_new_user('tester')
        self.user.new_user_password('tester')
        self.user.crating_new_user()
        print("New user creation completed. \n")
        self.user.selecting_new_user()
        self.user.selecting_permission()
        print("Changing new user DB permission \n")
        self.user.changing_db_permission()
        self.driver.back()
        self.user.saving_user_cfg()
        self.user.user_logout_button()
        print("Changing new user DB permission \n")

        # creating login page object to reuse it's methods for login with newly created user
        print("Re-Login begins with new user\n")
        self.login = LoginPage(self.driver)
        self.login.enter_username('tester')
        self.login.enter_password('tester')
        self.login.login_btn()
        self.login.select_db()
        print("Re-Login begins with new user completed\n")

    # shutdown the driver
    def teardown(self):
        time.sleep(10)
        self.driver.close()
        self.driver.quit()
        print("test completed.")


ui = Test()
ui.test_login()
ui.test_user()
ui.teardown()
