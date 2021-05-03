from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.action_chains import ActionChains
import time
import pyautogui


class BaseSelenium:
    driver: WebDriver

    def __init__(self):
        self.locator = None
        self.select = None

    @classmethod
    def set_up_class(cls):
        cls.driverLocation = "C:/Program Files (x86)/chromedriver.exe"
        cls.driver = webdriver.Chrome(cls.driverLocation)
        cls.driver.set_window_size(1250, 1000)  # custom window size
        cls.driver.get("http://127.0.0.1:8529/_db/_system/_admin/aardvark/index.html#login")

    @classmethod
    def tear_down(cls):
        time.sleep(5)
        cls.driver.close()
        print("\n--------Now Quiting--------\n")
        cls.driver.quit()

    '''This method will change tab and close it then return to home tab'''

    def switch_tab(self, locator):
        self.locator = locator
        self.locator.send_keys(Keys.CONTROL + Keys.RETURN)  # this will open new tab on top of current
        self.driver.switch_to.window(self.driver.window_handles[1])  # switch to new tab according to index value
        time.sleep(10)
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])

    '''This method will be used to scroll up and down to any page'''

    def scroll(self, down=0):
        self.driver.find_element_by_tag_name('html').send_keys(Keys.END)

        if down == 1:
            print("")
        else:
            time.sleep(5)
            self.driver.find_element_by_tag_name('html').send_keys(Keys.HOME)
        # self.driver.execute_script("window.scrollTo(0,500)")

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
            print("S:", locator_name, " locator has not found.")
        else:
            return self.locator

    '''This method will used for finding all the locators in drop down menu with options'''

    def locator_finder_by_select(self, locator_name, value):
        self.select = Select(self.driver.find_element_by_id(locator_name))
        self.select.select_by_index(value)
        if self.select is None:
            print("S:", locator_name, " locator has not found.")
        return self.select

    '''This method will used for finding all the locators and hover the mouse by id'''

    def locator_finder_by_hover_item_id(self, locator):
        item = self.driver.find_element_by_id(locator)
        action = ActionChains(self.driver)
        action.move_to_element(item).click().perform()
        time.sleep(1)
        return action

    '''This method will used for escape from a maximized window'''

    @staticmethod
    def escape():
        pyautogui.press("f11")

    '''This method will used for zoom in/out on any perspective window'''

    def zoom(self):
        print("zooming in now\n")
        self.driver.execute_script("document.body.style.zoom='80%'")

    '''This method will used for finding all the locators and hover the mouse by xpath'''

    def locator_finder_by_hover_item(self, locator):
        item = self.driver.find_element_by_xpath(locator)
        action = ActionChains(self.driver)
        action.move_to_element(item).click().perform()
        time.sleep(1)
        return action

    '''This method will used for finding all the locators text using ID'''

    def locator_finder_by_text_id(self, locator_name):
        self.locator = WebDriverWait(self.driver, 10).until(
            ec.element_to_be_clickable((By.ID, locator_name))
        )
        self.locator = self.locator.text
        if self.locator is None:
            print("S:", locator_name, " locator has not found.")
        else:
            return self.locator

    '''This method will used for finding all the locators text using xpath'''

    def locator_finder_by_text_xpath(self, locator_name):
        self.locator = WebDriverWait(self.driver, 10).until(
            ec.element_to_be_clickable((By.XPATH, locator_name))
        )
        self.locator = self.locator.text
        if self.locator is None:
            print("S:", locator_name, " locator has not found.")
        else:
            return self.locator

    '''This method will used for finding all the locators text using CSS Selector'''

    def locator_finder_by_css_selectors(self, locator_name):
        self.locator = WebDriverWait(self.driver, 10).until(
            ec.element_to_be_clickable((By.CSS_SELECTOR, locator_name))
        )
        self.locator = self.locator.text
        if self.locator is None:
            print("S:", locator_name, " locator has not found.")
        else:
            return self.locator
