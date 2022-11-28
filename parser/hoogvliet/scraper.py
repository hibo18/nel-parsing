import json
import logging
import requests

from typing import List

from parser.exceptions import ConnectionError


class HoogvlieScraper:

    MAIN_URL = "https://www.hoogvliet.com/"

    API_PRODUCTS = "https://navigator-group1.tweakwise.com/navigation/ed681b01"

    HEADERS = "?tn_q=&tn_p=%s&tn_ps=99&tn_sort=&tn_cid=999999&CatalogPermalink=producten&CategoryPermalink=producten&format=json&tn_parameters=ae-productorrecipe=product"

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
    
    def get_products(self, start_page: int = 1) -> List[dict]:
        page = start_page
        logging.info('Start parsing products...')
        products_data = []

        def wrapper_product_handler(product: dict) -> dict:
            name = product['title']
            logging.info(f'Parsing {name} product...')
            url = product['url']
            img_url = product['image']
            price = product['price']
            product_data = {
                'name': name,
                'url': url,
                'img_url': img_url,
                'price': price,
                'old_price': price
            }
            return product_data

        while(page):
            logging.info(f'Page: #{page}')
            url = self.API_PRODUCTS + self.HEADERS % str(page)
            response = requests.get(url)
            data = json.loads(response.text)
            products = data['items']
            if len(products) == 0:
                page = None
                continue
            products_data += list(map(
                wrapper_product_handler,
                products
            ))
            page += 1
        return products_data