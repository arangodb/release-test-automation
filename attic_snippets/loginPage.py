from baseSelenium import BaseSelenium


class LoginPage(BaseSelenium):

    def __init__(self, driver):
        super().__init__()
        self.driver = driver
        self.username_textbox_id = "loginUsername"
        self.password_textbox_id = "loginPassword"
        self.login_button_id = "submitLogin"
        self.select_db_opt_id = "loginDatabase"
        self.select_db_btn_id = "goToDatabase"
        self.logout_button_id = "userLogoutIcon"

    # login page entering username
    def enter_username(self, username):
        self.username_textbox_id = BaseSelenium.locator_finder_by_id(self, self.username_textbox_id)
        self.username_textbox_id.click()
        self.username_textbox_id.send_keys(username)

    # login page entering password
    def enter_password(self, password):
        self.password_textbox_id = BaseSelenium.locator_finder_by_id(self, self.password_textbox_id)
        self.password_textbox_id.click()
        self.password_textbox_id.send_keys(password)

    # login page click on login button
    def login_btn(self):
        self.login_button_id = BaseSelenium.locator_finder_by_id(self, self.login_button_id)
        self.login_button_id.click()

    # login page selecting database by default it's _system
    def select_db_opt(self):
        self.select_db_opt_id = BaseSelenium.locator_finder_by_dropdown_select(self, self.select_db_opt_id)
        self.select_db_opt_id.click()

    # select db
    def select_db(self):
        self.select_db_btn_id = BaseSelenium.locator_finder_by_id(self, self.select_db_btn_id)
        self.select_db_btn_id.click()

    '''This login method will call repeatedly before each tab test'''
    def login(self, username, password):
        print("Login begin with root user\n")
        self.enter_username(username)
        self.enter_password(password)
        self.login_btn()
        print("Selecting DB \n")
        self.select_db_opt()
        self.select_db()
        print("Login completed with root user\n")

    # selecting user logout button
    def logout_button(self):
        self.logout_button_id = BaseSelenium.locator_finder_by_id(self, self.logout_button_id)
        self.logout_button_id.click()
        print("Logout from the current user\n")
