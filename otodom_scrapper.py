import bs4
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.common.by import By
import time
from bs4 import BeautifulSoup
import pdb
import json
import os
import asyncio


import pandas as pd
import requests
import sys
from datetime import datetime
import timeit

from models import Session, Offers, OtodomWebsite


WEBS = {
    "dom_pierwotny": "https://www.otodom.pl/pl/wyniki/sprzedaz/dom%2Crynek-pierwotny/cala-polska?ownerTypeSingleSelect=ALL&by=DEFAULT&direction=DESC&viewType=listing&limit=72",
    "mieszkanie_pierwotny": "https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie%2Crynek-pierwotny/cala-polska?limit=72&ownerTypeSingleSelect=ALL&by=DEFAULT&direction=DESC&viewType=listing",
    "dom_wtorny": "https://www.otodom.pl/pl/wyniki/sprzedaz/dom,rynek-wtorny/cala-polska?limit=72&ownerTypeSingleSelect=ALL&by=DEFAULT&direction=DESC&viewType=listing",
    "mieszkanie_wtorny": "https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie%2Crynek-wtorny/cala-polska?ownerTypeSingleSelect=ALL&by=DEFAULT&direction=DESC&viewType=listing&limit=72",
    "dzialki": "https://www.otodom.pl/pl/wyniki/sprzedaz/dzialka/cala-polska?ownerTypeSingleSelect=ALL&viewType=listing&limit=72",
}


class Otodom:

    def __init__(self, save_to_db=True):
        self.save_to_db = save_to_db

    def init_driver(self):
        firefox_binary_path = "C:\\Program Files\\Mozilla Firefox\\firefox.exe"
        service = FirefoxService(
            executable_path="C:\projects\small_scrapper\geckodriver\geckodriver.exe"
        )
        firefox_options = Options()
        firefox_options.binary_location = firefox_binary_path
        firefox_options.add_argument("--headless")
        firefox_options.add_argument("--disable-gpu")
        firefox_options.add_argument("--incognito")
        firefox_options.add_argument("--window-size=1600,900")
        firefox_options.add_argument("--no-sandbox")
        self.driver = webdriver.Firefox(options=firefox_options, service=service)

    def create_folder_if_not_exists(self, folder_name):
        current_directory = os.getcwd()
        folder_path = os.path.join(current_directory, folder_name)

        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print(f"Utworzono folder: {folder_name}")
        else:
            print(f"Folder {folder_name} już istnieje.")

    def run(self):
        self.init_driver()
        self.check_pages()

    def accept_cookies(self):
        try:
            self.driver.find_element(
                By.XPATH, "/html/body/div[2]/div[2]/div/div[1]/div/div[2]/div/button[1]"
            ).click()
        except:
            print("No cookies")

    def check_pages(self):
        self.init_driver()
        date = str(datetime.now()).replace(" ", "_").replace(":", "")
        session = Session()
        session.query(OtodomWebsite).update({"active": 0})
        session.commit()

        for type, link in WEBS.items():
            self.type = type
            self.driver.get(link)
            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);"
            )
            time.sleep(2)
            html = self.driver.page_source
            # self.driver.close()
            soup = BeautifulSoup(html, "html.parser")
            buttons = soup.find_all("li", {"class": "css-1tospdx"})
            self.number_of_pages = int(buttons[-1].text)

            website = OtodomWebsite(
                link=link, active=True, num_pages=self.number_of_pages, type=type
            )
            session.add(website)

            print(f"Number of pages : {type} {self.number_of_pages}")

        session.commit()
        session.close()

    def find_wrong_letters(self, my_str):
        x = ""
        for x in my_str:
            try:
                int(x)
            except:
                break
        return x

    def scrap_offers(self, type, page_num):
        start_time = datetime.now()
        website = WEBS[type] + f"&page={page_num}"
        self.driver.get(website)
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        html = self.driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        offers = soup.find_all("div", {"class": ["css-13gthep eeungyz2"]})

        n_offers = len(offers)
        print("Number of offers", n_offers)

        if self.save_to_db:
            session = Session()

        self.elapsed_time = 0
        for offer in offers:
            try:
                link = (
                    "otodom.pl"
                    + offer.find("a", {"class": ["css-16vl3c1 e17g0c820"]})["href"]
                )
            except:
                link = None
            try:
                price = offer.find("div", {"class": ["css-fdwt8z e1nxvqrh0"]}).text
                bad_character = self.find_wrong_letters(price[:-2])
                price = float(price.replace(bad_character, "")[:-2])
            except:
                price = None

            try:
                address = offer.find("div", {"class": ["css-12h460e e1nxvqrh1"]}).text
            except:
                address = None
            try:
                title = offer.find("p", {"class": ["css-3czwt4 endh1010"]}).text
            except:
                title = None
            try:
                rooms = int(
                    offer.find("div", {"class": ["css-1c1kq07 e1clni9t0"]})
                    .find_all("dd")[0]
                    .text.split(" ")[0]
                )
            except:
                rooms = None
            try:
                size = float(
                    offer.find("div", {"class": ["css-1c1kq07 e1clni9t0"]})
                    .find_all("dd")[1]
                    .text.split(" ")[0]
                )
            except:
                size = None
            try:
                price_per_m = float(
                    offer.find("div", {"class": ["css-1c1kq07 e1clni9t0"]})
                    .find_all("dd")[2]
                    .text.split(" ")[0]
                    .strip()
                    .replace("\xa0", " ")
                    .split(" ")[0]
                )
            except:
                price_per_m = None
            try:
                seller = offer.find("div", {"class": ["css-15pdjbs es3mydq3"]}).text

            except:
                try:
                    seller = offer.find("div", {"class": ["css-7rx3ki es3mydq2"]}).text

                except:
                    seller = None
            try:
                seller_type = offer.find(
                    "div", {"class": ["css-196u6lt es3mydq4"]}
                ).text
            except:
                seller_type = None
            try:
                if (
                    offer.find("div", {"class": ["css-gduqhf es3mydq5"]}).text
                    == "Podbite"
                ):
                    bumped = True
                else:
                    bumped = False
            except:
                bumped = False

            if self.save_to_db:
                new_offer = Offers(
                    link=link,
                    type=type,
                    title=title,
                    address=address,
                    rooms=rooms,
                    size=size,
                    price=price,
                    price_per_m=price_per_m,
                    seller=seller,
                    seller_type=seller_type,
                    bumped=bumped,
                    page=page_num,
                )
                session.add(new_offer)
        if self.save_to_db:
            session.commit()

        end_time = datetime.now()
        elapsed_time = (end_time - start_time).total_seconds()
        print(f"Page {page_num}: {elapsed_time} sekund")

    def scrap_pages(self, type, start_page, chunk_size):
        self.init_driver()
        # odpalic selenium i strzelac linkami zapisujac kontent
        for page_num in range(start_page, start_page + chunk_size):
            self.scrap_offers(type, page_num)
        self.driver.close()
        self.driver.quit()

    def pages_from_db(self):
        session = Session()
        pages_to_scrap = (
            session.query(OtodomWebsite).filter(OtodomWebsite.active == 1).all()
        )
        return pages_to_scrap


if __name__ == "__main__":
    model = Otodom()
    n_pages = 104
    chunk_size = 10
    for i in range(0, n_pages, chunk_size):
        start = i + 1
        size = min(chunk_size, n_pages - i)
        model.scrap_pages("test", start, size)
