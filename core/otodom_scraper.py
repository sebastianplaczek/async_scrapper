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

import cProfile
import pstats


import pandas as pd
import numpy as np
import requests
import sys
from datetime import datetime
import timeit

from models import (
    Session,
    Offers,
    OtodomWebsite,
    ScrapInfo,
    OffersLoc,
    Runtime,
    ErrorLogs,
    CeleryTasks,
)


WEBS = {
    "dom_pierwotny": "https://www.otodom.pl/pl/wyniki/sprzedaz/dom%2Crynek-pierwotny/cala-polska?ownerTypeSingleSelect=ALL&by=DEFAULT&direction=DESC&viewType=listing&limit=72",
    "mieszkanie_pierwotny": "https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie%2Crynek-pierwotny/cala-polska?limit=72&ownerTypeSingleSelect=ALL&by=DEFAULT&direction=DESC&viewType=listing",
    "dom_wtorny": "https://www.otodom.pl/pl/wyniki/sprzedaz/dom,rynek-wtorny/cala-polska?limit=72&ownerTypeSingleSelect=ALL&by=DEFAULT&direction=DESC&viewType=listing",
    "mieszkanie_wtorny": "https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie%2Crynek-wtorny/cala-polska?ownerTypeSingleSelect=ALL&by=DEFAULT&direction=DESC&viewType=listing&limit=72",
    "dzialki": "https://www.otodom.pl/pl/wyniki/sprzedaz/dzialka/cala-polska?ownerTypeSingleSelect=ALL&viewType=listing&limit=72",
}


