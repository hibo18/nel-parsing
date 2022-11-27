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
        """
            Converting bs4 html's to dict
            
            :categories: iterable, bs4 objects
            
            return list of categories as dict
        """
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
        """
            Make get request to url, parse categories data

            :url_category: url with categories

            return list of categories as dict
        """
        html_page = requests.get(url_category).text
        soup = BeautifulSoup(html_page, 'html.parser')
        soup = soup.find('nav', 'product-category-header__nav')
        html_categories = soup.find_all('li')
        categories = self.convert_categories(html_categories)
        return categories

    def get_product(self, url_product: str) -> dict:
        """
            Make get request to url of product, parse data product

            :url_product: product url

            return list of categories as dict
        """
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
            product_old_price = price_segment.find(
                'div', 'product-card__price__old').text
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
        logging.info(f"{product_name} succesfully scraped!")
        return product

    def collect_product_urls(self, url_subcategory: str) -> List[str]:
        """
            Make get request to url and collect all links to product

            :url_subcategory: subcategory url

            return list of urls
        """
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

    def get_products(self,
        to_category: str = None,
        to_subcategory: str = None,
        is_end: bool = False
    ) -> List[dict]:
        """
            Main method to get all or selected products from category/subcategory.

            :to_category: category name | Copy from site
            :to_subcategory: subcategory name | Copy from site
            :is_end: if false, skips only categories at the beginning
                    if true, parses only the selected category

            return list of products
        """

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
                    products_url = self.collect_product_urls(
                        subcategory_url
                    )
                    logging.info("Handling products...")
                    products_subcategory = list(map(
                        lambda url: self.get_product(url),
                        products_url
                    ))
                    products += products_subcategory
                except AttributeError:
                    logging.warning(
                        f"Subcategory {subcategory['name']} has no products")
        return products
