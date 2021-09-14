import time

from selenium.common.exceptions import TimeoutException

from selenium_ui_test.base_selenium import BaseSelenium, Keys


class DatabasePage(BaseSelenium):

    def __init__(self, driver):
        super().__init__()
        self.driver = driver
        self.database_page = 'databases'
        self.create_new_db_btn = 'createDatabase'
        self.sort_db_sitem = '//*[@id="databaseDropdown"]/ul/li[2]/a/label/i'
        self.select_db_opt_id_sitem = "loginDatabase"

    def select_database_page(self):
        """Navigate to Database page"""
        db_sitem = self.database_page
        db_sitem = self.locator_finder_by_id(self, db_sitem)
        db_sitem.click()
        time.sleep(1)

    def create_new_db(self, db_name, index):
        """Creating new database"""
        print(f'Creating {db_name} database started \n')
        create_new_db_btn = self.create_new_db_btn
        create_new_db_btn_sitem = self.locator_finder_by_id(self, create_new_db_btn)
        create_new_db_btn_sitem.click()
        time.sleep(2)

        # fill up all the database details
        new_db_name = 'newDatabaseName'
        new_db_name_sitem = self.locator_finder_by_id(self, new_db_name)
        new_db_name_sitem.click()
        new_db_name_sitem.send_keys(db_name)
        time.sleep(1)

        replication_factor = 'new-replication-factor'
        replication_factor_sitem = self.locator_finder_by_id(self, replication_factor)
        replication_factor_sitem.click()
        replication_factor_sitem.clear()
        replication_factor_sitem.send_keys('3')
        time.sleep(1)

        write_concern = 'new-write-concern'
        write_concern_sitem = self.locator_finder_by_id(self, write_concern)
        write_concern_sitem.click()
        write_concern_sitem.clear()
        write_concern_sitem.send_keys('3')
        time.sleep(1)

        # selecting sharded option from drop down using index
        select_sharded_db = 'newSharding'
        self.locator_finder_by_select(self, select_sharded_db, index)
        time.sleep(1)

        # selecting user option from drop down using index for choosing root user.
        select_user = 'newUser'
        self.locator_finder_by_select(self, select_user, 0)   # 0 for root user
        time.sleep(1)

        # clicking create button
        create_db = 'modalButton1'
        create_db_sitem = self.locator_finder_by_id(self, create_db)
        create_db_sitem.click()
        time.sleep(4)

        print(f'Creating {db_name} database completed \n')

        print(f'Logging into newly created {db_name} database \n')
        change = '//*[@id="dbStatus"]/a[3]/i'
        change_db_sitem = self.locator_finder_by_xpath(self, change)
        change_db_sitem.click()
        time.sleep(5)

        db_opt = self.select_db_opt_id_sitem
        print('Database checked and found: ', db_name, '\n')
        time.sleep(4)

        if db_name == 'Sharded':
            # selecting newly created db for login from the dropdown menu
            self.locator_finder_by_select(self, db_opt, 1)
        if db_name == 'OneShard':
            # OneShard took place over Sharded database thus used index value 1
            self.locator_finder_by_select(self, db_opt, 1)

        select_db_btn_id = "goToDatabase"
        select_db_btn_id_sitem = self.locator_finder_by_id(self, select_db_btn_id)
        select_db_btn_id_sitem.click()
        time.sleep(2)

        db_name = '//*[@id="dbStatus"]/a[2]/span'
        db_name_sitem = self.locator_finder_by_xpath(self, db_name).text

        if index == 0:
            assert db_name_sitem == 'SHARDED', f"Expected SHARDED but got {db_name_sitem}"
        if index == 1:
            assert db_name_sitem == 'ONESHARD', f"Expected ONESHARD but got {db_name_sitem}"

        print(f'Logging out from {db_name} database \n')
        db = '//*[@id="dbStatus"]/a[3]/i'
        change_db_sitem = self.locator_finder_by_xpath(self, db)
        change_db_sitem.click()
        time.sleep(4)

        print('Re-Login to _system database \n')
        db_option = self.select_db_opt_id_sitem
        self.locator_finder_by_select(self, db_option, 0)
        select_db_btn_id = "goToDatabase"
        select_db_btn_id_sitem = self.locator_finder_by_id(self, select_db_btn_id)
        select_db_btn_id_sitem.click()
        time.sleep(3)

        self.select_database_page()
    
    def test_database_name(self):
        """This method will test all negative scenario"""
        print('Expected error scenario for the Database name Started. \n')
        create_new_db_btn = self.create_new_db_btn
        create_new_db_btn_sitem = self.locator_finder_by_id(self, create_new_db_btn)
        create_new_db_btn_sitem.click()
        time.sleep(2)

        # proper database name convention test
        # 1. keep db name blank

        print_statement = ['Checking blank DB name with " "', 'Checking Db name with symbol " @ "',
                           'Checking numeric value for DB name " 1 "']
        name_error = ['', '@', '1']     # name must be 64 bit thus 65 character won't work too.
        error_message = ['No database name given.', 'Only Symbols "_" and "-" are allowed.',
                         'Database name must start with a letter.']
        i = 0
        # looping through all the error scenario for db name
        while i < len(name_error):
            print(print_statement[i])
            new_db_name = 'newDatabaseName'
            new_db_name_sitem = self.locator_finder_by_id(self, new_db_name)
            new_db_name_sitem.click()
            new_db_name_sitem.clear()
            new_db_name_sitem.send_keys(name_error[i])
            time.sleep(1)
            new_db_name_sitem.send_keys(Keys.TAB)
            time.sleep(1)

            try:
                error = 'errorMessage'
                error_sitem = self.locator_finder_by_class(self, error).text
                print('Expected error found: ', error_sitem, '\n')
                time.sleep(2)

                assert error_sitem == error_message[i], \
                    f"Expected error message {error_message[i]} but got {error_sitem}"

            except TimeoutException:
                raise Exception('*****-->Error occurred. Manual inspection required<--***** \n')

            i = i + 1
        print('Expected error scenario for the Database name Completed \n')


    def sorting_db(self):
        """Sorting database"""
        db_settings = 'databaseToggle'
        db_settings_sitem = self.locator_finder_by_id(self, db_settings)
        db_settings_sitem.click()
        time.sleep(1)

        ascending = self.sort_db_sitem
        ascending_sitem = self.locator_finder_by_xpath(self, ascending)
        ascending_sitem.click()
        time.sleep(2)

        descending = self.sort_db_sitem
        descending_sitem = self.locator_finder_by_xpath(self, descending)
        descending_sitem.click()
        time.sleep(2)

    def searching_db(self, db_name):
        """Searching database"""
        db_search = 'databaseSearchInput'
        db_search_sitem = self.locator_finder_by_id(self, db_search)
        db_search_sitem.click()
        db_search_sitem.clear()
        db_search_sitem.send_keys(db_name)
        time.sleep(2)

        try:
            collection_name = '//*[@id="userManagementView"]/div/div[2]/div/h5'
            collection_name_sitem = self.locator_finder_by_xpath(self, collection_name).text

            if db_name == 'Sharded':
                assert 'Sharded' == collection_name_sitem, f"Expected {db_name} but got {collection_name_sitem}"
            elif db_name == 'OneShard':
                assert 'OneShard' == collection_name_sitem, f"Expected {db_name} but got {collection_name_sitem}"

        except TimeoutException():
            print('Error Occurred! \n')

        print('Clearing the search text area \n')
        clear_search = 'databaseSearchInput'
        clear_search_sitem = self.locator_finder_by_id(self, clear_search)
        clear_search_sitem.click()
        clear_search_sitem.clear()
        time.sleep(2)

    def Deleting_database(self, db_name):
        """Deleting Database"""
        self.driver.refresh()

        print(f'{db_name} deleting started \n')

        if db_name == 'OneShard':
            db_search = 'OneShard_edit-database'
            db_sitem = self.locator_finder_by_id(self, db_search)
            db_sitem.click()

        if db_name == 'Sharded':
            db_search = 'Sharded_edit-database'
            db_sitem = self.locator_finder_by_id(self, db_search)
            db_sitem.click()

        delete_btn = 'modalButton1'
        delete_btn_sitem = self.locator_finder_by_id(self, delete_btn)
        delete_btn_sitem.click()
        time.sleep(1)

        delete_confirm_btn = 'modal-confirm-delete'
        delete_confirm_btn_sitem = self.locator_finder_by_id(self, delete_confirm_btn)
        delete_confirm_btn_sitem.click()
        time.sleep(1)

        self.driver.refresh()

        print(f'{db_name} deleting completed \n')
