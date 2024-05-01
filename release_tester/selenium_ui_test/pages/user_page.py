#!/usr/bin/env python3
""" user page object """
import time
from selenium_ui_test.pages.navbar import NavigationBarPage
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium_ui_test.pages.base_page import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException

# can't circumvent long lines.. nAttr nLines
# pylint: disable=line-too-long disable=too-many-instance-attributes disable=too-many-statements


class UserPage(NavigationBarPage):
    """Class for User page"""

    def __init__(self, driver, cfg):
        """User page initialization"""
        super().__init__(driver, cfg)
        self.add_new_user_id = "createUser"
        self.enter_new_user_name_id = "newUsername"
        self.enter_new_name_id = "newName"
        self.enter_new_password_id = "newPassword"
        self.create_user_btn_id = "modalButton1"
        self.selecting_user_tester_id = "tester"
        self.select_tester_id = "//*[contains(text(),'tester ')]"
        self.permission_link_id = "//*[@id='subNavigationBarPage']/ul[2]/li[2]/a"
        self.db_permission_read_only = "//*[@id='*-db']/div[3]/input"
        self.db_permission_read_write = '//*[@id="*-db"]/div[2]/input'
        self.saving_user_cfg_id = "modalButton3"
        self.select_user_delete_btn = "modalButton0"
        self.select_confirm_delete_btn = "modal-confirm-delete"
        self.select_collection_page_id = "collections"
        self.select_create_collection_id = "createCollection"
        self.select_new_collection_name_id = "new-collection-name"
        self.a_first_id = '//h5[@class="collectionName"][text()="a_first"]'
        self.m_middle_id = '//h5[@class="collectionName"][text()="m_middle"]'
        self.z_last_id = '//h5[@class="collectionName"][text()="z_last"]'
        self.test_doc_collection_id = '//h5[@class="collectionName"][text()="testDoc"]'

    def user_tab(self):
        """selecting user tab"""
        self.navbar_goto("users")

    def add_new_user(self, tester):
        """User page selecting add new user"""
        print(f"New user {tester} creation begins \n")
        if self.version_is_newer_than("3.11.99"):
            new_user = "(//button[normalize-space()='Add user'])[1]"
            add_new_user_id_sitem = self.locator_finder_by_xpath(new_user)
        else:
            new_user = "createUser"
            add_new_user_id_sitem = self.locator_finder_by_id(new_user)
        add_new_user_id_sitem.click()

        # entering new user name
        if self.version_is_newer_than("3.11.99"):
            new_user_name = "(//input[@id='user'])[1]"
            enter_new_user_name_id_sitem = self.locator_finder_by_xpath(new_user_name)
        else:
            new_user_name = self.enter_new_user_name_id
            enter_new_user_name_id_sitem = self.locator_finder_by_id(new_user_name)
        enter_new_user_name_id_sitem.click()
        enter_new_user_name_id_sitem.send_keys(tester)
        time.sleep(3)

        # providing new username
        if self.version_is_newer_than("3.11.99"):
            new_name = "(//input[@id='name'])[1]"
            enter_new_name_id_sitem = self.locator_finder_by_xpath(new_name)
        else:
            new_name = self.enter_new_name_id
            enter_new_name_id_sitem = self.locator_finder_by_id(new_name)
        enter_new_name_id_sitem.click()
        enter_new_name_id_sitem.send_keys(tester)

        print("Adding Gravatar email address \n")
        if self.version_is_newer_than("3.11.99"):
            new_name = "(//input[@id='extra.img'])[1]"
            enter_new_name_id_sitem = self.locator_finder_by_xpath(new_name)
            enter_new_name_id_sitem.click()
            enter_new_name_id_sitem.send_keys("bluedio2020@gmail.com")

        print('entering new user pass \n')
        if self.version_is_newer_than("3.11.99"):
            new_password = "(//input[@id='passwd'])[1]"
            enter_new_password_id_sitem = self.locator_finder_by_xpath(new_password)
        else:
            new_password = self.enter_new_password_id
            enter_new_password_id_sitem = self.locator_finder_by_id(new_password)
        enter_new_password_id_sitem.click()
        enter_new_password_id_sitem.send_keys(tester)

        print('User page selecting add new user \n')
        if self.version_is_newer_than("3.11.99"):
            create_user = "(//button[normalize-space()='Create'])[1]"
            create_user_btn_id_sitem = self.locator_finder_by_xpath(create_user)
        else:
            create_user = self.create_user_btn_id
            create_user_btn_id_sitem = self.locator_finder_by_id(create_user)

        create_user_btn_id_sitem.click()
        time.sleep(3)
        print(f"New user {tester} creation completed \n")
    def selecting_user_tester(self):
        """Selecting tester user with pass tester"""
        if self.version_is_newer_than("3.11.99"):
            new_user = "(//a[normalize-space()='tester'])[1]"
            new_user = self.locator_finder_by_xpath(new_user)
            new_user.click()
        else:
            new_user = self.selecting_user_tester_id
            new_user = self.locator_finder_by_id(new_user)
            new_user.click()

    def selecting_permission_tab(self):
        """selecting the permissions tab of the newly created user"""
        self.click_submenu_entry("Permissions")

    def selecting_general_tab(self):
        """selecting the general tab of edited users"""
        try:
            self.wait_for_ajax()
            self.click_submenu_entry("General")
        except StaleElementReferenceException:
            # javascript may be doing stuff to the DOM so we retry once here...
            print("reloading...")
            self.webdriver.refresh()
            time.sleep(1)
            self.selecting_permission_tab()
            self.click_submenu_entry("General")

    def changing_db_permission_read_only(self):
        """changing permission for the new user to no access
        User gets db access but no creation or drop access"""
        if self.version_is_newer_than("3.11.99"):
            db_permission = "(//span[@aria-hidden='true'])[6]"
        else:
            db_permission = self.db_permission_read_only
        db_permission = self.locator_finder_by_xpath(db_permission)
        db_permission.click()

    def changing_db_permission_read_write(self):
        """changing permission for the new user to read-write"""
        if self.version_is_newer_than("3.11.99"):
            db_permission = '//*[@id="content-react"]/div/div[2]/div/table/tbody/tr[1]/td[2]/div/label/span'
        else:
            db_permission = self.db_permission_read_write
        db_permission = self.locator_finder_by_xpath(db_permission)
        db_permission.click()

    def saving_user_cfg(self):
        """saving new settings for new user"""
        save_button_sitem = self.locator_finder_by_id(self.saving_user_cfg_id)
        save_button_sitem.click()
        time.sleep(3)

    def selecting_new_user(self):
        """select a user"""
        if self.version_is_newer_than("3.11.99"):
            tester = "(//a[normalize-space()='tester'])[1]"
        else:
            tester = self.select_tester_id
        tester = self.locator_finder_by_xpath(tester)
        tester.click()
        time.sleep(4)

    def create_sample_collection(self, test_name):
        """creating sample collection"""
        try:
            collection_page = self.locator_finder_by_id(self.select_collection_page_id)
            collection_page.click()

            # Clicking on create new collection box
            create_collection = self.locator_finder_by_id(self.select_create_collection_id)

            # Check if create_collection is None and version is >= 3.11.99
            if create_collection is None and self.version_is_newer_than('3.11.99'):
                print("create_collection not found, but it's expected scenario for version >= 3.11.99.")
                return  # Exit the method if element not found

            if create_collection is not None:
                create_collection.click()
                time.sleep(2)
            else:
                print("Element 'create_collection' option not found.")
                return  # Exit the method if element not found

            # Providing new collection name
            collection_name = self.select_new_collection_name_id
            collection_name = self.locator_finder_by_id(collection_name)
            collection_name.click()
            collection_name.send_keys("testDoc")

            # creating collection by tapping on save button
            save = 'modalButton1'
            save = self.locator_finder_by_id(save)
            save.click()

            try:
                notification = 'noty_body'
                notification = self.locator_finder_by_class(notification)
                time.sleep(1)
                expected_text = 'Collection: Collection "testDoc" successfully created.'
                assert notification.text == expected_text, f"Expected text{expected_text} but got {notification.text}"

                try:
                    print('Deleting testDoc collection \n')

                    select_test_doc_collection_id = '//*[@id="collection_testDoc"]/div/h5'
                    select_collection_settings_id = "//*[@id='subNavigationBar']/ul[2]/li[4]/a"
                    select_test_doc_collection_id = self.locator_finder_by_xpath(select_test_doc_collection_id)
                    select_test_doc_collection_id.click()

                    time.sleep(4)
                    select_test_doc_settings_id = self.locator_finder_by_xpath(select_collection_settings_id)
                    select_test_doc_settings_id.click()

                    delete_collection_id = "//*[@id='modalButton0']"
                    delete_collection_confirm_id = "//*[@id='modal-confirm-delete']"

                    delete_collection_id = self.locator_finder_by_xpath(delete_collection_id)
                    delete_collection_id.click()
                    time.sleep(4)
                    delete_collection_confirm_id = self.locator_finder_by_xpath(delete_collection_confirm_id)
                    delete_collection_confirm_id.click()

                    print('Deleting testDoc collection completed\n')
                except TimeoutException:
                    print('Deleting testDoc collection failed which is expected. \n')

            except TimeoutException:
                print('FAIL: Unexpected error occurred! \n')

        except TimeoutException:
            if test_name == 'access':
                print("Collection creation failed, which is expected\n")
            elif test_name == 'read/write':
                raise Exception("FAIL: Unexpected error occurred!\n")
    
    def delete_user_btn(self):
        """Delete user button"""
        if self.version_is_newer_than("3.11.99"):
            select_user_delete_btn = "(//button[normalize-space()='Delete'])[1]"
            select_user_delete_btn_sitem = self.locator_finder_by_xpath(select_user_delete_btn)
        else:
            select_user_delete_btn = "modalButton0"
            select_user_delete_btn_sitem = self.locator_finder_by_id(select_user_delete_btn)
        select_user_delete_btn_sitem.click()

    def confirm_delete_btn(self):
        """Confirming the delete button press"""
        if self.version_is_newer_than("3.11.99"):
            select_confirm_delete_btn = "(//button[normalize-space()='Yes'])[1]"
            select_confirm_delete_btn_sitem = self.locator_finder_by_xpath(select_confirm_delete_btn)
        else:
            select_confirm_delete_btn = "modal-confirm-delete"
            select_confirm_delete_btn_sitem = self.locator_finder_by_id(select_confirm_delete_btn)
        select_confirm_delete_btn_sitem.click()
        time.sleep(3)

    def check_user_collection_sort(self):
        """This method will check user's collection sorting in user's permission tab"""
        print("check_user_collection_sort started \n")
        # selecting root user
        root_user = '//h5[@class="collectionName"][text()="root "]'
        root_user_sitem = self.locator_finder_by_xpath(root_user)
        root_user_sitem.click()
        time.sleep(1)

        permission_tab = '//li[@class="subMenuEntry "]//a[text()="Permissions"]'
        permission_tab_sitem = self.locator_finder_by_xpath(permission_tab)
        permission_tab_sitem.click()
        time.sleep(1)

        select_system_db = '//*[@id="_system-db"]/div[1]'
        select_system_db_sitem = self.locator_finder_by_xpath(select_system_db)
        select_system_db_sitem.click()
        time.sleep(1)

        col_id_list = '//*[@class="collName"]'
        collections_array = self.webdriver.find_elements(By.XPATH, col_id_list)

        a_first, m_middle, z_last = 0,0,0
        # this loop will run through all the collections and find the index for desired one
        for index, item in enumerate(collections_array):
            if item.text == "a_first":
                a_first = index
            elif item.text == "m_middle":
                m_middle = index
            elif item.text == "z_last":
                z_last = index
            else:
                pass

        if a_first < m_middle < z_last:
            print("Sorting check successfully completed.\n")
        else:
            raise Exception("Sorting inside user collection failed and need manual inspection!\n")
