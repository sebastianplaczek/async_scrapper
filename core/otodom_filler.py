from models import Session, Offers, engine, NominatimApi, OffersLoc, CeleryTasks
import bs4
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.common.by import By
import time
from bs4 import BeautifulSoup
import re



import requests
import pandas as pd
import json
from datetime import datetime
import numpy as np


class Filler:

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

    def take_data_from_db(self, filled_type=0, column="id"):

        query = f"""
        SELECT id
        FROM OFFERS_LOC
        WHERE filled = {filled_type}

        """
        with engine.connect() as conn:
            self.df = pd.read_sql(sql=query, con=conn.connection)
            self.count = self.df.shape[0]

        return self.df[f"{column}"].to_list()

    def nominatim_request(self, address, offer_id):
        address_list = re.split(r"[ ,]+", address)

        for i in range(0, len(address_list)):
            try:
                address = " ".join(address_list[i:])
            except:
                pass
            url = f"http://localhost:8080/search?q={address}&format=json&addressdetails=1&limit=1"
            response = requests.get(url)
            status_code = response.status_code

            try:
                data = response.json()
            except Exception as e:
                data = []
                print(e)

            if status_code == 200 and data != []:
                data = response.json()
                empty = False
            else:
                data = None
                empty = True

            session_db = Session()
            object_db = NominatimApi(
                link=url, status_code=status_code, empty=empty, offer_id=offer_id
            )
            session_db.add(object_db)
            session_db.commit()

            try:
                city = data[0]["address"]["town"]
            except:
                try:
                    city = data[0]["address"]["city"]
                except:
                    try:
                        city = data[0]["address"]["village"]
                    except:
                        city = None

            if city:
                return data

        return data

    def update_row(self, offer_id):

        session = Session()
        offer = session.query(OffersLoc).get(offer_id)

        address = offer.address

        if address != "":

            data = self.nominatim_request(address, offer_id)
            if data:
                lat = float(data[0]["lat"])
                lon = float(data[0]["lon"])
                api_address = data[0]["address"]

                try:
                    road = api_address["road"]
                except:
                    road = None
                try:
                    city = api_address["town"]
                except:
                    try:
                        city = api_address["city"]
                    except:
                        try:
                            city = api_address["village"]
                        except:
                            city = None
                try:
                    municipality = api_address["municipality"]
                except:
                    municipality = None
                try:
                    county = api_address["county"]
                except:
                    county = None
                try:
                    vivodeship = api_address["state"].split(" ")[1]
                except:
                    vivodeship = None
                try:
                    postcode = api_address["postcode"]
                except:
                    postcode = None

                new_offer_loc = OffersLoc(
                    lat=lat,
                    lon=lon,
                    city=city,
                    municipality=municipality,
                    county=county,
                    vivodeship=vivodeship,
                    postcode=postcode,
                    link=offer.link,
                    address=offer.address,
                )
                offer.lat = lat
                offer.lon = lon
                offer.city = city
                offer.municipality = municipality
                offer.county = county
                offer.vivodeship = vivodeship
                offer.postcode = postcode
                offer.filled = 1
                session.commit()

        else:
            offer.filled = 1
            session.commit()

    def scrap_additional_params(self, offer_id):

        offer = self.session.query(OffersLoc).get(offer_id)

        self.driver.get("http://www." + offer.link)
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        html = self.driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        additional_params = soup.find_all("div", {"class": ["css-1ivc1bc e26jmad1"]})

        params_dict = {}
        for params in additional_params:
            label = params.find("div", {"class": ["css-rqy0wg e26jmad3"]}).text
            try:
                value = params.find("div", {"class": ["css-1wi2w6s e26jmad5"]}).text
            except:
                value = ""

            if value != "":
                params_dict[label] = value

        offer.filled = 2
        offer.additional_params = json.dumps(params_dict)
        self.session.commit()

    def update_chunk_rows(self, list_id, threads):
        self.session = Session()
        task = CeleryTasks(
            type="nominatim",
            status="QUEUE",
            time_start=datetime.now(),
            pages=len(list_id),
            threads=threads,
        )
        for offer_id in list_id:
            self.update_row(offer_id)

        task.time_end = datetime.now()
        task.runtime = np.round((task.time_end - task.time_start).total_seconds(), 1)
        task.status = "FINISHED"
        self.session.commit()
        self.session.close()

    def scrap_chunk_additional_params(self, id_list):
        self.init_driver()
        self.session = Session()
        for offer_id in id_list:
            self.scrap_additional_params(offer_id)
        self.session.close()
        self.driver.close()
        self.driver.quit()


if __name__ == "__main__":
    model = Filler()
    # id_list = model.take_data_from_db(filled_type=0,column='id')
    id_list = [54567]
    model.update_chunk_rows(id_list)

# if __name__ == "__main__":
#     model = Filler()
#     # id_list = model.take_data_from_db(filled_type=1,column='id')
#     id_list = [278338]
#     model.scrap_chunk_additional_params(id_list)


# przetestowac predkosc requests i aiohttp
