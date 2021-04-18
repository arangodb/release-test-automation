from baseSelenium import BaseSelenium
from dashboardPage import DashboardPage
from loginPage import LoginPage
from userPage import UserPage


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
        self.login.logout_button()
        del self.login

    def test_dashboard(self):
        print("---------Checking Dashboard started--------- \n")
        self.login = LoginPage(self.driver)
        self.login.login('root', 'aa')
        # creating object for dashboard
        self.dash = DashboardPage(self.driver)
        self.dash.check_server_package_name()
        self.dash.check_current_package_version()
        self.dash.check_current_username()
        self.dash.check_current_db()
        self.dash.check_db_status()
        self.dash.check_db_engine()
        self.dash.check_db_uptime()
        print("\nSwitch to System Resource tab\n")
        self.dash.check_system_resource()
        print("Switch to Metrics tab\n")
        self.dash.check_system_metrics()
        print("scrolling the current page \n")
        self.dash.scroll()
        print("Downloading Metrics as JSON file \n")
        self.dash.metrics_download()
        self.dash.select_reload_btn()
        print("Opening Twitter link \n")
        self.dash.click_twitter_link()
        print("Opening Stackoverflow link \n")
        self.dash.click_stackoverflow_link()
        print("Opening Google group link \n")
        self.dash.click_google_group_link()
        self.login.logout_button()
        del self.login
        print("---------Checking Dashboard Completed--------- \n")

    # testing creating new user
    def test_user(self):
        print("---------User Test Begin--------- \n")
        self.login = LoginPage(self.driver)
        self.login.login('root', 'aa')
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
        self.login.logout_button()
        print("Changing new user DB permission completed. \n")

        # creating login page object to reuse it's methods for login with newly created user
        print("Re-Login begins with new user\n")
        self.login = LoginPage(self.driver)
        self.login.login('tester', 'tester')
        print("Re-Login begins with new user completed\n")

        # logout from the current user to get back to root
        self.login.logout_button()
        del self.login
        # login back with root user
        self.login = LoginPage(self.driver)
        self.login.login('root', 'aa')
        # fixme Deleting old user object
        del self.user
        self.user = UserPage(self.driver)
        self.user.new_user_tab()
        self.user.selecting_new_user()
        print("Deleting created user begins\n")
        self.user.delete_user_btn()
        self.user.confirm_delete_btn()
        print("Deleting created user completed \n")
        self.login.logout_button()
        # fixme Deleting old user object
        del self.login
        print("---------User Test Completed---------\n")


ui = Test()     # creating obj for the UI test
ui.test_login()  # testing Login functionality
ui.test_dashboard()  # testing Dashboard functionality
ui.test_user()  # testing User functionality
ui.teardown()   # close the driver and quit
