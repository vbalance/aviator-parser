import os
from configuration import configuration
from logger import logger

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager


def create_webdriver(headless: bool = False):
    chrome_profile_path = configuration.get("settings", "chrome_profile_path")
    USER_PROFILE_DIR = chrome_profile_path[:chrome_profile_path.rindex("\\")].replace("\\", "/")
    USER_PROFILE_NAME = chrome_profile_path[chrome_profile_path.rindex("\\")+1:].replace("\\", "/")

    if not os.path.exists(chrome_profile_path):
        raise ValueError("chrome_profile_path folder does not exists. Change chrome_profile_path in config.ini.")

    logger.info("Creating webdriver")
    logger.info(f"Chrome profile path: ...{chrome_profile_path[-20:]}")

    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.page_load_strategy = "eager"

    options.add_argument(f"--user-data-dir={USER_PROFILE_DIR}")
    options.add_argument(f"--profile-directory={USER_PROFILE_NAME}")

    if configuration.getboolean("settings", "visible_webbrowser") is not True or headless is True:
        logger.info("Making webdriver not visible")
        options.add_argument('--headless=new')

    os.system("taskkill /f /im chrome.exe")
    os.system("taskkill /f /im chromedriver.exe")
    driver = webdriver.Chrome(options=options, service=ChromeService(ChromeDriverManager().install()))
    driver.set_page_load_timeout(10)

    return driver
