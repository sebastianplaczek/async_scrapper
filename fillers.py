from models import Session, Offers, engine, NominatimApi


import requests
import pandas as pd


class Filler:

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

    def nominatim_request(self, address):
        url = f"https://nominatim.openstreetmap.org/search?q={address}&format=json&addressdetails=1&limit=1"
        agent = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36"
        }
        response = requests.get(url, headers=agent)
        status_code = response.status_code
        session_db = Session()
        object_db = NominatimApi(link=url, status_code=status_code)
        session_db.add(object_db)
        session_db.commit()
        if status_code == 200:
            data = response.json()
            return data
        else:
            return None

    def ask_api_about_address(self, address):

        data = self.nominatim_request(address)
        if data and data != []:
            return data
        else:
            address = "".join(address.split(",")[1:])
            data = self.nominatim_request(address)
            if data and data != []:
                return data
            else:
                return None
        # usunac ulice i sprobowac jeszcze raz :)

    def update_row(self, offer_id):

        offer = self.session.query(Offers).filter(Offers.id == offer_id).first()
        address = offer.address

        data = self.ask_api_about_address(address)
        test = 0
        if data:
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            api_address = data[0]["address"]

            try:
                road = api_address["road"]
            except:
                road = None
            try:
                town = api_address["town"]
            except:
                town = None
            try:
                municipality = api_address["municipality"]
            except:
                municipality = None
            try:
                county = aapi_address["county"]
            except:
                county = None
            try:
                state = api_address["state"].split(" ")[1]
            except:
                state = None
            try:
                postcode = api_address["postcode"]
            except:
                postcode = None

            row_values = {
                "lat": lat,
                "lon": lon,
                "city": town,
                "municipality": municipality,
                "county": county,
                "vivodeship": state,
                "postcode": postcode,
                "filled": True,
            }

            offer.update(row_values)
            self.session.commit()

            self.counter += 1
            print(f"{self.counter}/{self.count}")

        else:

            print("No data in response")

    def update_chunk_rows(self, list_id):
        self.session = Session()
        for offer_id in list_id:
            self.update_row(offer_id)
        self.session.close()


if __name__ == "__main__":
    model = Filler()
    id_list = model.take_data_from_db()
    model.update_chunk_rows([54567])


# przetestowac predkosc requests i aiohttp
