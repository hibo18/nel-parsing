import requests
import logging
import json

from typing import List
from datetime import datetime
from bs4 import BeautifulSoup

from parser.exceptions import ConnectionError


class CoopScraper:

    MAIN_URL = "https://www.coop.nl"
    MAIN_CATALOG = "https://www.coop.nl/categorie/boodschappen"
    DISCOUNTS_URL = "https://api.coop.nl/INTERSHOP/rest/WFS/COOP-COOPBase-Site/-;loc=nl_NL;cur=EUR/categories/FULL"

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

    def get_categories(self, url_category: str) -> List[dict]:
        response = requests.get(url_category)
        soup = BeautifulSoup(response.text, 'html.parser')
        list_container = soup.find('custom-category-list')
        list_container = list_container.find('div', {'id': 'listContainer'})
        categories_html = list_container.find_all(
                'custom-category-tile',
                {'class': 'ng-star-inserted'}
            )
        def wrapper_category_handler(category: BeautifulSoup) -> dict:
            name = category.find(
                'div',
                {'class': 'category-tile__name'}
            )
            link = category.find('a')['href']
            category_data = {
                'name': name.text,
                'link': self.MAIN_URL + link
            }
            return category_data
        
        categories_data = list(map(
            wrapper_category_handler,
            categories_html
        ))
        return categories_data
    
    def collect_products(self, url_products: str) -> List[dict]:
        resoponse = requests.get(url_products)
        soup = BeautifulSoup(resoponse.text, 'html.parser')
        product_container = soup.find('custom-product-list', {'class': 'ng-star-inserted'})
        products_html = product_container.find_all('div', {'class': 'product-list__column ng-star-inserted'})
        def wrapper_product_handler(product: BeautifulSoup) -> dict:
            name = product.find('p', {'itemprop': 'name'}).text
            logging.info(f"Product {name} parsing...")
            link = product.find('a')['href']
            link_img = product.find(
                    'img',
                    {
                        'class': 'product-image ng-star-inserted',
                        'itemprop': 'image'
                    }
                )['src']
            price = product.find('meta', {'itemprop': 'price'})['content']
            old_price = product.find('div', {'class': 'sticker default'})
            old_price = price
            product_data = {
                'name': name,
                'url': self.MAIN_URL + link,
                'img_url': link_img,
                'price': price,
                'old_price': old_price
            }
            return product_data
        
        products_data = list(map(
            wrapper_product_handler,
            products_html
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
                subcategories = self.get_categories(category_url)
            except AttributeError:
                logging.warning(
                    f"Category {category['name']} has no subcategory!")
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
                    logging.warning(
                        f"Subcategory {subcategory['name']} has no products")
        return products
    