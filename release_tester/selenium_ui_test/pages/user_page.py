#!/usr/bin/env python3
""" user page object """
import time
from collections import namedtuple

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

from selenium_ui_test.pages.navbar import NavigationBarPage

# can't circumvent long lines.. nAttr nLines
# pylint: disable=line-too-long disable=too-many-instance-attributes disable=too-many-statements


class UserPage(NavigationBarPage):
    """Class for User page"""

    def __init__(self, driver, cfg, video_start_time):
        """User page initialization"""
        super().__init__(driver, cfg, video_start_time)
        self.page_name = "user"
        # enabling external page locators for analyzer page
        ui_version = 'new_ui' if self.version_is_newer_than('3.11.99') else 'old_ui'
        elements_dict = dict(self.elements_data[self.page_name][ui_version])
        Elements = namedtuple("Elements", list(elements_dict.keys())) # pylint: disable=C0103
        self.elements = Elements(*list(elements_dict.values()))
        # page locators exposed in the test suite class
        self.a_first_collection = self.elements.header_a_first_collection
        self.m_middle_collection = self.elements.header_m_middle_collection
        self.z_last_collection = self.elements.header_z_last_collection
        self.test_doc_collection = self.elements.header_test_doc_collection

    def user_tab(self):
        """selecting user tab"""
        time.sleep(5)
        self.navbar_goto("users")
        self.wait_for_ajax()
        time.sleep(5)

    def add_new_user(self, tester):
        """User page selecting add new user"""
        self.tprint(f"New user {tester} creation begins \n")
        time.sleep(5)
        # btn_add_new_user = self.locator_finder_by_xpath_or_css_selector(self.elements.btn_add_new_user)
        self.locator_finder_by_xpath_or_css_selector(self.elements.btn_add_new_user).click()
        # time.sleep(3)
        # btn_add_new_user.click()
        time.sleep(5)

        # entering new username
        txt_new_user_name = self.locator_finder_by_xpath_or_css_selector(self.elements.txt_new_user_name)
        txt_new_user_name.click()
        txt_new_user_name.send_keys(tester)
        time.sleep(3)

        # providing new username
        txt_new_name = self.locator_finder_by_xpath_or_css_selector(self.elements.txt_new_name)
        txt_new_name.click()
        txt_new_name.send_keys(tester)

        self.tprint("Adding Gravatar email address \n")
        if self.version_is_newer_than("3.11.99"):
            txt_email_address = self.locator_finder_by_xpath_or_css_selector(self.elements.txt_email_address)
            txt_email_address.click()
            txt_email_address.send_keys("bluedio2020@gmail.com")

        self.tprint('entering new user pass \n')
        txt_new_password = self.locator_finder_by_xpath_or_css_selector(self.elements.txt_new_password)
        txt_new_password.click()
        txt_new_password.send_keys(tester)

        self.tprint('User page selecting add new user \n')
        btn_create_new_user = self.locator_finder_by_xpath_or_css_selector(self.elements.btn_create_new_user)
        btn_create_new_user.click()
        time.sleep(3)

        self.tprint(f"New user {tester} creation completed \n")

    def selecting_user_tester(self):
        """Selecting tester user with pass tester"""
        select_tester_user = self.locator_finder_by_xpath_or_css_selector(
            self.elements.select_tester_user, benchmark=True)
        select_tester_user.click()

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
            self.tprint("reloading...")
            self.webdriver.refresh()
            time.sleep(1)
            self.selecting_permission_tab()
            self.click_submenu_entry("General")

    def changing_db_permission_read_only(self):
        """changing permission for the new user to no access
        User gets db access but no creation or drop access"""
        span_db_read_only = self.locator_finder_by_xpath_or_css_selector(
            self.elements.span_db_read_only, benchmark=True)
        span_db_read_only.click()

    def changing_db_permission_read_write(self):
        """changing permission for the new user to read-write"""
        span_db_write = self.locator_finder_by_xpath_or_css_selector(self.elements.span_db_write)
        span_db_write.click()

    def saving_user_cfg(self):
        """saving new settings for new user"""
        btn_save_user_config = self.locator_finder_by_xpath_or_css_selector(self.elements.btn_save_user_config)
        btn_save_user_config.click()
        time.sleep(3)

    def selecting_new_user(self):
        """select a user"""
        select_new_tester_user = self.locator_finder_by_xpath_or_css_selector(self.elements.select_new_tester_user)
        select_new_tester_user.click()
        time.sleep(4)

    def create_sample_collection(self, test_name):
        """creating sample collection"""
        try:
            menu_item_collection_page = self.locator_finder_by_xpath_or_css_selector(
                self.elements.menu_item_collection_page)
            menu_item_collection_page.click()

            # Clicking on create new collection box
            btn_create_collection = self.locator_finder_by_xpath_or_css_selector(self.elements.btn_create_collection)

            # Check if create_collection is None and version is >= 3.11.99
            if btn_create_collection is None and self.version_is_newer_than('3.11.99'):
                self.tprint("create_collection not found, but it's expected scenario for version >= 3.11.99.")
                return  # Exit the method if element not found

            if btn_create_collection is not None:
                btn_create_collection.click()
                time.sleep(2)
            else:
                self.tprint("Element 'create_collection' option not found.")
                return  # Exit the method if element not found

            # Providing new collection name
            txt_collection_name = self.locator_finder_by_xpath_or_css_selector(self.elements.txt_collection_name)
            txt_collection_name.click()
            txt_collection_name.send_keys("testDoc")

            # creating collection by tapping on save button
            btn_save_collection = self.locator_finder_by_xpath_or_css_selector(self.elements.btn_save_collection)
            btn_save_collection.click()

            try:
                span_notification = self.locator_finder_by_xpath_or_css_selector(self.elements.span_notification)
                time.sleep(1)
                expected_text = 'Collection: Collection "testDoc" successfully created.'
                assert span_notification.text == expected_text, \
                    f"Expected text{expected_text} but got {span_notification.text}"

                try:
                    self.tprint('Deleting testDoc collection \n')
                    header_test_collection = self.locator_finder_by_xpath_or_css_selector(
                        self.elements.header_test_collection)
                    header_test_collection.click()
                    time.sleep(4)

                    tab_collection_settings = self.locator_finder_by_xpath_or_css_selector(
                        self.elements.tab_collection_settings)
                    tab_collection_settings.click()

                    btn_delete_collection = self.locator_finder_by_xpath_or_css_selector(
                        self.elements.btn_delete_collection)
                    btn_delete_collection.click()
                    time.sleep(4)

                    btn_confirm_deletion = self.locator_finder_by_xpath_or_css_selector(
                        self.elements.btn_confirm_deletion)
                    btn_confirm_deletion.click()

                    self.tprint('Deleting testDoc collection completed\n')
                except TimeoutException:
                    self.tprint('Deleting testDoc collection failed which is expected. \n')

            except TimeoutException:
                self.tprint('FAIL: Unexpected error occurred! \n')

        except TimeoutException as ex:
            if test_name == 'access':
                self.tprint("Collection creation failed, which is expected\n")
            elif test_name == 'read/write':
                raise Exception("FAIL: Unexpected error occurred!\n") from ex

    def delete_user_btn(self):
        """Delete user button"""
        btn_delete_user = self.locator_finder_by_xpath_or_css_selector(self.elements.btn_delete_user)
        btn_delete_user.click()

    def confirm_delete_btn(self):
        """Confirming the delete button press"""
        btn_confirm_user_deletion = self.locator_finder_by_xpath_or_css_selector(
            self.elements.btn_confirm_user_deletion)
        btn_confirm_user_deletion.click()
        time.sleep(3)

    def check_user_collection_sort(self):
        """This method will check user's collection sorting in user's permission tab"""
        self.tprint("check_user_collection_sort started \n")
        # selecting root user
        header_root_user = self.locator_finder_by_xpath_or_css_selector(self.elements.header_root_user)
        header_root_user.click()
        time.sleep(1)

        tab_permissions = self.locator_finder_by_xpath_or_css_selector(self.elements.tab_permissions)
        tab_permissions.click()
        time.sleep(1)

        div_system_db = self.locator_finder_by_xpath_or_css_selector(self.elements.div_system_db)
        div_system_db.click()
        time.sleep(1)

        collections_array = self.webdriver.find_elements(By.CSS_SELECTOR, self.elements.list_collections)

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
            self.tprint("Sorting check successfully completed.\n")
        else:
            raise Exception("Sorting inside user collection failed and need manual inspection!\n")
        time.sleep(15)
