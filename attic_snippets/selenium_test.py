from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time

from selenium.webdriver import FirefoxOptions
from selenium.webdriver import ChromeOptions
from selenium.webdriver.firefox.options import Options

opts = Options()
opts.log.level = "trace"
# opts.add_argument("--headless")


# opts = FirefoxOptions()
#opts.add_argument("--headless")
#opts = ChromeOptions()

driver = webdriver.Firefox(firefox_options=opts)
driver.get("http://root:@127.0.0.1:9529/_db/_system/_admin/aardvark/index.html")
time.sleep(3)

assert "ArangoDB Web Interface" in driver.title
elem = driver.find_element_by_id("loginUsername")
elem.clear()
elem.send_keys("root")
elem.send_keys(Keys.RETURN)
time.sleep(13)
elem = driver.find_element_by_id("goToDatabase").click()

assert "No results found." not in driver.page_source
time.sleep(13)
driver.close()
