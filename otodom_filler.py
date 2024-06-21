from models import Session, Offers, engine, NominatimApi, OffersLoc
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


class Filler:
    def take_data_from_db(self):

        query = f"""
        SELECT id
        FROM OFFERS_LOC
        WHERE filled = 0

        """
        with engine.connect() as conn:
            self.df = pd.read_sql(sql=query, con=conn.connection)
            self.count = self.df.shape[0]

        return self.df["id"].to_list()

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

        if address != '':

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

        else :
            offer.filled = 1
            session.commit()
            

    def update_chunk_rows(self, list_id):
        self.session = Session()
        for offer_id in list_id:
            self.update_row(offer_id)
        self.session.close()


if __name__ == "__main__":
    model = Filler()
    id_list = model.take_data_from_db()
    model.update_chunk_rows(id_list)


# przetestowac predkosc requests i aiohttp
