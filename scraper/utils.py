import time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

"""Download the HTML of a web page using Selenium"""
def fetch_page(url, element_id):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    service = ChromeService()
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get(url)
    time.sleep(2)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, element_id)))
    html = driver.page_source
    driver.quit()

    return html


"""Parses the HTML and returns a BeautifulSoup object"""
def parse_page(html):
    return BeautifulSoup(html, 'html.parser')