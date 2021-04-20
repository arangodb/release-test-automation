from baseSelenium import BaseSelenium
from dashboardPage import DashboardPage
from loginPage import LoginPage
from userPage import UserPage
from viewsPage import ViewsPage


class Test(BaseSelenium):
    BaseSelenium.set_up_class()

    def __init__(self):
        super().__init__()

    @staticmethod
    def teardown():
        BaseSelenium.tear_down()  # shutdown the driver

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
        print("Changing new user DB permission completed. \n")
        self.login.logout_button()

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

    def test_views(self):
        print("---------Checking Views Begin--------- \n")
        self.login = LoginPage(self.driver)
        self.login.login('root', 'aa')
        self.views = ViewsPage(self.driver)  # creating obj for viewPage
        self.views1 = ViewsPage(self.driver)  # creating 2nd obj for viewPage to do counter part of the testing

        print("Selecting Views tab\n")
        self.views.select_views_tab()
        print("Creating first views\n")
        self.views.create_new_views()
        self.views.naming_new_view("firstView")
        self.views.select_create_btn()
        print("Creating first views completed\n")

        print("Creating second views\n")
        self.views1.create_new_views()
        self.views1.naming_new_view("secondView")
        self.views1.select_create_btn()
        print("Creating second views completed\n")

        self.views.select_views_settings()
        print("Sorting views to descending\n")
        self.views.select_sorting_views()

        print("Sorting views to ascending\n")
        self.views1.select_sorting_views()

        print("search views option testing\n")
        self.views1.search_views("se")
        self.views.search_views("fi")

        print("Selecting first Views \n")
        self.views.select_first_view()
        print("Selecting collapse button \n")
        self.views.select_collapse_btn()
        print("Selecting expand button \n")
        self.views.select_expand_btn()
        print("Selecting editor mode \n")
        self.views.select_editor_mode_btn()
        print("Switch editor mode to Code \n")
        self.views.switch_to_code_editor_mode()

        print("Selecting editor mode \n")
        self.views1.select_editor_mode_btn()
        print("Switch editor mode to Tree \n")
        self.views1.switch_to_tree_editor_mode()

        print("Clicking on ArangoSearch documentation link \n")
        self.views.click_arangosearch_documentation_link()
        print("Selecting search option\n")
        self.views.select_inside_search("i")
        print("all search results traversing results \n")
        self.views.search_result_traverse()
        self.views1.select_inside_search("")
        # print("Changing views consolidationPolicy id to 55555555 \n")
        # self.views1.change_consolidation_policy(55555555)
        print("Rename the current Views started \n")
        self.views.clicking_rename_views_btn()
        self.views.rename_views_name("thirdView")
        self.views.rename_views_name_confirm()
        print("Rename the current Views completed \n")
        self.driver.back()
        print("Deleting views started \n")
        self.views.select_renamed_view()
        self.views.delete_views_btn()
        self.views.delete_views_confirm_btn()
        self.views.final_delete_confirmation()

        self.views1.select_second_view()
        self.views1.delete_views_btn()
        self.views1.delete_views_confirm_btn()
        self.views1.final_delete_confirmation()
        print("Deleting views completed\n")
        self.login.logout_button()
        del self.login
        del self.views
        del self.views1
        print("---------Checking Views completed--------- \n")


ui = Test()  # creating obj for the UI test
ui.test_login()  # testing Login functionality
ui.test_dashboard()  # testing Dashboard functionality
ui.test_user()  # testing User functionality
ui.test_views()  # testing User functionality
ui.teardown()  # close the driver and quit
