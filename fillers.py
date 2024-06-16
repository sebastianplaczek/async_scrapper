from models import Session, Offers, engine, NominatimApi, OffersLoc
import bs4
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.common.by import By
import time
from bs4 import BeautifulSoup


import requests
import pandas as pd


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

    def take_data_from_db(self):

        query = f"""
        SELECT id
        FROM OFFERS
        WHERE filled = 0

        """
        with engine.connect() as conn:
            self.df = pd.read_sql(sql=query, con=conn.connection)
            self.count = self.df.shape[0]

        return self.df["id"].to_list()

    def nominatim_request(self, address, offer_id):
        url = f"http://localhost:8080/search?q={address}&format=json&addressdetails=1&limit=1"
        response = requests.get(url)
        status_code = response.status_code

        if status_code == 200:
            data = response.json()
        else:
            data = None
        if data == [] or data is None:
            empty = True
        else:
            empty = False

        session_db = Session()
        object_db = NominatimApi(
            link=url, status_code=status_code, empty=empty, offer_id=offer_id
        )
        session_db.add(object_db)
        session_db.commit()

        return data

    def ask_api_about_address(self, address, offer_id):

        data = self.nominatim_request(address, offer_id)
        if data and data != []:
            return data
        else:
            address = "".join(address.split(",")[1:])
            data = self.nominatim_request(address, offer_id)
            if data and data != []:
                return data
            else:
                return None

    def update_row(self, offer_id):

        session = Session()
        offer = session.query(Offers).get(offer_id)
        offer_loc = session.query(OffersLoc).filter(OffersLoc.link == offer.link)

        n_offer = offer_loc.count()

        if n_offer == 0:

            address = offer.address

            data = self.ask_api_about_address(address, offer_id)
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
                )

                session.add(new_offer_loc)
                session.commit()
                offer.offer_loc_id = new_offer_loc.id
                offer.filled = 1
                session.commit()
        else:
            offer.filled = 1
            session.commit()

    def update_chunk_rows(self, list_id):
        self.session = Session()
        self.init_driver()
        for offer_id in list_id:
            self.update_row(offer_id)
        self.session.close()
        self.driver.close()


if __name__ == "__main__":
    model = Filler()
    id_list = model.take_data_from_db()[:50]
    model.update_chunk_rows(id_list)


# przetestowac predkosc requests i aiohttp
