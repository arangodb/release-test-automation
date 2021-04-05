from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait


class BaseSelenium:
    locator: object

    @classmethod
    def set_up_class(cls):
        cls.driverLocation = "C:/Program Files (x86)/chromedriver.exe"
        cls.driver = webdriver.Chrome(cls.driverLocation)
        cls.driver.get("http://127.0.0.1:8529/_db/_system/_admin/aardvark/index.html#login")

    '''This method will used for finding all the locators by their id'''

    def locator_finder_by_id(self, locator_name):
        self.locator = WebDriverWait(self.driver, 10).until(
            ec.element_to_be_clickable((By.ID, locator_name))
        )
        if self.locator is None:
            print(locator_name, " locator has not found.")
        else:
            return self.locator

    '''This method will used for finding all the locators by their xpath'''

    def locator_finder_by_xpath(self, locator_name):
        self.locator = WebDriverWait(self.driver, 10).until(
            ec.element_to_be_clickable((By.XPATH, locator_name))
        )
        if self.locator is None:
            print(locator_name, " locator has not found.")
        else:
            return self.locator
