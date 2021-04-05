from loginPage import LoginPage
from userPage import UserPage
from baseSelenium import BaseSelenium


class Test(BaseSelenium):
    BaseSelenium.set_up_class()

    # testing login page
    def test_login(self):
        self.login = LoginPage(self.driver)
        self.login.enter_username('root')
        self.login.enter_password('aa')
        self.login.login_btn()
        self.login.select_db()

    # testing creating new user
    def test_user(self):
        self.user = UserPage(self.driver)
        self.user.new_user_tab()
        self.user.add_new_user()
        self.user.new_user_name('tester')
        self.user.naming_new_user('tester')
        self.user.new_user_password('tester')
        self.user.crating_new_user()

    # shutdown the driver
    def teardown(self):
        self.driver.close()
        self.driver.quit()
        print("test completed.")


ui = Test()
ui.test_login()
ui.test_user()
# ui.teardown()
