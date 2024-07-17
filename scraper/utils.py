import time
import logging
import re

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.remote_connection import LOGGER as selenium_logger

selenium_logger.setLevel(logging.WARNING)

"""Download the HTML of a web page using Selenium"""


def fetch_page(url, element_id):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")

    service = ChromeService()
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get(url)
        time.sleep(2)
        # Scroll to the bottom to load all card elements
        last_height = driver.execute_script("return document.body.scrollHeight")

        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        # Make sure the target element is rendered
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, element_id))
        )
        html = driver.page_source

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        driver.quit()
        raise e

    finally:
        driver.quit()

    return html


"""Parses the HTML and returns a BeautifulSoup object"""


def parse_page(html):
    return BeautifulSoup(html, "html.parser")


def convert_price(price):
    price = re.sub(r"\D", "", price)
    price = price[:-2] + "." + price[-2:]
    return float(price)
