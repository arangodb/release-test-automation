#!/usr/bin/env python3
""" database page object """
import time
import semver
import traceback
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium_ui_test.pages.navbar import NavigationBarPage

# pylint: disable=too-many-statements
class DatabasePage(NavigationBarPage):
    """ database page object """
    def __init__(self, webdriver, cfg):
        super().__init__(webdriver, cfg)
        self.database_page = "databases"
        self.create_new_db_btn = "createDatabase"
        self.sort_db = '//*[@id="databaseDropdown"]/ul/li[2]/a/label/i'
        self.select_db_opt_id_sitem = "loginDatabase"

    def create_new_db(self, db_name, index, cluster, enterprise):
        """Creating and checking new database"""
        # pylint: disable=too-many-locals
        self.navbar_goto("databases")
        self.wait_for_ajax()
        self.tprint(f'Creating {db_name} database started \n')
        if self.version_is_newer_than("3.11.99"):
            create_new_db_btn = "(//button[normalize-space()='Add database'])[1]"
            create_new_db_btn_sitem = self.locator_finder_by_xpath(create_new_db_btn)
        else:
            create_new_db_btn = self.create_new_db_btn
            create_new_db_btn_sitem = self.locator_finder_by_id(create_new_db_btn)

        create_new_db_btn_sitem.click()
        time.sleep(2)

        self.tprint("fill up all the database details \n")
        if self.version_is_newer_than("3.11.99"):
            new_db_name = "(//input[@id='name'])[1]"
            new_db_name_sitem = self.locator_finder_by_xpath(new_db_name)
        else:
            new_db_name = 'newDatabaseName'
            new_db_name_sitem = self.locator_finder_by_id(new_db_name)

        new_db_name_sitem.click()
        new_db_name_sitem.send_keys(db_name)
        time.sleep(1)

        if cluster:
            self.tprint(f"Cluster deployment selected for {db_name} \n")
            if self.version_is_newer_than("3.11.99"):
                replication_factor = 'replicationFactor'
            else:
                replication_factor = 'new-replication-factor'
            
            replication_factor_sitem = self.locator_finder_by_id(replication_factor)
            replication_factor_sitem.click()
            if self.version_is_newer_than("3.11.99"):
                self.send_key_action(Keys.BACKSPACE)
                self.send_key_action(Keys.BACKSPACE)
            else:
                replication_factor_sitem.clear()

            replication_factor_sitem.send_keys("3")
            time.sleep(1)

            if self.version_is_newer_than("3.11.99"):
                write_concern = 'writeConcern'
            else:
                write_concern = 'new-write-concern'
            
            write_concern_sitem = self.locator_finder_by_id(write_concern)
            write_concern_sitem.click()
            if self.version_is_newer_than("3.11.99"):
                self.send_key_action(Keys.BACKSPACE)
                self.send_key_action(Keys.BACKSPACE)
            else:
                write_concern_sitem.clear()
            write_concern_sitem.send_keys("3")
            time.sleep(1)

            if enterprise:
                if self.version_is_newer_than("3.11.99"):
                    self.tprint(f"selecting one shard database for {db_name}\n")
                    if db_name == "OneShard":
                        one_shard = '//*[@id="chakra-modal--body-4"]/div/div/div[2]/div[5]/div/div/label/span/span'
                        one_shard_sitem = self.locator_finder_by_xpath(one_shard)
                        one_shard_sitem.click()
                    else:
                        pass
                else:
                    self.tprint(f"selecting sharded option from drop down using index for {db_name}\n")
                    select_sharded_db = "newSharding"
                    self.locator_finder_by_select(select_sharded_db, index)
                    time.sleep(1)
            else:
                self.tprint(f"Skipped for Community or < v3.11.99 for {db_name}\n")

        self.tprint(f"selecting user option from drop down using index for choosing root user for {db_name} \n")
        if self.version_is_newer_than("3.11.99"):
            select_user = "(//input[@id='users'])[1]"
            select_user_sitem = self.locator_finder_by_xpath(select_user)  # 0 for root user
            select_user_sitem.send_keys("tester")
            actions = ActionChains(self.webdriver)
            actions.send_keys(Keys.RETURN)
            actions.perform()
            time.sleep(1)

        else:
            select_user = "newUser"
            self.locator_finder_by_select(select_user, 0)  # 0 for root user
            time.sleep(1)

        # clicking create button
        if self.version_is_newer_than("3.11.99"):
            create_db = "(//button[normalize-space()='Create'])[1]"
            create_db_sitem = self.locator_finder_by_xpath(create_db)
        else:
            create_db = "modalButton1"
            create_db_sitem = self.locator_finder_by_id(create_db)
        
        create_db_sitem.click()
        time.sleep(4)
        self.tprint(f"Creating {db_name} database completed \n")
        
        if self.current_package_version() < semver.VersionInfo.parse("3.11.0"):
            self.tprint(f"Logging into newly created {db_name} database \n")
            change_db = '//*[@id="dbStatus"]/a[3]/i'
            change_db_sitem = self.locator_finder_by_xpath(change_db)
            change_db_sitem.click()
            time.sleep(5)

            db_opt = self.select_db_opt_id_sitem
            self.tprint("Database checked and found: ", db_name, "\n")
            time.sleep(4)

            if db_name == "Sharded":
                # selecting newly created db for login from the dropdown menu
                self.locator_finder_by_select(db_opt, 0)
            if db_name == "OneShard":
                # OneShard took place over Sharded database thus used index value 1
                self.locator_finder_by_select(db_opt, 1)

            select_db_btn_id = "goToDatabase"
            select_db_btn_id_sitem = self.locator_finder_by_id(select_db_btn_id)
            select_db_btn_id_sitem.click()
            time.sleep(2)

            db_name = '//*[@id="dbStatus"]/a[2]/span'
            db_name_sitem = self.locator_finder_by_xpath(db_name).text

            if index == 0:
                assert db_name_sitem == "SHARDED", f"Expected SHARDED but got {db_name_sitem}"
            if index == 1:
                assert db_name_sitem == "ONESHARD", f"Expected ONESHARD but got {db_name_sitem}"

            self.tprint(f"Logging out from {db_name_sitem} database \n")
            db_id = '//*[@id="dbStatus"]/a[3]/i'
            change_db_sitem = self.locator_finder_by_xpath(db_id)
            change_db_sitem.click()
            time.sleep(4)

            self.tprint("Re-Login to _system database \n")
            db_option = self.select_db_opt_id_sitem
            self.locator_finder_by_select(db_option, 0)
            select_db_btn_id = "goToDatabase"
            select_db_btn_id_sitem = self.locator_finder_by_id(select_db_btn_id)
            select_db_btn_id_sitem.click()
            time.sleep(3)
        self.navbar_goto("databases")
        self.wait_for_ajax()

    def test_database_expected_error(self, cluster):
        """This method will test all negative scenario"""
        # pylint: disable=too-many-statements disable=too-many-statements  disable=too-many-locals
        self.navbar_goto("databases")
        self.wait_for_ajax()
        self.tprint("Expected error scenario for the Database name Started. \n")
        create_new_db_btn = self.create_new_db_btn
        create_new_db_btn_sitem = self.locator_finder_by_id(create_new_db_btn)
        create_new_db_btn_sitem.click()
        time.sleep(2)

        # ---------------------------------------database name convention test---------------------------------------
        self.tprint("Expected error scenario for the Database name Started \n")

        ver_db_names = semver.VersionInfo.parse("3.9.0")
        ver_db_replf = semver.VersionInfo.parse("3.8.0")
        version = self.current_package_version()
        
        if version >= ver_db_names:
            db_name_error_input = ["1", ".", "/"]  # name must be 64 bit thus 65 character won't work too.
            db_name_print_statement = [
                'Checking numeric value for DB name " 1 "',
                'Checking with dot value "."',
                'Checking with slash "/"',
            ]
            if version >= "3.10.0":
                db_name_error_message = [
                "DB: Invalid parameters: database name invalid",
                "DB: Invalid parameters: database name invalid",
                "DB: Invalid parameters: database name invalid"
                ]
            else:
                db_name_error_message = [
                "DB: Invalid Parameters: database name invalid",
                "DB: Invalid Parameters: database name invalid",
                "DB: Invalid Parameters: database name invalid"
                ]
            db_name = "newDatabaseName"
            db_name_error = "/html/body/div[10]/div/div[1]"
        else:
            db_name_error_input = ["", "@", "1", "שלום"]  # name must be 64 bit thus 65 character won't work too.
            db_name_print_statement = [
                'Checking blank DB name with " "',
                'Checking Db name with symbol " @ "',
                'Checking numeric value for DB name " 1 "',
                'Checking Non-ASCII Hebrew Characters "שלום"',
            ]
            db_name_error_message = [
                "No database name given.",
                'Only Symbols "_" and "-" are allowed.',
                "Database name must start with a letter.",
                'Only Symbols "_" and "-" are allowed.',
            ]
            db_name = "newDatabaseName"
            db_name_error = '//*[@id="row_newDatabaseName"]/th[2]/p'

        # method template (self, error_input, print_statement, error_message, locators_id, error_message_id)
        self.check_expected_error_messages_for_database(
            db_name_error_input, db_name_print_statement, db_name_error_message, db_name, db_name_error
        )
        self.tprint("Expected error scenario for the Database name Completed \n")

        if cluster and version >= ver_db_names:
            db_sitem = self.locator_finder_by_id("newDatabaseName")
            db_sitem.click()
            db_sitem.clear()
            db_sitem.send_keys("db")
            time.sleep(2)
            # ----------------------------database Replication Factor convention test-----------------------------
            self.tprint("Expected error scenario for the Database Replication Factor Started \n")
            rf_error_input = ["@", "a", "11", "שלום"]
            rf_print_statement = [
                'Checking RF with "@"',
                'Checking RF with "a"',
                'Checking RF with "11"',
                'Checking RF with "שלום"',
            ]
            rf_error_message = [
                "Must be a number between 1 and 10.",
                "Must be a number between 1 and 10.",
                "Must be a number between 1 and 10.",
                "Must be a number between 1 and 10.",
            ]
            rf_name = "new-replication-factor"
            db_name_error_id = '//*[@id="row_new-replication-factor"]/th[2]/p'

            # method template (self, error_input, print_statement, error_message, locators_id, error_message_id)
            self.check_expected_error_messages_for_database(
                rf_error_input, rf_print_statement, rf_error_message, rf_name, db_name_error_id, True
            )  # True defines cluster deployment
            self.tprint("Expected error scenario for the Database Replication Factor Completed \n")

            # -------------------------------database Write Concern convention test----------------------------------
            self.tprint("Expected error scenario for the Database Write Concern Started \n")
            wc_error_input = ["@", "a", "11", "שלום"]
            wc_print_statement = [
                'Checking Write Concern with "@"',
                'Checking Write Concern with "a"',
                'Checking Write Concern with "11"',
                'Checking Write Concern with "שלום"',
            ]
            wc_error_message = [
                "Must be a number between 1 and 10. Has to be smaller or equal compared to the replicationFactor.",
                "Must be a number between 1 and 10. Has to be smaller or equal compared to the replicationFactor.",
                "Must be a number between 1 and 10. Has to be smaller or equal compared to the replicationFactor.",
                "Must be a number between 1 and 10. Has to be smaller or equal compared to the replicationFactor.",
            ]
            wc_name = "new-write-concern"
            wc_name_error_id = '//*[@id="row_new-write-concern"]/th[2]/p'

            # method template (self, error_input, print_statement, error_message, locators_id, error_message_id)
            self.check_expected_error_messages_for_database(
                wc_error_input, wc_print_statement, wc_error_message, wc_name, wc_name_error_id, True
            )
            self.tprint("Expected error scenario for the Database Write Concern Completed \n")

        if cluster and version == ver_db_replf:
            # -------------------------------database Replication Factor convention test------------------------------
            self.tprint("Expected error scenario for the Database Replication Factor Started \n")
            rf_error_input = ["@", "a", "11", "שלום"]
            rf_print_statement = [
                'Checking RF with "@"',
                'Checking RF with "a"',
                'Checking RF with "11"',
                'Checking RF with "שלום"',
            ]
            rf_error_message = [
                "Must be a number between 1 and 10.",
                "Must be a number between 1 and 10.",
                "Must be a number between 1 and 10.",
                "Must be a number between 1 and 10.",
            ]
            rf_name = "new-replication-factor"
            db_name_error = '//*[@id="row_new-replication-factor"]/th[2]/p'

            # method template (self, error_input, print_statement, error_message, locators_id, error_message_id)
            self.check_expected_error_messages_for_database(
                rf_error_input, rf_print_statement, rf_error_message, rf_name, db_name_error
            )
            self.tprint("Expected error scenario for the Database Replication Factor Completed \n")

            # -------------------------------database Write Concern convention test----------------------------------
            self.tprint("Expected error scenario for the Database Write Concern Started \n")
            wc_error_input = ["@", "a", "11", "שלום"]
            wc_print_statement = [
                'Checking Write Concern with "@"',
                'Checking Write Concern with "a"',
                'Checking Write Concern with "11"',
                'Checking Write Concern with "שלום"',
            ]
            wc_error_message = [
                "Must be a number between 1 and 10. Has to be smaller or equal compared to the replicationFactor.",
                "Must be a number between 1 and 10. Has to be smaller or equal compared to the replicationFactor.",
                "Must be a number between 1 and 10. Has to be smaller or equal compared to the replicationFactor.",
                "Must be a number between 1 and 10. Has to be smaller or equal compared to the replicationFactor.",
            ]
            wc_name = "new-write-concern"
            wc_name_error = '//*[@id="row_new-write-concern"]/th[2]/p'

            # method template (self, error_input, print_statement, error_message, locators_id, error_message_id)
            self.check_expected_error_messages_for_database(
                wc_error_input, wc_print_statement, wc_error_message, wc_name, wc_name_error
            )
            self.tprint("Expected error scenario for the Database Write Concern Completed \n")

        self.tprint("Closing the database creation \n")
        close_btn = "modalButton0"
        close_btn_sitem = self.locator_finder_by_id(close_btn)
        close_btn_sitem.click()
        time.sleep(3)

    def sorting_db(self):
        """Sorting database"""
        self.wait_for_ajax()
        db_settings = "databaseToggle"
        db_settings_sitem = self.locator_finder_by_id(db_settings)
        db_settings_sitem.click()
        time.sleep(1)

        ascending = self.sort_db
        ascending_sitem = self.locator_finder_by_xpath(ascending)
        ascending_sitem.click()
        time.sleep(2)

        descending = self.sort_db
        descending_sitem = self.locator_finder_by_xpath(descending)
        descending_sitem.click()
        time.sleep(2)

    def searching_db(self, db_name):
        """Searching database"""
        self.wait_for_ajax()
        db_search = "databaseSearchInput"
        db_search_sitem = self.locator_finder_by_id(db_search)
        db_search_sitem.click()
        db_search_sitem.clear()
        db_search_sitem.send_keys(db_name)
        time.sleep(2)

        try:
            collection_name = '//*[@id="userManagementView"]/div/div[2]/div/h5'
            collection_name_sitem = self.locator_finder_by_xpath(collection_name).text

            if db_name == "Sharded":
                assert collection_name_sitem == "Sharded", f"Expected {db_name} but got {collection_name_sitem}"
            elif db_name == "OneShard":
                assert collection_name_sitem == "OneShard", f"Expected {db_name} but got {collection_name_sitem}"

        except TimeoutException():
            self.tprint("Error Occurred! \n")

        self.tprint("Clearing the search text area \n")
        clear_search = "databaseSearchInput"
        clear_search_sitem = self.locator_finder_by_id(clear_search)
        clear_search_sitem.click()
        clear_search_sitem.clear()
        time.sleep(2)

    def deleting_database(self, db_name):
        """Deleting Database"""
        self.wait_for_ajax()
        try:
            self.webdriver.refresh()
            self.navbar_goto("databases")
            self.wait_for_ajax()

            self.tprint(f'{db_name} deleting started \n')
            if db_name == 'OneShard':
                if self.version_is_newer_than("3.11.99"):
                    db_select = "(//a[normalize-space()='OneShard'])[1]"
                    db_select_sitem = self.locator_finder_by_xpath(db_select)
                    db_select_sitem.click()
                    time.sleep(1)
                else:
                    db_search = 'OneShard_edit-database'
                    db_sitem = self.locator_finder_by_id(db_search)
                    db_sitem.click()

            else:
                # for sharded database deletion
                if self.version_is_newer_than("3.11.99"):
                    db_select = "(//a[normalize-space()='Sharded'])[1]"
                    db_select_sitem = self.locator_finder_by_xpath(db_select)
                    db_select_sitem.click()
                    time.sleep(1)
                else:
                    db_search = 'Sharded_edit-database'
                    db_sitem = self.locator_finder_by_id(db_search)
                    db_sitem.click()

            if self.version_is_newer_than('3.11.99'):
                delete_btn = "(//button[normalize-space()='Delete'])[1]"
                delete_btn_sitem = self.locator_finder_by_xpath(delete_btn)
            else:
                delete_btn = 'modalButton1'
                delete_btn_sitem = self.locator_finder_by_id(delete_btn)

            delete_btn_sitem.click()
            time.sleep(1)

            if self.version_is_newer_than("3.11.99"):
                delete_confirm_btn = '//footer//button[2]'
                delete_confirm_btn_sitem = self.locator_finder_by_xpath(delete_confirm_btn)
            else:
                delete_confirm_btn = 'modal-confirm-delete'
                delete_confirm_btn_sitem = self.locator_finder_by_id(delete_confirm_btn)

            delete_confirm_btn_sitem.click()
            time.sleep(1)

            self.webdriver.refresh()

            self.tprint(f'{db_name} deleting completed \n')
        except TimeoutException:
            self.tprint('TimeoutException occurred! \n')
            self.tprint('Info: Database has already been deleted or never created. \n')
        except Exception:
            raise Exception('Critical Error occurred and need manual inspection!! \n')

    
    def deleting_user(self, username):
        """Deleting users created for the Database test"""
        self.wait_for_ajax()
        try:
            self.webdriver.refresh()
            self.tprint('Selecting user for deletion \n')
            if self.version_is_newer_than("3.11.99"):
                tester = "(//a[normalize-space()='tester'])[1]"
                tester01 = "(//a[normalize-space()='tester01'])[1]"
            else:
                tester = "//h5[text()='tester (tester)']"
                tester01 = "//h5[text()='tester01 (tester01)']"

            if username == 'tester':
                self.locator_finder_by_xpath(tester).click()
            elif username == 'tester01':
                self.locator_finder_by_xpath(tester01).click()
            else:
                raise Exception('Wrong user has been chosen for deletion!!! \n')
            time.sleep(2)

            if self.version_is_newer_than("3.11.99"):
                select_user_delete_btn = "(//button[normalize-space()='Delete'])[1]"
                select_user_delete_btn_sitem = self.locator_finder_by_xpath(select_user_delete_btn)
                select_user_delete_btn_sitem.click()

                select_confirm_delete_btn = "(//button[normalize-space()='Yes'])[1]"
                select_confirm_delete_btn_sitem = self.locator_finder_by_xpath(select_confirm_delete_btn)
                select_confirm_delete_btn_sitem.click()
            else:
                self.tprint(f'Deleting {username} begins \n')
                del_button = 'modalButton0'
                self.locator_finder_by_id(del_button).click()

                # confirming delete user
                confirm_btn = 'modal-confirm-delete'
                self.locator_finder_by_id(confirm_btn).click()
                self.tprint(f'Deleting {username} completed \n')
                time.sleep(2)
        except TimeoutException:
            self.tprint('TimeoutException occurred! \n')
            self.tprint('Info: User has already been deleted or never created. \n')
        except Exception:
            raise Exception('Critical Error occurred and need manual inspection!! \n')
