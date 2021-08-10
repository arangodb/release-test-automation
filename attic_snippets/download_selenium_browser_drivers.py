import time
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from webdriver_manager.utils import ChromeType

"""
pip install selenium
pip install webdriver-manager

More info: https://pypi.org/project/webdriver-manager/
           https://github.com/bonigarcia/webdrivermanager/blob/master/README.md

WebDriver will download all the latest driver matched
with the current browser version downloaded into 
working machine, if browser version unknown will 
download the latest version of the driver.

Browser need to be downloaded beforehand
"""


class BaseSelenium:
    browser_name = None
    driver: WebDriver

    def __init__(self):
        self.locator = None

    @classmethod
    def set_up_class(cls):
        """This method will be used for the basic driver setup"""

        browser_list = ['1 = chrome', '2 = firefox', '3 = edge', '4 = chromium']
        print(*browser_list, sep="\n")

        while cls.browser_name not in {1, 2, 3, 4}:
            cls.browser_name = int(input('Choose your browser: '))

            if cls.browser_name == 1:

                chrome_options = webdriver.ChromeOptions()
                chrome_options.add_argument("--disable-notifications")
                cls.driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=chrome_options)

            elif cls.browser_name == 2:
                print("You have chosen: Firefox browser \n")

                # This preference will disappear download bar for firefox
                profile = webdriver.FirefoxProfile()
                profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/json, text/csv")  # mime
                profile.set_preference("browser.download.manager.showWhenStarting", False)
                profile.set_preference("browser.download.dir",
                                       "C:\\Users\\rearf\\Downloads")  # need to be changed accordingly
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

    @classmethod
    def tear_down(cls):
        """This method will be used for teardown the driver instance"""
        time.sleep(5)
        cls.driver.close()
        print("\n--------Now Quiting--------\n")
        cls.driver.quit()
