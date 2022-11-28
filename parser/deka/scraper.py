import logging
import requests

from typing import List
from bs4 import BeautifulSoup


class DekaScraper:

    MAIN_URL = "https://www.dekamarkt.nl"
    MAIN_CATALOG = "https://www.dekamarkt.nl/aanbiedingen"

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
    
    def get_dicounts(self) -> List[dict]:
        response = requests.get(self.MAIN_CATALOG)
        soup = BeautifulSoup(response.text, 'html.parser')
        products = soup.find_all('article', 'deka-product-card')
        def wrapper_product_handler(product: BeautifulSoup) -> dict:
            name = product.find('h3', {
                'class': 'deka-product-card--info--title product-card-title-1'
            }).text
            logging.info(f'Parsing {name} product...')
            url = self.MAIN_URL + product.find(
                'a',
                {'class': 'deka-product-card--image'}
            )['href']
            img_url = product.find('img')['src']
            euros = product.find(
                'span',
                {'class': 'price--before-decimal--offer price-1'}).text
            cents = product.find(
                'span',
                {'class': 'price--after-decimal--offer price-2'}).text
            price = euros + cents
            euros = product.find(
                'span',
                {'class': 'price--before-decimal--regular price-2'})
            cents = product.find(
                'span',
                {'class': 'price--after-decimal--regular price-2'})
            if euros and cents:
                old_price = euros.text + cents.text
            else:
                old_price = price
            product_data = {
                'name': name,
                'url': url,
                'img_url': img_url,
                'price': price,
                'old_price': old_price
            }
            return product_data
        products = list(map(
            wrapper_product_handler,
            products
        ))
        return products
    