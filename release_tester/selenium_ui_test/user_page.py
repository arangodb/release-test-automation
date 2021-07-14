import time
from base_selenium import BaseSelenium

# can't circumvent long lines..
# pylint: disable=C0301

class UserPage(BaseSelenium):
    """Class for User page"""

    def __init__(self, driver):
        """User page initialization"""
        super().__init__()
        self.driver = driver
        self.select_user_tab_id = "users"
        self.add_new_user_id = "createUser"
        self.enter_new_user_name_id = "newUsername"
        self.enter_new_name_id = "newName"
        self.enter_new_password_id = "newPassword"
        self.create_user_btn_id = "modalButton1"
        self.selecting_new_user_id = "tester"
        self.permission_link_id = "//*[@id='subNavigationBar']/ul[2]/li[2]/a"
        self.changing_db_permission_id = "//*[@id='*-db']/div[3]/input"
        self.saving_user_cfg_id = "modalButton3"
        self.select_user_delete_btn = "modalButton0"
        self.select_confirm_delete_btn = "modal-confirm-delete"

    def new_user_tab(self):
        """selecting user tab"""
        self.select_user_tab_id = BaseSelenium.locator_finder_by_id(self, self.select_user_tab_id)
        self.select_user_tab_id.click()

    def add_new_user(self):
        """User page selecting add new user"""
        self.add_new_user_id = BaseSelenium.locator_finder_by_id(self, self.add_new_user_id)
        self.add_new_user_id.click()

    def new_user_name(self, name):
        """entering new user name"""
        self.enter_new_user_name_id = BaseSelenium.locator_finder_by_id(self, self.enter_new_user_name_id)
        self.enter_new_user_name_id.click()
        self.enter_new_user_name_id.send_keys(name)
        time.sleep(3)

    def naming_new_user(self, name):
        """providing new user name"""
        self.enter_new_name_id = BaseSelenium.locator_finder_by_id(self, self.enter_new_name_id)
        self.enter_new_name_id.click()
        self.enter_new_name_id.send_keys(name)

    def new_user_password(self, password):
        """entering new user pass"""
        self.enter_new_password_id = BaseSelenium.locator_finder_by_id(self, self.enter_new_password_id)
        self.enter_new_password_id.click()
        self.enter_new_password_id.send_keys(password)

    def creating_new_user(self):
        """User page selecting add new user"""
        self.create_user_btn_id = BaseSelenium.locator_finder_by_id(self, self.create_user_btn_id)
        self.create_user_btn_id.click()
        time.sleep(3)

    def selecting_new_user(self):
        """selecting newly created user"""
        self.selecting_new_user_id = BaseSelenium.locator_finder_by_id(self, self.selecting_new_user_id)
        self.selecting_new_user_id.click()

    def selecting_permission(self):
        """selecting newly created user"""
        self.permission_link_id = BaseSelenium.locator_finder_by_xpath(self, self.permission_link_id)
        self.permission_link_id.click()

    def changing_db_permission(self):
        """changing permission for the new user"""
        self.changing_db_permission_id = BaseSelenium.locator_finder_by_xpath(self, self.changing_db_permission_id)
        self.changing_db_permission_id.click()

    def saving_user_cfg(self):
        """saving new settings for new user"""
        self.saving_user_cfg_id = BaseSelenium.locator_finder_by_id(self, self.saving_user_cfg_id)
        self.saving_user_cfg_id.click()
        time.sleep(3)

    def delete_user_btn(self):
        """deleting user"""
        self.select_user_delete_btn = BaseSelenium.locator_finder_by_id(self, self.select_user_delete_btn)
        self.select_user_delete_btn.click()

    def confirm_delete_btn(self):
        """confirming delete user"""
        self.select_confirm_delete_btn = BaseSelenium.locator_finder_by_id(self, self.select_confirm_delete_btn)
        self.select_confirm_delete_btn.click()
        time.sleep(3)
