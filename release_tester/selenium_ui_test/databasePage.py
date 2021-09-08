import time

from selenium.common.exceptions import TimeoutException

from baseSelenium import BaseSelenium


class DatabasePage(BaseSelenium):

    def __init__(self, driver):
        super().__init__()
        self.driver = driver
        self.database_page = 'databases'
        self.create_new_db_btn_sitem = 'createDatabase'
        self.sort_db_sitem = '//*[@id="databaseDropdown"]/ul/li[2]/a/label/i'
        self.select_db_opt_id_sitem = "loginDatabase"

    def select_database_page(self):
        """Navigate to Database page"""
        db_sitem = self.database_page
        db_sitem = BaseSelenium.locator_finder_by_id(self, db_sitem)
        db_sitem.click()
        time.sleep(1)

    def create_new_db(self, db_name, index):
        """Creating new database"""
        print(f'Creating {db_name} database started \n')
        create_new_db_btn_sitem = self.create_new_db_btn_sitem
        create_new_db_btn_sitem = BaseSelenium.locator_finder_by_id(self, create_new_db_btn_sitem)
        create_new_db_btn_sitem.click()
        time.sleep(1)

        # fill up all the database details
        new_db_name = 'newDatabaseName'
        new_db_name = BaseSelenium.locator_finder_by_id(self, new_db_name)
        new_db_name.click()
        new_db_name.send_keys(db_name)
        time.sleep(1)

        replication_factor_sitem = 'new-replication-factor'
        replication_factor_sitem = BaseSelenium.locator_finder_by_id(self, replication_factor_sitem)
        replication_factor_sitem.click()
        replication_factor_sitem.clear()
        replication_factor_sitem.send_keys('3')
        time.sleep(1)

        write_concern_sitem = 'new-write-concern'
        write_concern_sitem = BaseSelenium.locator_finder_by_id(self, write_concern_sitem)
        write_concern_sitem.click()
        write_concern_sitem.clear()
        write_concern_sitem.send_keys('3')
        time.sleep(1)

        # selecting sharded option from drop down using index
        select_sharded_db_sitem = 'newSharding'
        BaseSelenium.locator_finder_by_select(self, select_sharded_db_sitem, index)
        time.sleep(1)

        # selecting user option from drop down using index for choosing root user.
        select_user_sitem = 'newUser'
        BaseSelenium.locator_finder_by_select(self, select_user_sitem, 0)   # 0 for root user
        time.sleep(1)

        # clicking create button
        create_db_sitem = 'modalButton1'
        create_db_sitem = BaseSelenium.locator_finder_by_id(self, create_db_sitem)
        create_db_sitem.click()
        time.sleep(4)

        print(f'Creating {db_name} database completed \n')

        print(f'Logging into newly created {db_name} database \n')
        change_sitem = '//*[@id="dbStatus"]/a[3]/i'
        change_db_sitem = BaseSelenium.locator_finder_by_xpath(self, change_sitem)
        change_db_sitem.click()
        time.sleep(5)

        db_opt = self.select_db_opt_id_sitem
        print('Database checked and found: ', db_name, '\n')
        time.sleep(4)

        if db_name == 'Sharded':
            # selecting newly created db for login from the dropdown menu
            BaseSelenium.locator_finder_by_select(self, db_opt, 1)
        if db_name == 'OneShard':
            # OneShard took place over Sharded database thus used index value 1
            BaseSelenium.locator_finder_by_select(self, db_opt, 1)

        select_db_btn_id = "goToDatabase"
        select_db_btn_id = BaseSelenium.locator_finder_by_id(self, select_db_btn_id)
        select_db_btn_id.click()
        time.sleep(2)

        db_name_sitem = '//*[@id="dbStatus"]/a[2]/span'
        db_name_sitem = BaseSelenium.locator_finder_by_xpath(self, db_name_sitem).text

        if index == 0:
            assert db_name_sitem == 'SHARDED', f"Expected SHARDED but got {db_name_sitem}"
        if index == 1:
            assert db_name_sitem == 'ONESHARD', f"Expected ONESHARD but got {db_name_sitem}"

        print(f'Logging out from {db_name} database \n')
        db_sitem = '//*[@id="dbStatus"]/a[3]/i'
        change_db_sitem = BaseSelenium.locator_finder_by_xpath(self, db_sitem)
        change_db_sitem.click()
        time.sleep(4)

        print('Re-Login to _system database \n')
        db_option = self.select_db_opt_id_sitem
        BaseSelenium.locator_finder_by_select(self, db_option, 0)
        select_db_btn_id_sitem = "goToDatabase"
        select_db_btn_id_sitem = BaseSelenium.locator_finder_by_id(self, select_db_btn_id_sitem)
        select_db_btn_id_sitem.click()
        time.sleep(3)

        self.select_database_page()

    def sorting_db(self):
        """Sorting database"""
        db_settings_sitem = 'databaseToggle'
        db_settings_sitem = BaseSelenium.locator_finder_by_id(self, db_settings_sitem)
        db_settings_sitem.click()
        time.sleep(1)

        ascending = self.sort_db_sitem
        ascending = BaseSelenium.locator_finder_by_xpath(self, ascending)
        ascending.click()
        time.sleep(2)

        descending = self.sort_db_sitem
        descending = BaseSelenium.locator_finder_by_xpath(self, descending)
        descending.click()
        time.sleep(2)

    def searching_db(self, db_name):
        """Searching database"""
        db_search_sitem = 'databaseSearchInput'
        db_search_sitem = BaseSelenium.locator_finder_by_id(self, db_search_sitem)
        db_search_sitem.click()
        db_search_sitem.clear()
        db_search_sitem.send_keys(db_name)
        time.sleep(2)

        try:
            collection_name_sitem = '//*[@id="userManagementView"]/div/div[2]/div/h5'
            collection_name_sitem = BaseSelenium.locator_finder_by_xpath(self, collection_name_sitem).text

            if db_name == 'Sharded':
                assert 'Sharded' == collection_name_sitem, f"Expected {db_name} but got {collection_name_sitem}"
            elif db_name == 'OneShard':
                assert 'OneShard' == collection_name_sitem, f"Expected {db_name} but got {collection_name_sitem}"

        except TimeoutException():
            print('Error Occurred! \n')

        print('Clearing the search text area \n')
        clear_search_sitem = 'databaseSearchInput'
        clear_search_sitem = BaseSelenium.locator_finder_by_id(self, clear_search_sitem)
        clear_search_sitem.click()
        clear_search_sitem.clear()
        time.sleep(2)

    def Deleting_database(self, db_name):
        """Deleting Database"""
        self.driver.refresh()

        print(f'{db_name} deleting started \n')

        if db_name == 'OneShard':
            db_search_sitem = 'OneShard_edit-database'
            db_sitem = BaseSelenium.locator_finder_by_id(self, db_search_sitem)
            db_sitem.click()

        if db_name == 'Sharded':
            db_search_sitem = 'Sharded_edit-database'
            db_sitem = BaseSelenium.locator_finder_by_id(self, db_search_sitem)
            db_sitem.click()

        delete_btn_sitem = 'modalButton1'
        delete_btn_sitem = BaseSelenium.locator_finder_by_id(self, delete_btn_sitem)
        delete_btn_sitem.click()
        time.sleep(1)

        delete_confirm_btn_sitem = 'modal-confirm-delete'
        delete_confirm_btn_sitem = BaseSelenium.locator_finder_by_id(self, delete_confirm_btn_sitem)
        delete_confirm_btn_sitem.click()
        time.sleep(1)

        self.driver.refresh()

        print(f'{db_name} deleting completed \n')
