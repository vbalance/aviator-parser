import sys
import os
import traceback
from time import time
from configuration import configuration
from colorama import init as colorama_init
from colorama import Fore, Back, Style
from webdriver import create_webdriver
from logger import logger
from time import sleep
import argparse

from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from dataclasses import dataclass
from datetime import datetime, timedelta

from aviator_excel_writer import open_document, write_payout_info


@dataclass
class PayoutPlayer():
    name: str
    seed: str


@dataclass
class PayoutInfo():
    round_number: str
    result: float
    dt: datetime
    server_seed: str
    client_seeds: list[PayoutPlayer]
    concat_hash: str
    result_hex: str
    result_decimal: str


def switch_to_game_iframe(driver: webdriver.Chrome, wait_for_connection_time: int = 50):
    pu_game_frame = WebDriverWait(driver, timeout=80).until(lambda _: driver.find_element(By.TAG_NAME, "pu-game-frame"))
    game_iframe = pu_game_frame.find_element(By.TAG_NAME, "iframe")

    driver.switch_to.frame(game_iframe)


def get_payouts_block(driver: webdriver.Chrome, timeout: int = 10):
    return WebDriverWait(driver, timeout=timeout).until(lambda _: driver.find_element(By.CSS_SELECTOR, "div.payouts-block"))


def get_last_payout_element(driver: webdriver.Chrome, timeout: int = 10):
    payouts_block = get_payouts_block(driver, timeout=timeout)
    payouts_bubbles = payouts_block.find_elements(By.TAG_NAME, "app-bubble-multiplier")
    return payouts_bubbles[0]


def timedelta_to_string(td: timedelta):
    return str(td).split(".")[0]


def retrieve_last_payout_info(driver, last_payout_element, max_waiting_for_window: int = 10):
    start_click = time()

    while time() - start_click < max_waiting_for_window:
        try:
            last_payout_element.click()
            round_details_window = driver.find_element(By.TAG_NAME, "app-fairness")
            sleep(1.5)
            break
        except:
            sleep(1)
            pass

    else:
        logger.error(f"Waiting too long for payout window. Returning None")
        return None

    round_number = WebDriverWait(driver, timeout=5).until(lambda _: driver.find_element(By.XPATH, "/html/body/ngb-modal-window/div/div/app-fairness/div[1]/span"))
    round_number = round_number.get_attribute("textContent").strip().split(" ")[1]

    result = WebDriverWait(driver, timeout=5).until(lambda _: driver.find_element(By.XPATH, "/html/body/ngb-modal-window/div/div/app-fairness/div[2]/div/div/div[5]/div[6]/span"))
    result = float(result.get_attribute("textContent"))

    time_str = WebDriverWait(driver, timeout=5).until(lambda _: driver.find_element(By.XPATH, "/html/body/ngb-modal-window/div/div/app-fairness/div[1]/div/div[2]"))
    time_str_split = time_str.get_attribute("textContent").split(":")
    dt_now = datetime.now()

    dt = datetime(dt_now.year, dt_now.month, dt_now.day, int(time_str_split[0]), int(time_str_split[1]), int(time_str_split[2]))

    server_seed = WebDriverWait(driver, timeout=5).until(lambda _: driver.find_element(By.XPATH, "/html/body/ngb-modal-window/div/div/app-fairness/div[2]/div/div/div[1]/div[2]/input").get_attribute("value"))

    client_seeds = [
        WebDriverWait(driver, timeout=5).until(lambda _: driver.find_element(By.XPATH, "/html/body/ngb-modal-window/div/div/app-fairness/div[2]/div/div/div[2]/div[2]/div/div[2]/div").get_attribute("textContent")),
        driver.find_element(By.XPATH, "/html/body/ngb-modal-window/div/div/app-fairness/div[2]/div/div/div[2]/div[3]/div/div[2]/div").get_attribute("textContent"),
        driver.find_element(By.XPATH, "/html/body/ngb-modal-window/div/div/app-fairness/div[2]/div/div/div[2]/div[4]/div/div[2]/div").get_attribute("textContent"),
    ]

    client_names = [
        driver.find_element(By.XPATH, "/html/body/ngb-modal-window/div/div/app-fairness/div[2]/div/div/div[2]/div[2]/div/div[1]/div").get_attribute("textContent"),
        driver.find_element(By.XPATH, "/html/body/ngb-modal-window/div/div/app-fairness/div[2]/div/div/div[2]/div[3]/div/div[1]/div").get_attribute("textContent"),
        driver.find_element(By.XPATH, "/html/body/ngb-modal-window/div/div/app-fairness/div[2]/div/div/div[2]/div[4]/div/div[1]/div").get_attribute("textContent"),
    ]

    players = [ PayoutPlayer(n, s) for n, s in zip(client_names, client_seeds) ]

    concat_hash = WebDriverWait(driver, timeout=5).until(lambda _: driver.find_element(By.XPATH, "/html/body/ngb-modal-window/div/div/app-fairness/div[2]/div/div/div[3]/div[2]/input").get_attribute("value"))
    result_hex = driver.find_element(By.XPATH, "/html/body/ngb-modal-window/div/div/app-fairness/div[2]/div/div/div[5]/div[2]/span").get_attribute("textContent")
    result_decimal = driver.find_element(By.XPATH, "/html/body/ngb-modal-window/div/div/app-fairness/div[2]/div/div/div[5]/div[4]/span").get_attribute("textContent")

    close_button = driver.find_element(By.XPATH, "/html/body/ngb-modal-window/div/div/app-fairness/div[1]/button")

    payout_info = PayoutInfo(
        round_number=round_number,
        result=result,
        dt=dt,
        server_seed=server_seed,
        client_seeds=players,
        concat_hash=concat_hash,
        result_hex=result_hex,
        result_decimal=result_decimal
    )

    close_button.click()
    return payout_info

