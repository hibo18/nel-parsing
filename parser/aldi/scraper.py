import logging
import requests

from bs4 import BeautifulSoup
from typing import List

from parser.exceptions import ConnectionError


class AldiScraper:

    MAIN_URL = "https://www.aldi.nl"
    MAIN_CATALOG = "https://www.aldi.nl/producten.html"

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

    def get_categories(self, category_url: str) -> List[dict]:
        response = requests.get(category_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        categories_container = soup.find('div', {'class': 'tiles-grid'})
        categories_html = categories_container.find_all(
            'div',
            {'class': 'mod mod-content-tile'}
        )
        def wrapper_category_handler(category: BeautifulSoup) -> dict:
            name = category.find(
                'h4',
                {'class': 'mod-content-tile__title'}
            ).text
            link = category.find(
                'a',
                {'class': 'link link--primary'}
            )['href']
            category_data = {
                'name': name,
                'link': self.MAIN_URL + link
            }
            return category_data

        categories = list(map(
            wrapper_category_handler,
            categories_html
        ))
        return categories

    def collect_products(self, products_url: str) -> List[dict]:
        response = requests.get(products_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        products = soup.find_all(
            'div',
            {'class': 'mod-article-tile'}
        )
        def wrapper_product_handler(product: BeautifulSoup) -> dict:
            try:
                name = product.find(
                    'span',
                    {'class': 'mod-article-tile__title'}
                ).text.strip()
                logging.info(f'Parsing {name} product...')
                url = self.MAIN_URL + product.find('a')['href']
                description = product.find(
                    'span',
                    {'class': 'price__unit'}
                ).text
                img_url = self.MAIN_URL + product.find(
                    'img'
                )['data-srcset'].split(',')[-1].split(' ')[0]
                price = product.find(
                    'span',
                    {'class': 'price__wrapper'}
                ).text
                old_price = product.find(
                    's',
                    {'class': 'price__previous'}
                )
            except Exception:
                return {}
            old_price = old_price.text if old_price else price
            product_data = {
                'name': name,
                'description': description,
                'url': url,
                'img_url': img_url,
                'price': price.strip(),
                'old_price': old_price.strip(),
            }
            return product_data

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
                subcategories = self.get_categories(category_url)
            except Exception:
                try:
                    category_products = self.collect_products(
                        category_url)
                    products += category_products
                except AttributeError:
                    pass
                except Exception as e:
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
                except Exception as e:
                    pass
        return products
    