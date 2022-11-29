import json
import logging
import requests
import traceback

from pathlib import Path
from typing import List
from bs4 import BeautifulSoup

# from parser.exceptions import ConnectionError


class PoieszScrapper:

    MAIN_URL = "https://www.poiesz-supermarkten.nl/"
    API_URL = "https://api.poiesz-supermarkten.nl/api/v1.0/products/%s/%s/products"

    API_OFFERS = "https://api.poiesz-supermarkten.nl/api/v1.0/offers?storeNumber=null"

    PATH_DATA = Path(
            Path.cwd(),
            'parser',
            'poiesz',
            'data',
            'data.json'
        )

    def __init__(self) -> None:
        logging.info(f"Initial {self.__class__.__name__}...")
        logging.info(f"Try to connect {self.MAIN_URL}")
        if not self.isAviable():
            logging.error(f"Can't connect to {self.MAIN_URL}")
            raise ConnectionError(f"Can't connect to {self.MAIN_URL}")
        logging.info(f"{self.MAIN_URL} aviable!")
        logging.info("...initial complete")

    def isAviable(self) -> bool:
        response = requests.get(self.MAIN_URL)
        if response.status_code == 200:
            return True
        return False

    def get_end_page(self, url: str, headers: dict) -> int:
        response = requests.get(
            url=url,
            headers=headers
        )
        data = json.loads(response.text)
        end_page = int(data['paging']['pages'])
        return end_page

    def collect_products(self, url: str, headers: dict) -> List[dict]:
        response = requests.get(
            url=url,
            headers=headers
        )
        data = json.loads(response.text)
        products = data['items']
        def wrapper_product_handler(product: dict) -> dict:
            name = product['name']
            logging.info(f'Parsing {name} product...')
            url = "https://webwinkel.poiesz-supermarkten.nl/boodschappen/producten/" + str(product['id'])
            img_url = product['image']
            price = product['price']
            old_price = price
            product_data = {
                'id': str(product['id']),
                'name': name,
                'url': url,
                'description': product['description'],
                'img_url': img_url,
                'price': price,
                'old_price': old_price,
                'sale': '0%'
            }
            return product_data

        products = list(map(
            wrapper_product_handler,
            products
        ))
        return products

    def get_offers(self) -> List[dict]:
        response = requests.get(self.API_OFFERS)
        data = json.loads(response.text)
        logging.info('Parsing offers...')
        categories = data['categories']
        products_data = []

        for category in categories:
            logging.info(f'Parsing {category["name"]} category...')
            offers = category['offers']

            for product in offers:
                def wrapper_product_handler(product_id: int):
                    product_id = str(product_id)
                    name = product['commercialTextLine1']
                    logging.info(f'Parsing {name} product')
                    url = 'https://webwinkel.poiesz-supermarkten.nl/boodschappen/producten/' + product_id
                    img_url = f'https://webwinkel.poiesz-supermarkten.nl/artikelen/{product_id}.png'
                    desc_1 = product['commercialTextDetailsLine1']
                    desc_1 = desc_1 if desc_1 else ""
                    desc_2 = product['commercialTextDetailsLine2']
                    desc_2 = desc_2 if desc_2 else ""
                    desc_3 = product['commercialTextDetailsLine3']
                    desc_3 = desc_3 if desc_3 else ""
                    description = desc_1 + desc_2 + desc_3
                    price = product['newPriceLow']
                    old_price = product['oldPriceHigh']
                    sale_1 = product['offerTypeLine1']
                    sale_1 = sale_1 if sale_1 else ""
                    sale_2 = product['offerTypeLine2']
                    sale_2 = sale_2 if sale_2 else ""
                    sale_3 = product['offerTypeLine3']
                    sale_3 = sale_3 if sale_3 else ""
                    sale = sale_1 + sale_2 + sale_3
                    product_data = {
                        'id': product_id,
                        'name': name,
                        'description': description,
                        'url': url,
                        'img_url': img_url,
                        'price': price,
                        'old_price': old_price,
                        'sale': sale
                    }
                    return product_data
                
                offer_products_data = list(map(
                    wrapper_product_handler,
                    product['productIDs']
                ))
                products_data += offer_products_data
        return products_data

    def get_products(self) -> List[dict]:
        with open(self.PATH_DATA, 'r', encoding='utf-8') as file:
            categories = json.load(file)
        products = []

        for category in categories:
            category_name = category['name']
            logging.info(f'Parsing {category_name} category...')
            subcategories = category['subcategories']
            
            for subcategory in subcategories:
                subcategory_name = subcategory
                logging.info(f'Parsing {subcategory_name} subcategory...')

                url = self.API_URL % (category_name, subcategory_name)
                headers = {
                    'page': "1",
                    'storeNumber': 'null'
                }
                try:
                    end_page = self.get_end_page(url, headers)
                except json.JSONDecodeError:
                    logging.warning(
                        f"JSONDecodeError : {url}"
                    )

                for page in range(1, end_page + 1):
                    logging.info(f'Parsing {page}/{end_page} page products...')
                    headers['page'] = str(page)
                    try:
                        page_products = self.collect_products(
                            url=url,
                            headers=headers
                        )
                        products += page_products
                    except Exception as e:
                        logging.error(traceback.format_exc())

        return products
        

if __name__ == "__main__":
    pass
