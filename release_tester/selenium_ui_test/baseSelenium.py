import os
import time

import pyautogui
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait

from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from webdriver_manager.utils import ChromeType


class BaseSelenium:
    driver: WebDriver

    def __init__(self):
        self.locator = None
        self.select = None

    @classmethod
    def set_up_class(cls):

        browser_list = ['1 = chrome', '2 = firefox', '3 = edge', '4 = chromium']
        print(*browser_list, sep="\n")
        cls.browser_name = None

        while cls.browser_name not in {1, 2, 3, 4}:
            cls.browser_name = int(input('Choose your browser: '))

            if cls.browser_name == 1:
                print("You have chosen: Chrome browser \n")
                cls.driver = webdriver.Chrome(ChromeDriverManager().install())
            elif cls.browser_name == 2:
                print("You have chosen: Firefox browser \n")

                # This preference will disappear download bar for firefox
                profile = webdriver.FirefoxProfile()
                profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/json, text/csv")  # mime
                profile.set_preference("browser.download.manager.showWhenStarting", False)
                profile.set_preference("browser.download.dir", "C:\\Users\\rearf\\Downloads")
                profile.set_preference("browser.download.folderList", 2)
                profile.set_preference("pdfjs.disabled", True)

                cls.driver = webdriver.Firefox(executable_path=GeckoDriverManager().install(), firefox_profile=profile)

            elif cls.browser_name == 3:
                print("You have chosen: Edge browser \n")
                cls.driver = webdriver.Edge(EdgeChromiumDriverManager().install())
            elif cls.browser_name == 4:
                print("You have chosen: Chromium browser \n")
                cls.driver = webdriver.Chrome(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
            else:
                print("Kindly provide a specific browser name from the list. \n")

        cls.driver.set_window_size(1250, 1000)  # custom window size
        cls.driver.get("http://127.0.0.1:8529/_db/_system/_admin/aardvark/index.html#login")

    @classmethod
    def tear_down(cls):
        time.sleep(5)
        cls.driver.close()
        print("\n--------Now Quiting--------\n")
        cls.driver.quit()

    '''This method will be used for executing console command'''

    @staticmethod
    def command(cmd):
        os.system(cmd)

    @staticmethod
    def query(query):
        pyautogui.typewrite(query)

    '''This method will switch to IFrame window'''

    def switch_to_iframe(self, iframe_id):
        self.driver.switch_to.frame(self.driver.find_element_by_xpath(iframe_id))
        time.sleep(1)

    '''This method will switch back to origin window'''

    def switch_back_to_origin_window(self):
        self.driver.switch_to.default_content()
        time.sleep(1)

    '''This method will select all text and clean it'''

    @staticmethod
    def clear_all_text():
        pyautogui.keyDown('ctrl')
        pyautogui.press('a')
        pyautogui.keyUp('ctrl')
        pyautogui.press('del')

    '''This method will close the download bar from the chrome browser'''

    @staticmethod
    def clear_download_bar():
        print("closing download banner from the bottom \n")
        pyautogui.hotkey('ctrl', 'j')
        pyautogui.hotkey('ctrl', 'w')

    '''This method will be used for clear all the text in single text field if .clear() does not work'''

    def clear_text_field(self, locator):
        locator.send_keys(Keys.CONTROL + 'a', Keys.BACKSPACE)

        if self.locator is None:
            print("UI-Test: ", locator, " locator has not found.")
        else:
            return self.locator

    '''This method will change tab and close it and finally return to origin tab'''

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
            time.sleep(3)
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
            print("UI-Test: ", locator_name, " locator has not found.")
        else:
            return self.locator

    '''This method will used for finding all the locators in drop down menu with options'''

    def locator_finder_by_select(self, locator_name, value):
        self.select = Select(self.driver.find_element_by_id(locator_name))
        self.select.select_by_index(value)
        if self.select is None:
            print("UI-Test: ", locator_name, " locator has not found.")
        return self.select

    '''This method will used for finding all the locators and hover the mouse by id'''

    def locator_finder_by_hover_item_id(self, locator):
        item = self.driver.find_element_by_id(locator)
        action = ActionChains(self.driver)
        action.move_to_element(item).click().perform()
        time.sleep(1)
        return action

    '''This method will used for escape from a maximized to minimize window'''

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
            print("UI-Test: ", locator_name, " locator has not found.")
        else:
            return self.locator

    '''This method will used for finding all the locators text using xpath'''

    def locator_finder_by_text_xpath(self, locator_name):
        self.locator = WebDriverWait(self.driver, 10).until(
            ec.element_to_be_clickable((By.XPATH, locator_name))
        )
        self.locator = self.locator.text
        if self.locator is None:
            print("UI-Test: ", locator_name, " locator has not found.")
        else:
            return self.locator

    '''This method will used for finding all the locators text using CSS Selector'''

    def locator_finder_by_css_selectors(self, locator_name):
        self.locator = WebDriverWait(self.driver, 10).until(
            ec.element_to_be_clickable((By.CSS_SELECTOR, locator_name))
        )
        self.locator = self.locator.text
        if self.locator is None:
            print("UI-Test: ", locator_name, " locator has not found.")
        else:
            return self.locator
