from baseSelenium import BaseSelenium


class LoginPage(BaseSelenium):

    def __init__(self, driver):
        self.driver = driver
        self.username_textbox_id = "loginUsername"
        self.password_textbox_id = "loginPassword"
        self.login_button_id = "submitLogin"
        self.select_db_btn = "goToDatabase"

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

    # login page selecting default database
    def select_db(self):
        self.select_db_btn = BaseSelenium.locator_finder_by_id(self, self.select_db_btn)
        self.select_db_btn.click()

