#!/usr/bin/env python
"""
aardvark ui object for users
"""
import time
from selenium_ui_test.base_selenium import BaseSelenium
from selenium.common.exceptions import TimeoutException

# can't circumvent long lines.. nAttr nLines
# pylint: disable=C0301 disable=R0902 disable=R0915

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
        self.selecting_user_tester_id = "tester"
        self.permission_link_id = "//*[@id='subNavigationBar']/ul[2]/li[2]/a"
        self.db_permission_read_only = "//*[@id='*-db']/div[3]/input"
        self.db_permission_read_write = '//*[@id="*-db"]/div[2]/input'
        self.saving_user_cfg_id = "modalButton3"
        self.select_user_delete_btn = "modalButton0"
        self.select_confirm_delete_btn = "modal-confirm-delete"
        self.select_collection_page_id = "collections"
        self.select_create_collection_id = "createCollection"
        self.select_new_collection_name_id = "new-collection-name"

    def user_tab(self):
        """selecting user tab"""
        user_tab = self.select_user_tab_id
        user_tab = BaseSelenium.locator_finder_by_id(self, user_tab)
        user_tab.click()

    def add_new_user(self, tester):
        """User page selecting add new user"""
        print("New user creation begins \n")
        self.add_new_user_id = BaseSelenium.locator_finder_by_id(self, self.add_new_user_id)
        self.add_new_user_id.click()

        # entering new user name
        self.enter_new_user_name_id = BaseSelenium.locator_finder_by_id(self, self.enter_new_user_name_id)
        self.enter_new_user_name_id.click()
        self.enter_new_user_name_id.send_keys(tester)
        time.sleep(3)

        # providing new user name
        self.enter_new_name_id = BaseSelenium.locator_finder_by_id(self, self.enter_new_name_id)
        self.enter_new_name_id.click()
        self.enter_new_name_id.send_keys(tester)

        # entering new user password
        self.enter_new_password_id = BaseSelenium.locator_finder_by_id(self, self.enter_new_password_id)
        self.enter_new_password_id.click()
        self.enter_new_password_id.send_keys(tester)

        # User page selecting add new user
        self.create_user_btn_id = BaseSelenium.locator_finder_by_id(self, self.create_user_btn_id)
        self.create_user_btn_id.click()
        time.sleep(3)
        print("New user creation completed \n")

    def selecting_user_tester(self):
        """selecting newly created user"""
        new_user = self.selecting_user_tester_id
        new_user = BaseSelenium.locator_finder_by_id(self, new_user)
        new_user.click()

    def selecting_permission(self):
        """selecting newly created user"""
        permission = self.permission_link_id
        permission = BaseSelenium.locator_finder_by_xpath(self, permission)
        permission.click()

    def changing_db_permission_read_only(self):
        """changing permission for the new user"""
        db_permission = self.db_permission_read_only
        db_permission = BaseSelenium.locator_finder_by_xpath(self, db_permission)
        db_permission.click()

    def changing_db_permission_read_write(self):
        """changing permission for the new user"""
        db_permission = self.db_permission_read_write
        db_permission = BaseSelenium.locator_finder_by_xpath(self, db_permission)
        db_permission.click()

    # saving new settings for new user
    def saving_user_cfg(self):
        save_button = self.saving_user_cfg_id
        save_button = BaseSelenium.locator_finder_by_id(self, save_button)
        save_button.click()
        time.sleep(3)

    def selecting_new_user(self):
        tester = '//*[@id="userManagementThumbnailsIn"]/div[3]/div/h5'
        tester = BaseSelenium.locator_finder_by_xpath(self, tester)
        tester.click()
        time.sleep(4)

    def create_sample_collection(self, test_name):
        # selecting collection tab
        try:
            collection_page = self.select_collection_page_id
            collection_page = \
                BaseSelenium.locator_finder_by_id(self, collection_page)
            collection_page.click()

            # Clicking on create new collection box
            create_collection = self.select_create_collection_id
            create_collection = \
                BaseSelenium.locator_finder_by_id(self, create_collection)
            create_collection.click()
            time.sleep(2)

            # Providing new collection name
            collection_name = self.select_new_collection_name_id
            collection_name = \
                BaseSelenium.locator_finder_by_id(self, collection_name)
            collection_name.click()
            collection_name.send_keys("testDoc")

            # creating collection by tapping on save button
            save = 'modalButton1'
            save = BaseSelenium.locator_finder_by_id(self, save)
            save.click()

            try:
                notification = 'noty_body'
                notification = self.locator_finder_by_css_selectors(notification)
                time.sleep(1)
                expected_text = 'Collection: Collection "testDoc" successfully created.'
                assert notification.text == expected_text, f"Expected text{expected_text} but got {notification.text}"
            except TimeoutException:
                print('Unexpected error occurred!')

        except TimeoutException:
            if test_name == 'access':
                print("Collection creation failed, which is expected")
            if test_name == 'read/write':
                raise Exception("Unexpected error occurred!")

    def delete_user_btn(self):
        """deleting user"""
        self.select_user_delete_btn = BaseSelenium.locator_finder_by_id(self, self.select_user_delete_btn)
        self.select_user_delete_btn.click()

    def confirm_delete_btn(self):
        """confirming delete user"""
        self.select_confirm_delete_btn = BaseSelenium.locator_finder_by_id(self, self.select_confirm_delete_btn)
        self.select_confirm_delete_btn.click()
        time.sleep(3)