class Scraper:

    def __init__(self, save_to_db=True, threads=None):
        self.save_to_db = save_to_db
        self.threads = threads
        self.check_scrap_num()

    def check_scrap_num(self):
        session = Session()
        self.n_scrap = session.query(ScrapInfo).filter(ScrapInfo.active == 1).first().id
        session.close()

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
        # self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        html = self.driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        offers = soup.find_all("div", {"class": ["css-13gthep eeungyz2"]})

        n_offers = len(offers)

        session = Session()

        self.elapsed_time = 0
        for position, offer in enumerate(offers):
            # try:
            (
                link,
                price,
                address,
                title,
                size,
                floor,
                rooms,
                seller,
                seller_type,
                bumped,
            ) = (None, None, None, None, None, None, None, None, None, None)
            try:
                link_element = offer.find("a", {"class": ["css-16vl3c1 e17g0c820"]})
                link = "otodom.pl" + link_element["href"]
            except Exception as e:
                error = ErrorLogs(exception=e)
                session.add(error)

            try:
                price_element = offer.find("div", {"class": ["css-fdwt8z e1nxvqrh0"]})
                price = price_element.text
                bad_character = self.find_wrong_letters(price[:-2])
                if price == "Zapytaj o cenę":
                    price = None
                else:
                    price = float(
                        price.replace(bad_character, "")[:-2].replace(",", ".")
                    )
            except Exception as e:
                value = price_element.text if price_element else None
                error = ErrorLogs(
                    type=type, exception=e, value=value, value_type="price"
                )
                session.add(error)

            try:
                address_element = offer.find(
                    "div", {"class": ["css-12h460e e1nxvqrh1"]}
                )
                address = address_element.text
            except Exception as e:
                value = address_element.text if address_element else None
                error = ErrorLogs(
                    exception=e, value=value, type=type, value_type="address"
                )
                session.add(error)

            try:
                title_element = offer.find("p", {"class": ["css-3czwt4 endh1010"]})
                title = title_element.text
            except Exception as e:
                value = title_element.text if title_element else None
                error = ErrorLogs(
                    exception=e, value=value, type=type, value_type="title"
                )
                session.add(error)

            params = offer.find("div", {"class": ["css-1c1kq07 e1clni9t0"]})
            params_dd = params.find_all("dd")

            if type in ("dom_pierwotny", "dom_wtorny"):
                try:
                    rooms = int(params_dd[0].text.split(" ")[0].replace("+", ""))
                except Exception as e:
                    value = params_dd[0].text
                    error = ErrorLogs(
                        exception=e, value=value, type=type, value_type="rooms"
                    )
                    session.add(error)
                try:
                    size = float(params_dd[1].text.split(" ")[0])
                except Exception as e:
                    value = params_dd[1].text
                    error = ErrorLogs(
                        exception=e, value=value, type=type, value_type="size"
                    )
                    session.add(error)
            elif params_dd and type == "dzialki":
                try:
                    size = float(params_dd[0].text.split(" ")[0])
                except Exception as e:
                    value = params_dd[0].text
                    error = ErrorLogs(
                        exception=e, value=value, type=type, value_type="size"
                    )
                    session.add(error)
            elif params_dd and type in (
                "mieszkanie_pierwotny",
                "mieszkanie_wtorny",
            ):
                try:
                    rooms = int(params_dd[0].text.split(" ")[0].replace("+", ""))
                except Exception as e:
                    value = params_dd[0].text
                    error = ErrorLogs(
                        exception=e, value=value, type=type, value_type="rooms"
                    )
                    session.add(error)

                try:
                    size = float(params_dd[1].text.split(" ")[0])
                except Exception as e:
                    value = params_dd[1].text
                    error = ErrorLogs(
                        exception=e, value=value, type=type, value_type="size"
                    )
                    session.add(error)
                try:
                    if len(params_dd) > 3:
                        floor_elem = params_dd[3].text
                    else:
                        floor_elem = params_dd[2].text
                    if floor_elem == "parter":
                        floor = 0
                    elif "piętro" in floor_elem:
                        floor = int(floor_elem.split(" ")[0].replace("+", ""))
                    else:
                        floor = int(floor_elem)

                    test = 0

                except Exception as e:
                    value = floor_elem
                    error = ErrorLogs(
                        exception=e, value=value, type=type, value_type="floor"
                    )
                    session.add(error)
            try:
                price_per_m = np.round(price / size, 2) if price and size else None
            except Exception as e:
                value = f"{price}/{size}" if price and size else None
                error = ErrorLogs(
                    exception=e, value=value, type=type, value_type="price_per_m"
                )
                session.add(error)

            try:
                seller_element = offer.find("div", {"class": ["css-15pdjbs es3mydq3"]})
                seller = seller_element.text
            except Exception as e:
                seller = None

            try:
                seller_type_element = offer.find(
                    "div", {"class": ["css-196u6lt es3mydq4"]}
                )
                seller_type = seller_type_element.text if seller_type_element else None
            except Exception as e:
                seller_type = None

            try:
                bumped_element = offer.find("div", {"class": ["css-gduqhf es3mydq5"]})
                bumped_text = bumped_element.text
                if bumped_text == "Podbite":
                    bumped = True
                else:
                    bumped = False
            except Exception as e:
                value = bumped_element.text if bumped_element else None
                error = ErrorLogs(
                    exception=e, value=value, type=type, value_type="bumped"
                )
                session.add(error)

            n_offer = session.query(OffersLoc).filter(OffersLoc.link == link).count()

            if n_offer == 0:
                new_link = OffersLoc(
                    type=type,
                    link=link,
                    address=address,
                    rooms=rooms,
                    floor=floor,
                    size=size,
                    price=price,
                    price_per_m=price_per_m,
                    filled=False,
                )
                session.add(new_link)

                if self.save_to_db:
                    session.commit()

                offer_loc_id = new_link.id

            else:
                offer_loc_id = (
                    session.query(OffersLoc).filter(OffersLoc.link == link).first().id
                )

            new_offer = Offers(
                type=type,
                link=link,
                title=title,
                seller=seller,
                seller_type=seller_type,
                bumped=bumped,
                page=page_num,
                position=position,
                n_scrap=self.n_scrap,
                offer_loc_id=offer_loc_id,
            )
            session.add(new_offer)

        # except Exception as e:
        #     print(e)
        end_time = datetime.now()
        elapsed_time = np.round((end_time - start_time).total_seconds(), 1)
        time_per_offer = np.round(elapsed_time / n_offers, 2)
        print(
            f"{type}, page {page_num}, offers {n_offers}: {elapsed_time}s, {time_per_offer}s"
        )

        page_runtime = Runtime(
            type=type,
            n_offers=n_offers,
            page=page_num,
            n_scrap=self.n_scrap,
            threads=self.threads,
            time_s=elapsed_time,
            time_per_offer=time_per_offer,
        )
        session.add(page_runtime)

        if self.save_to_db:
            session.commit()

    def scrap_pages(self, type, start_page, chunk_size):
        self.init_driver()
        session = Session()
        task = CeleryTasks(
            type=type,
            status="QUEUE",
            time_start=datetime.now(),
            pages=chunk_size,
            start_page=start_page,
            threads=self.threads,
        )
        session.add(task)
        session.commit()
        # odpalic selenium i strzelac linkami zapisujac kontent
        for page_num in range(start_page, start_page + chunk_size):
            try:
                self.scrap_offers(type, page_num)
            except Exception as e:
                print(e)
                self.driver.close()
                self.driver.quit()
                self.init_driver()
        self.driver.close()
        self.driver.quit()
        task.time_end = datetime.now()
        task.runtime = np.round((task.time_end - task.time_start).total_seconds(), 1)
        task.status = "FINISHED"
        session.commit()
        session.close()

    def pages_from_db(self):
        session = Session()
        pages_to_scrap = (
            session.query(OtodomWebsite).filter(OtodomWebsite.active == 1).all()
        )
        session.close()
        return pages_to_scrap


if __name__ == "__main__":
    model = Scraper(save_to_db=False, threads=1)
    # links = [object.pages_from_db()[1]]
    # n_pages = links.num_pages
    n_pages = 5
    chunk_size = 5
    for type in [
        # "dzialki",
        "mieszkanie_pierwotny"
        # "mieszkanie_wtorny",
        # "dom_pierwotny",
        # "dom_wtorny",
    ]:
        for i in range(0, n_pages, chunk_size):
            start = i + 1
            size = min(chunk_size, n_pages - i)
            model.scrap_pages(type, start, size)
