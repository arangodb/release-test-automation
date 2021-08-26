#!/usr/bin/env python
"""
aardvark ui object for users
"""
import time
from selenium_ui_test.base_selenium import BaseSelenium
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
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
        self.tester_id = '//*[@id="userManagementThumbnailsIn"]/div[3]/div/h5'
        self.general_link_id = "//*[@id='subNavigationBar']/ul[2]/li[1]/a"
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
        user_tab = self.locator_finder_by_id(self.select_user_tab_id)
        user_tab.click()

    def add_new_user(self, tester):
        """User page selecting add new user"""
        print("New user creation begins \n")
        add_new_user_sitem = self.locator_finder_by_id(self.add_new_user_id)
        add_new_user_sitem.click()

        # entering new user name
        enter_new_user_name_sitem = self.locator_finder_by_id(self.enter_new_user_name_id)
        enter_new_user_name_sitem.click()
        enter_new_user_name_sitem.send_keys(tester)
        time.sleep(3)

        # providing new user name
        enter_new_name_sitem = self.locator_finder_by_id(self.enter_new_name_id)
        enter_new_name_sitem.click()
        enter_new_name_sitem.send_keys(tester)

        # entering new user password
        enter_new_password_sitem = self.locator_finder_by_id(self.enter_new_password_id)
        enter_new_password_sitem.click()
        enter_new_password_sitem.send_keys(tester)

        # User page selecting add new user
        create_user_btn_sitem = self.locator_finder_by_id(self.create_user_btn_id)
        create_user_btn_sitem.click()
        time.sleep(3)
        print("New user creation completed \n")

    def selecting_user_tester(self):
        """selecting newly created user"""
        new_user_sitem = self.locator_finder_by_id(self.selecting_user_tester_id)
        new_user_sitem.click()

    def selecting_permission_tab(self):
        """selecting the permissions tab of the newly created user"""
        permission_sitem = self.locator_finder_by_xpath(self.permission_link_id)
        permission_sitem.click()

    def selecting_general_tab(self):
        """selecting the general tab of edited users """
        try:
            permission_sitem = self.locator_finder_by_xpath(self.general_link_id)
            permission_sitem.click()
        except StaleElementReferenceException:
            # javascript may be doing stuff to the DOM so we retry once here...
            time.sleep(1)
            permission_sitem = self.locator_finder_by_xpath(self.general_link_id)
            permission_sitem.click()

    def changing_db_permission_read_only(self):
        """changing permission for the new user"""
        db_permission_sitem = self.locator_finder_by_xpath(self.db_permission_read_only)
        db_permission_sitem.click()

    def changing_db_permission_read_write(self):
        """changing permission for the new user"""
        db_permission_sitem = self.locator_finder_by_xpath(self.db_permission_read_write)
        db_permission_sitem.click()

    def saving_user_cfg(self):
        """ saving new settings for new user """
        save_button_sitem = self.locator_finder_by_id(self.saving_user_cfg_id)
        save_button_sitem.click()
        time.sleep(3)

    def selecting_new_user(self):
        """ select a user """
        tester_sitem = self.locator_finder_by_xpath(self.tester_id)
        tester_sitem.click()
        time.sleep(4)

    def create_sample_collection(self, test_name):
        """ selecting collection tab """
        try:
            collection_page_sitem = self.locator_finder_by_id(self.select_collection_page_id)
            collection_page_sitem.click()

            # Clicking on create new collection box
            create_collection_sitem = self.locator_finder_by_id(self.select_create_collection_id)
            create_collection_sitem.click()
            time.sleep(2)

            # Providing new collection name
            collection_name_sitem = self.locator_finder_by_id(self.select_new_collection_name_id)
            collection_name_sitem.click()
            collection_name_sitem.send_keys("testDoc")

            # creating collection by tapping on save button
            save_sitem = self.locator_finder_by_id('modalButton1')
            save_sitem.click()

            try:
                notification_sitem = self.locator_finder_by_css_selectors('noty_body')
                time.sleep(1)
                expected_text = 'Collection: Collection "testDoc" successfully created.'
                assert notification_sitem.text == expected_text, f"Expected text{expected_text} but got {notification_sitem.text}"
            except TimeoutException:
                print('Unexpected error occurred!')

        except TimeoutException as ex:
            if test_name == 'access':
                print("Collection creation failed, which is expected")
            if test_name == 'read/write':
                raise Exception("Unexpected error occurred!") from ex

    def delete_user_btn(self):
        """deleting user"""
        select_user_delete_btn_sitem = self.locator_finder_by_id(self.select_user_delete_btn)
        select_user_delete_btn_sitem.click()

    def confirm_delete_btn(self):
        """confirming delete user"""
        select_confirm_delete_btn_sitem = self.locator_finder_by_id(self.select_confirm_delete_btn)
        select_confirm_delete_btn_sitem.click()
        time.sleep(3)
