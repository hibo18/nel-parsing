import requests
import logging

from bs4 import BeautifulSoup
from typing import List, Iterable

from parser.exceptions import ConnectionError


class DirkScraper:

    MAIN_URL = "https://www.dirk.nl/"
    MAIN_CATALOG = "https://www.dirk.nl/boodschappen"

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

    def convert_categories(
            self,
            categories: Iterable[BeautifulSoup]
    ) -> List[dict]:
        data = []
        for html_category in categories:
            html_link = html_category.find('a')
            category = {
                'link': self.MAIN_URL + html_link['href'].strip('/'),
                'name': html_link.text
            }
            data.append(category)
        return data

    def get_categories(self, url_category: str) -> List[dict]:
        html_page = requests.get(url_category).text
        soup = BeautifulSoup(html_page, 'html.parser')
        soup = soup.find('nav', 'product-category-header__nav')
        html_categories = soup.find_all('li')
        categories = self.convert_categories(html_categories)
        return categories

    def get_product(self, url_product: str) -> dict:
        response = requests.get(url_product)
        html_product = BeautifulSoup(response.text, 'html.parser')
        product_name = html_product.find(
                'div', 'product-details__info').find(
                    'h1', 'product-details__info__title').text
        img_url = html_product.find(
                'div', 'product-details__image').find('img')['src']
        price_segment = html_product.find('div', 'product-card__price')
        euros = price_segment.find('span', 'product-card__price__euros').text
        cents = price_segment.find('span', 'product-card__price__cents').text
        product_price = euros + cents
        try:
            product_old_price = price_segment.find('div', 'product-card__price__old').text
        except AttributeError:
            logging.info(f'{product_name} is sold without discount.')
            product_old_price = product_price

        product = {
            'name': product_name,
            'url': url_product,
            'img_url': img_url,
            'price': product_price,
            'old_price': product_old_price.strip()
            }
        return product

    def collect_product_urls(self, url_subcategory: str) -> Iterable[BeautifulSoup]:
        html_page = requests.get(url_subcategory)
        soup = BeautifulSoup(html_page.text, 'html.parser')
        soup = soup.find(
            'div',
            'products-list-container'
        ).find('div', 'products-wrapper')
        products = soup.find_all('div', 'product-card')
        product_urls = list(map(
            lambda product: self.MAIN_URL + product.find(
                'a',
                'product-card__image')['href'].strip('/'),
            products
        ))
        return product_urls

    def get_products(self) -> List[dict]:
        categories = self.get_categories(self.MAIN_CATALOG)
        products = []

        for category in categories:
            logging.info(f"Handling {category['name']} category...")
            category_url = category['link']
            subcategories = self.get_categories(category_url)
            for subcategory in subcategories:
                logging.info(f"Handling {subcategory['name']} subcategory...")
                subcategory_url = subcategory['link']
                products_url = self.collect_product_urls(
                    subcategory_url
                )
                logging.info("Handling products...")
                products_subcategory = list(map(
                    lambda url: self.get_product(url),
                    products_url
                ))
                products += products_subcategory
        return products
            
