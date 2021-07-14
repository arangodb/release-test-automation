from base_selenium import BaseSelenium


class LoginPage(BaseSelenium):
    """Login class for selenium UI testing"""

    def __init__(self, driver):
        """Login page initialization"""
        super().__init__()
        self.driver = driver
        self.username_textbox_id = "loginUsername"
        self.password_textbox_id = "loginPassword"
        self.login_button_id = "submitLogin"
        self.select_db_opt_id = "loginDatabase"
        self.select_db_btn_id = "goToDatabase"
        self.logout_button_id = "userLogoutIcon"

    def enter_username(self, username):
        """login page entering username"""
        self.username_textbox_id = BaseSelenium.locator_finder_by_id(self, self.username_textbox_id)
        self.username_textbox_id.click()
        self.username_textbox_id.send_keys(username)

    def enter_password(self, password):
        """login page entering password"""
        self.password_textbox_id = BaseSelenium.locator_finder_by_id(self, self.password_textbox_id)
        self.password_textbox_id.click()
        self.password_textbox_id.send_keys(password)

    def login_btn(self):
        """login page click on login button"""
        self.login_button_id = BaseSelenium.locator_finder_by_id(self, self.login_button_id)
        self.login_button_id.click()

    def select_db_opt(self, index):
        """login page selecting database by default it's _system"""
        self.select_db_opt_id = BaseSelenium.locator_finder_by_select(self, self.select_db_opt_id, index)

    def select_db(self):
        """select db"""
        self.select_db_btn_id = BaseSelenium.locator_finder_by_id(self, self.select_db_btn_id)
        self.select_db_btn_id.click()

    def login(self, username, password, db_index=0):  # 0 = default database
        """This login method will call repeatedly before each tab test"""
        print("Login begin with root user\n")
        self.enter_username(username)
        self.enter_password(password)
        self.login_btn()
        print("Selecting DB \n")
        self.select_db_opt(db_index)  # selecting default database _system
        self.select_db()
        print("Login completed with root user\n")

    def logout_button(self):
        """selecting user logout button"""
        self.logout_button_id = BaseSelenium.locator_finder_by_id(self, self.logout_button_id)
        self.logout_button_id.click()
        print("Logout from the current user\n")
