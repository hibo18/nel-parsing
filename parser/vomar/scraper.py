import logging
import requests

from typing import List
from bs4 import BeautifulSoup

from parser.exceptions import ConnectionError


class VomarScraper:

    MAIN_URL = "https://www.vomar.nl"
    MAIN_CATALOG = "https://www.vomar.nl/producten"

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

    def get_categories(self, url_category: str, is_sub: bool = False) -> List[dict]:
        response = requests.get(url_category)
        soup = BeautifulSoup(response.text, 'html.parser')
        html_classes = {
            'container': 'productrange' if not is_sub else 'department',
            'category_card': 'col-xs-6' if not is_sub else 'department-group'
        }
        categories_container = soup.find('div', html_classes['container'])
        categories = categories_container.find_all(
            'div', html_classes['category_card'])

        def wrapper_category_handler(category: BeautifulSoup) -> dict:
            name = category.find('span').text
            link = category.find('a')['href']
            category_data = {
                'name': name,
                'link': self.MAIN_URL + link
            }
            return category_data
        categories_data = list(map(
            wrapper_category_handler,
            categories
        ))
        return categories_data

    def collect_products(self, subcategory_url: str) -> List[dict]:
        response = requests.get(subcategory_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        products_container = soup.find('div', {'id': 'products'})
        products = products_container.find_all('div', {'class': 'product'})

        def wrapper_product_handler(product: BeautifulSoup) -> dict:
            try:
                name = product.find('p', {'class': 'description'}).text
                logging.info(f"Product {name} parsing...")
                link = self.MAIN_URL + product.find('a')['href']
                link_image = product.find('img')['src']
                price = product.find('span', {'class': 'large'}).text +\
                    product.find('span', {'class': 'small'}).text
                old_price = product.find('img', {'class': 'discount'})
                old_price = price
                sale = product.find('img', {'class': 'discount'})
                sale = 'discount' if sale else "no discount"
                product_data = {
                    'name': name,
                    'url': link,
                    'img_url': link_image,
                    'price': price,
                    'old_price': old_price,
                    'sale': sale
                }
                return product_data
            except Exception:
                return {}
        products_data = list(map(
            wrapper_product_handler,
            products
        ))
        products_data = list(filter(
            lambda x: len(x) != 0,
            products_data
        ))
        return products_data

    def get_products(
            self,
            to_category: str = None,
            to_subcategory: str = None,
            is_end: bool = False
    ) -> List[dict]:
        categories = self.get_categories(self.MAIN_CATALOG)
        products = []

        for category in categories:
            try:
                if category['name'] != to_category and to_category:
                    logging.info(
                        f"Going to {to_category}, category {category['name']} skipped!")
                    continue
                else:
                    to_category = to_category if is_end else None
                logging.info(f"Handling {category['name']} category...")
                category_url = category['link']
                subcategories = self.get_categories(category_url, is_sub=True)
            except AttributeError:
                continue
            for subcategory in subcategories:
                if subcategory['name'] != to_subcategory and to_subcategory:
                    logging.info(
                        f"Going to {to_subcategory}, category {subcategory['name']} skipped!")
                    continue
                else:
                    to_subcategory = to_subcategory if is_end else None
                logging.info(f"Handling {subcategory['name']} subcategory...")
                subcategory_url = subcategory['link']
                try:
                    subcategory_products = self.collect_products(
                        subcategory_url)
                    products += subcategory_products
                except AttributeError:
                    pass
        return products
    