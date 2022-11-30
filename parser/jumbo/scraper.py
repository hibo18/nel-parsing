import json
import logging
import requests

from typing import List
from pathlib import Path

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By


class JumboScraper:
    
    MAIN_URL = 'https://www.jumbo.com'
    API_CATEGORIES = 'https://www.jumbo.com/api/category-search-api/categories/tree'

    def __init__(self, driver_path: Path | str) -> None:
        logging.info(f"Initial {self.__class__.__name__}...")
        logging.info('Starting webdriver...')
        self.driver = webdriver.Chrome(driver_path)
        logging.info('Webdriver started')
        self.categories = self.get_categories()

    def get_categories(self) -> List[dict]:
        logging.info('Try to get categories...')
        self.driver.get(self.API_CATEGORIES)
        response = self.driver.find_element(By.TAG_NAME, 'body')
        data = json.loads(str(response.text))
        categroies = data['data']['subpages']
        return categroies

    def collect_products(self, url_products: str) -> List[dict]:
        self.driver.get(url_products)
        page_html = self.driver.page_source
        soup = BeautifulSoup(page_html, 'html.parser')
        product_container = soup.find(
            'div',
            {'class': 'jum-card-grid'}
        )
        product_cards = product_container.find_all(
            'article',
            {'class': 'product-container'}
        )

        def wrapper_product_handler(product: BeautifulSoup) -> dict:
            try:
                name = product.find('a', {'class': 'title-link'}).text
                link = self.MAIN_URL + product.find(
                    'a',
                    {'class': 'title-link'}
                )['href']
                img_link = product.find(
                    'img',
                    {'class': 'image'}
                )['src']
                description = ' '.join(
                    product.find('div', {'class': 'subtitle'}).find_all('a').text
                )
                price = product.find(
                    'div',
                    {'class': 'current-price'}
                )
                price = price.find('span').text + '.' + price.findt('sup').text
                old_price = price
                sale = product.find('span', {'class': 'jum-tag prominent'})
                if sale:
                    sale = sale.text
                product_data = {
                    'name': name,
                    'url': link,
                    'img_url': img_link,
                    'description': description,
                    'price': price,
                    'old_price': old_price,
                    'sale': sale
                }
                return product_data
            except Exception:
                return {}
        
        products_data = list(map(
                wrapper_product_handler,
                product_cards
            ))
        return products_data

    def get_products(self) -> List[dict]:
        categories = self.categories
        products_data = []
        for category in categories:
            logging.info(f'Parsing {category["title"]} category...')
            subcategories = category['subpages']
            for subcategory in subcategories:
                url = self.MAIN_URL + subcategory['link']
                logging.info(f'Parsing {subcategory["title"]} subcategory...')
                try:
                    self.driver.get(url)
                    html_page = self.driver.page_source
                    soup = BeautifulSoup(html_page, 'html.parser')
                    soup = soup.find('div', {'class': 'pages-grid'})
                    page_end = soup.find('span', {'class': 'page-text'}).text
                    offset_end = 24 * int(page_end)
                except Exception:
                    continue
                for offset_number in range(0, offset_end, 24):
                    logging.info(f'{offset_number} pagination offset')
                    headers = f'?offSet={offset_number}&pageSize=24'
                    url += headers
                    print(url)
                    products = self.collect_products(url)
                    products_data += products
        return products_data
