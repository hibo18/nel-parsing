import logging
import requests

from typing import List
from bs4 import BeautifulSoup

from parser.exceptions import ConnectionError


class JanlindersScraper:

    MAIN_URL = "https://www.janlinders.nl"
    MAIN_CATALOG = "https://www.janlinders.nl/ons-assortiment.html"

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

    def get_categories(self, url_categories: str, is_sub: bool = False) -> List[dict]:
        response = requests.get(url_categories)
        soup = BeautifulSoup(response.text, 'html.parser')
        if not is_sub:
            categories_container = soup.find(
                'div', {'class': 'mod_catalog_navigation'})
        else:
            categories_container = soup.find(
                'div',
                {'id': 'main'}
            ).find(
                'div',
                'inside'
            )
        category_class = [
            'catalog_navigation_item replace_commas even first',
            'catalog_navigation_item replace_commas odd first',
            'catalog_navigation_item replace_commas odd',
            'catalog_navigation_item replace_commas even',
            'catalog_navigation_item replace_commas odd last',
            'catalog_navigation_item replace_commas even last'
        ]
        subcategory_class = [
            'catalog_navigation_item odd first',
            'catalog_navigation_item even first',
            'catalog_navigation_item even',
            'catalog_navigation_item odd',
            'catalog_navigation_item even last',
            'catalog_navigation_item odd last'
        ]
        ch_class = category_class if not is_sub else subcategory_class
        categories = categories_container.find_all('li', {'class': ch_class})

        def wrapper_category_handler(category: BeautifulSoup) -> dict:
            if not is_sub:
                name = category.find('a')
            else:
                name = category.find('span', {'class': 'title'})
            link = category.find('a')['href']
            category_data = {
                'name': name.text.strip(),
                'link': self.MAIN_URL + '/' + link
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
        products_container = soup.find('div', {'class': 'catalog_list_items'})
        products = products_container.find_all(
            'div', {'class': 'item_container'})

        def wrapper_product_handler(product: BeautifulSoup) -> dict:
            name = product.find('span', {'class': 'teaser'}).text
            name += product.find('h3', {'class': 'item_header'}).find('a').text
            link = product.find(
                'h3', {'class': 'item_header'}).find('a')['href']
            link_image = product.find(
                'div', {'class': 'item_imgcontainer'}).find('img')['src']
            price = product.find('div', {'class': 'pricebox'}).find(
                'span', {'class': 'price'})
            price = price.contents[0] + '.' + price.contents[1].text
            old_price = False
            product_data = {
                'name': name,
                'url': self.MAIN_URL + '/' + link,
                'img_url': link_image,
                'price': price,
                'old_price': old_price
            }
            return product_data
        products_data = list(map(
            wrapper_product_handler,
            products
        ))
        return products_data

    def get_pagination_len(self, url: str) -> int:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        end_pagination = soup.find(
            'div',
            'pagination block'
        ).find('a', {'class': 'last'})['title']
        return int(end_pagination.split(" ")[-1])

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
                    end_pagination = self.get_pagination_len(subcategory_url)
                    for page in range(1, end_pagination + 1):
                        logging.info(
                            f"{subcategory['name']} | Pagination: {page}/{end_pagination}")
                        url = subcategory_url + f'#!page={page}'
                        subcategory_products = self.collect_products(
                            url)
                        products += subcategory_products
                except AttributeError:
                    logging.warning(
                        f"Subcategory {subcategory['name']} has no products")

        return products