if __name__ == "__main__":
    # Parsing arguments from cmd
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-browser", help="Include this argument to make browser window invisible", action="store_true")
    parser.add_argument("-F", "--file", help="Name of Excel file to write data to. Leave empty to create new one", required=False)

    args = parser.parse_args()
    headless, filename = args.no_browser, args.file

    if filename is None:
        filename_input = input("Enter existing Excel document filename (Leave empty to create new document): ")
        if len(filename_input) < 1:
            filename = None
        else:
            filename = filename_input

    if filename and not os.path.exists(filename):
        logger.info(f"Filename {filename} doesn't exists!")
        sys.exit(1)
    # filename, headless = None, False

    # Main application
    MAIN_URL = "https://pin-up.ua/ru/casino/provider/spribe/aviator?mode=real"
    CONNECT_TIMEOUT = configuration.getint("settings", "connect_timeout")

    driver = create_webdriver(headless)

    logger.info(f"Getting to main page")
    driver.get(MAIN_URL)

    logger.info(f"Waiting {CONNECT_TIMEOUT} seconds for connection...")
    switch_to_game_iframe(driver)

    last_payout = get_last_payout_element(driver, timeout=CONNECT_TIMEOUT)

    logger.info(f"\n\n{Fore.GREEN}Connected!{Style.RESET_ALL}")

    logger.info(f"\nLast payout: {last_payout.text}")
    logger.info("Opening Excel document")

    excel_file, excel = open_document(filename)

    logger.info(f"\n\n{Fore.GREEN}Waiting for new payouts{Style.RESET_ALL}")

    amount = 0
    script_start = datetime.now()

    while True:
        # Check if chat is opened
        try:
            close_chat_button = driver.find_element(By.XPATH, "/html/body/app-root/app-game/div/div[2]/app-chat-widget/div/app-chat-header/div/div[2]/button")
            close_chat_button.click()
        except:
            pass

        # Getting payouts
        try:
            new_last_payout = get_last_payout_element(driver)
        except:
            logger.info(f"{Fore.RED}Erorr!{Style.RESET_ALL}\n")
            traceback.print_exc()
            sleep(0.5)
            continue

        if new_last_payout == last_payout:
            sleep(0.5)
            continue

        last_payout = new_last_payout

        logger.info(f"{Fore.GREEN}New payout: {new_last_payout.text}{Style.RESET_ALL}")

        try:
            payout_info = retrieve_last_payout_info(driver, last_payout)
        except Exception as e:
            logger.info(f"{Fore.RED}Erorr!{Style.RESET_ALL}\n")
            traceback.print_exc()

            logger.info(f"\n{Fore.RED}Trying to close popup window{Style.RESET_ALL}\n")
            close_button = driver.find_elements(By.XPATH, "/html/body/ngb-modal-window/div/div/app-fairness/div[1]/button")

            if len(close_button) == 0:
                logger.info(f"{Fore.RED}Failed to find popup close button. Skipping this payout{Style.RESET_ALL}\n")
                continue
            else:
                logger.info(f"{Fore.YELLOW}Found close button. Clicking.{Style.RESET_ALL}\n")
                close_button[0].click()

            sleep(1)
            continue

        if payout_info is None:
            logger.info(f"{Fore.RED}Failed to parse payout. Skipping.{Style.RESET_ALL}")
            close_buttons = driver.find_elements(By.CSS_SELECTOR, "button.close")
            
            if len(close_buttons) >= 2:
                logger.info(f"{Fore.YELLOW}Trying to close window.{Style.RESET_ALL}")
                close_buttons[1].click()

            continue

        amount += 1
        logger.info(f"Total payouts: {amount}. Working time: {timedelta_to_string(datetime.now() - script_start)}")

        while True:
            try:
                write_payout_info(excel, payout_info)
                sleep(0.5)
                break
            except Exception as e:
                logger.info(f"{Fore.RED}Excel error! Trying again.{Style.RESET_ALL}")
                logger.info(f"{Fore.RED}If you've opened with Excel window, minimize it and try not to interract with it during parser work.{Style.RESET_ALL}")
                traceback.print_exc()

        excel_file.save()
