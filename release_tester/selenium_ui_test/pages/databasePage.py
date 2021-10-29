import time
from selenium.common.exceptions import TimeoutException
from selenium_ui_test.pages.navbar import NavigationBarPage


class DatabasePage(NavigationBarPage):
    def __init__(self, webdriver):
        super().__init__(webdriver)
        self.database_page = "databases"
        self.create_new_db_btn = "createDatabase"
        self.sort_db = '//*[@id="databaseDropdown"]/ul/li[2]/a/label/i'
        self.select_db_opt_id_sitem = "loginDatabase"

    def select_database_page(self):
        """Navigate to Database page"""
        db_sitem = self.database_page
        db_sitem = self.locator_finder_by_id(db_sitem)
        db_sitem.click()
        time.sleep(1)

    def create_new_db(self, db_name, index, cluster):
        """Creating and checking new database"""
        self.select_database_page()
        print(f'Creating {db_name} database started \n')
        create_new_db_btn = self.create_new_db_btn
        create_new_db_btn_sitem = self.locator_finder_by_id(create_new_db_btn)
        create_new_db_btn_sitem.click()
        time.sleep(2)

        # fill up all the database details
        new_db_name = 'newDatabaseName'
        new_db_name_sitem = self.locator_finder_by_id(new_db_name)
        new_db_name_sitem.click()
        new_db_name_sitem.send_keys(db_name)
        time.sleep(1)

        if cluster:
            replication_factor = 'new-replication-factor'
            replication_factor_sitem = self.locator_finder_by_id(replication_factor)
            replication_factor_sitem.click()
            replication_factor_sitem.clear()
            replication_factor_sitem.send_keys('3')
            time.sleep(1)

            write_concern = 'new-write-concern'
            write_concern_sitem = self.locator_finder_by_id(write_concern)
            write_concern_sitem.click()
            write_concern_sitem.clear()
            write_concern_sitem.send_keys('3')
            time.sleep(1)

            if super().check_server_package() == 'COMMUNITY EDITION':
                pass
            elif super().check_server_package() == 'ENTERPRISE EDITION':
                # selecting sharded option from drop down using index
                select_sharded_db = 'newSharding'
                self.locator_finder_by_select(select_sharded_db, index)
                time.sleep(1)
            else:
                print('Can not determined the ')

        # selecting user option from drop down using index for choosing root user.
        select_user = 'newUser'
        self.locator_finder_by_select(select_user, 0)  # 0 for root user
        time.sleep(1)

        # clicking create button
        create_db = 'modalButton1'
        create_db_sitem = self.locator_finder_by_id(create_db)
        create_db_sitem.click()
        time.sleep(4)

        print(f'Creating {db_name} database completed \n')

        print(f'Logging into newly created {db_name} database \n')
        change_db = '//*[@id="dbStatus"]/a[3]/i'
        change_db_sitem = self.locator_finder_by_xpath(change_db)
        change_db_sitem.click()
        time.sleep(5)

        db_opt = self.select_db_opt_id_sitem
        print('Database checked and found: ', db_name, '\n')
        time.sleep(4)

        if db_name == 'Sharded':
            # selecting newly created db for login from the dropdown menu
            self.locator_finder_by_select(db_opt, 1)
        if db_name == 'OneShard':
            # OneShard took place over Sharded database thus used index value 1
            self.locator_finder_by_select(db_opt, 1)

        select_db_btn_id = "goToDatabase"
        select_db_btn_id_sitem = self.locator_finder_by_id(select_db_btn_id)
        select_db_btn_id_sitem.click()
        time.sleep(2)

        db_name = '//*[@id="dbStatus"]/a[2]/span'
        db_name_sitem = self.locator_finder_by_xpath(db_name).text

        if index == 0:
            assert db_name_sitem == 'SHARDED', f"Expected SHARDED but got {db_name_sitem}"
        if index == 1:
            assert db_name_sitem == 'ONESHARD', f"Expected ONESHARD but got {db_name_sitem}"

        print(f'Logging out from {db_name_sitem} database \n')
        db = '//*[@id="dbStatus"]/a[3]/i'
        change_db_sitem = self.locator_finder_by_xpath(db)
        change_db_sitem.click()
        time.sleep(4)

        print('Re-Login to _system database \n')
        db_option = self.select_db_opt_id_sitem
        self.locator_finder_by_select(db_option, 0)
        select_db_btn_id = "goToDatabase"
        select_db_btn_id_sitem = self.locator_finder_by_id(select_db_btn_id)
        select_db_btn_id_sitem.click()
        time.sleep(3)

    def test_database_expected_error(self, cluster):
        """This method will test all negative scenario"""
        self.select_database_page()
        print('Expected error scenario for the Database name Started. \n')
        create_new_db_btn = self.create_new_db_btn
        create_new_db_btn_sitem = self.locator_finder_by_id(create_new_db_btn)
        create_new_db_btn_sitem.click()
        time.sleep(2)

        # ---------------------------------------database name convention test---------------------------------------
        print('Expected error scenario for the Database name Started \n')
        version = super().current_package_version()
        if version == 3.9:
            db_name_error_input = ['@', '1', 'שלום']  # name must be 64 bit thus 65 character won't work too.
            db_name_print_statement = ['Checking Db name with symbol " @ "',
                                       'Checking numeric value for DB name " 1 "',
                                       'Checking Non-ASCII Hebrew Characters "שלום"']
            db_name_error_message = ['DB: Invalid Parameters: database name invalid',
                                     'DB: Invalid Parameters: database name invalid',
                                     'DB: Invalid Parameters: database name invalid']
            db_name = 'newDatabaseName'
            db_name_error = '/html/body/div[10]/div/div[1]'
        else:
            db_name_error_input = ['', '@', '1', 'שלום']  # name must be 64 bit thus 65 character won't work too.
            db_name_print_statement = ['Checking blank DB name with " "',
                                       'Checking Db name with symbol " @ "',
                                       'Checking numeric value for DB name " 1 "',
                                       'Checking Non-ASCII Hebrew Characters "שלום"']
            db_name_error_message = ['No database name given.',
                                     'Only Symbols "_" and "-" are allowed.',
                                     'Database name must start with a letter.',
                                     'Only Symbols "_" and "-" are allowed.']
            db_name = 'newDatabaseName'
            db_name_error = '//*[@id="row_newDatabaseName"]/th[2]/p'

        # method template (self, error_input, print_statement, error_message, locators_id, error_message_id)
        self.check_expected_error_messages_for_database(db_name_error_input,
                                                        db_name_print_statement,
                                                        db_name_error_message,
                                                        db_name,
                                                        db_name_error)
        print('Expected error scenario for the Database name Completed \n')

        if cluster and version == 3.9:
            db = self.locator_finder_by_id('newDatabaseName')
            db.click()
            db.clear()
            db.send_keys('db')
            time.sleep(2)
            # ----------------------------database Replication Factor convention test-----------------------------
            print('Expected error scenario for the Database Replication Factor Started \n')
            rf_error_input = ['@', 'a', '11', 'שלום']
            rf_print_statement = ['Checking RF with "@"', 'Checking RF with "a"',
                                  'Checking RF with "11"', 'Checking RF with "שלום"']
            rf_error_message = ['Must be a number between 1 and 10.',
                                'Must be a number between 1 and 10.',
                                'Must be a number between 1 and 10.',
                                'Must be a number between 1 and 10.']
            rf_name = 'new-replication-factor'
            db_name_error_id = '//*[@id="row_new-replication-factor"]/th[2]/p'

            # method template (self, error_input, print_statement, error_message, locators_id, error_message_id)
            self.check_expected_error_messages_for_database(rf_error_input,
                                                            rf_print_statement,
                                                            rf_error_message,
                                                            rf_name,
                                                            db_name_error_id,
                                                            True)  # True defines cluster deployment
            print('Expected error scenario for the Database Replication Factor Completed \n')

            # -------------------------------database Write Concern convention test----------------------------------
            print('Expected error scenario for the Database Write Concern Started \n')
            wc_error_input = ['@', 'a', '11', 'שלום']
            wc_print_statement = ['Checking Write Concern with "@"',
                                  'Checking Write Concern with "a"',
                                  'Checking Write Concern with "11"',
                                  'Checking Write Concern with "שלום"']
            wc_error_message = ['Must be a number between 1 and 10. Has to be smaller or equal compared to the '
                                'replicationFactor.',
                                'Must be a number between 1 and 10. Has to be smaller or equal compared to the '
                                'replicationFactor.',
                                'Must be a number between 1 and 10. Has to be smaller or equal compared to the '
                                'replicationFactor.',
                                'Must be a number between 1 and 10. Has to be smaller or equal compared to the '
                                'replicationFactor.']
            wc_name = 'new-write-concern'
            wc_name_error_id = '//*[@id="row_new-write-concern"]/th[2]/p'

            # method template (self, error_input, print_statement, error_message, locators_id, error_message_id)
            self.check_expected_error_messages_for_database(wc_error_input,
                                                            wc_print_statement,
                                                            wc_error_message,
                                                            wc_name,
                                                            wc_name_error_id,
                                                            True)
            print('Expected error scenario for the Database Write Concern Completed \n')

        if cluster and version == 3.8:
            # -------------------------------database Replication Factor convention test------------------------------
            print('Expected error scenario for the Database Replication Factor Started \n')
            rf_error_input = ['@', 'a', '11', 'שלום']
            rf_print_statement = ['Checking RF with "@"',
                                  'Checking RF with "a"',
                                  'Checking RF with "11"',
                                  'Checking RF with "שלום"']
            rf_error_message = ['Must be a number between 1 and 10.',
                                'Must be a number between 1 and 10.',
                                'Must be a number between 1 and 10.',
                                'Must be a number between 1 and 10.']
            rf_name = 'new-replication-factor'
            db_name_error = '//*[@id="row_new-replication-factor"]/th[2]/p'

            # method template (self, error_input, print_statement, error_message, locators_id, error_message_id)
            self.check_expected_error_messages_for_database(rf_error_input,
                                                            rf_print_statement,
                                                            rf_error_message,
                                                            rf_name,
                                                            db_name_error)
            print('Expected error scenario for the Database Replication Factor Completed \n')

            # -------------------------------database Write Concern convention test----------------------------------
            print('Expected error scenario for the Database Write Concern Started \n')
            wc_error_input = ['@', 'a', '11', 'שלום']
            wc_print_statement = ['Checking Write Concern with "@"', 'Checking Write Concern with "a"',
                                  'Checking Write Concern with "11"', 'Checking Write Concern with "שלום"']
            wc_error_message = ['Must be a number between 1 and 10. Has to be smaller or equal compared to the '
                                'replicationFactor.',
                                'Must be a number between 1 and 10. Has to be smaller or equal compared to the '
                                'replicationFactor.',
                                'Must be a number between 1 and 10. Has to be smaller or equal compared to the '
                                'replicationFactor.',
                                'Must be a number between 1 and 10. Has to be smaller or equal compared to the '
                                'replicationFactor.']
            wc_name = 'new-write-concern'
            wc_name_error = '//*[@id="row_new-write-concern"]/th[2]/p'

            # method template (self, error_input, print_statement, error_message, locators_id, error_message_id)
            self.check_expected_error_messages_for_database(wc_error_input,
                                                            wc_print_statement,
                                                            wc_error_message,
                                                            wc_name,
                                                            wc_name_error)
            print('Expected error scenario for the Database Write Concern Completed \n')

        print('Closing the database creation \n')
        close_btn = 'modalButton0'
        close_btn_sitem = self.locator_finder_by_id(close_btn)
        close_btn_sitem.click()
        time.sleep(3)

    def sorting_db(self):
        """Sorting database"""
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
            print("Error Occurred! \n")

        print("Clearing the search text area \n")
        clear_search = "databaseSearchInput"
        clear_search_sitem = self.locator_finder_by_id(clear_search)
        clear_search_sitem.click()
        clear_search_sitem.clear()
        time.sleep(2)

    def deleting_database(self, db_name):
        """Deleting Database"""
        self.webdriver.refresh()
        try:
            print(f"{db_name} deleting started \n")

            if db_name == "OneShard":
                db_search = "OneShard_edit-database"
                db_sitem = self.locator_finder_by_id(db_search)
                db_sitem.click()

            if db_name == "Sharded":
                db_search = "Sharded_edit-database"
                db_sitem = self.locator_finder_by_id(db_search)
                db_sitem.click()

            delete_btn = "modalButton1"
            delete_btn_sitem = self.locator_finder_by_id(delete_btn)
            delete_btn_sitem.click()
            time.sleep(1)

            delete_confirm_btn = "modal-confirm-delete"
            delete_confirm_btn_sitem = self.locator_finder_by_id(delete_confirm_btn)
            delete_confirm_btn_sitem.click()
            time.sleep(1)

            self.webdriver.refresh()

            print(f"{db_name} deleting completed \n")
        except TimeoutException as ex:
            print("FAIL: Error occurred during DB deletion \n")

    def deleting_user(self, username):
        """Deleting users created for the Database test"""
        self.webdriver.refresh()
        try:
            print('Selecting user for deletion \n')
            tester = "//h5[text()='tester (tester)']"
            tester01 = "//h5[text()='tester01 (tester01)']"
            if username == 'tester':
                self.locator_finder_by_xpath(tester).click()
            elif username == 'tester01':
                self.locator_finder_by_xpath(tester01).click()
            else:
                raise Exception('Wrong user has been chosen for deletion!!! \n')
            time.sleep(2)

            print(f'Deleting {username} begins \n')
            del_button = 'modalButton0'
            self.locator_finder_by_id(del_button).click()

            # confirming delete user
            confirm_btn = 'modal-confirm-delete'
            self.locator_finder_by_id(confirm_btn).click()
            print(f'Deleting {username} completed \n')
            time.sleep(2)
        except TimeoutException:
            print("FAIL: Error occurred during USER deletion \n")