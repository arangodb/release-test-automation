from baseSelenium import BaseSelenium


class UserPage(BaseSelenium):

    def __init__(self, driver):
        self.driver = driver
        self.select_user_tab_id = "users"
        self.add_new_user_id = "createUser"
        self.enter_new_user_name_id = "newUsername"
        self.enter_new_name_id = "newName"
        self.enter_new_password_id = "newPassword"
        self.create_user_btn_id = "modalButton1"

    # selecting user tab
    def new_user_tab(self):
        self.select_user_tab_id = BaseSelenium.locator_finder_by_id(self, self.select_user_tab_id)
        self.select_user_tab_id.click()

    # User page selecting add new user
    def add_new_user(self):
        self.add_new_user_id = BaseSelenium.locator_finder_by_id(self, self.add_new_user_id)
        self.add_new_user_id.click()

    # entering new user name
    def new_user_name(self, name):
        self.enter_new_user_name_id = BaseSelenium.locator_finder_by_id(self, self.enter_new_user_name_id)
        self.enter_new_user_name_id.click()
        self.enter_new_user_name_id.send_keys(name)

    # providing new user name
    def naming_new_user(self, name):
        self.enter_new_name_id = BaseSelenium.locator_finder_by_id(self, self.enter_new_name_id)
        self.enter_new_name_id.click()
        self.enter_new_name_id.send_keys(name)

    # entering new user pass
    def new_user_password(self, password):
        self.enter_new_password_id = BaseSelenium.locator_finder_by_id(self, self.enter_new_password_id)
        self.enter_new_password_id.click()
        self.enter_new_password_id.send_keys(password)

    # User page selecting add new user
    def crating_new_user(self):
        self.create_user_btn_id = BaseSelenium.locator_finder_by_id(self, self.create_user_btn_id)
        self.create_user_btn_id.click()
