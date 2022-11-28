import logging
import requests

from typing import List
from bs4 import BeautifulSoup


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
    
    def get_categories(self, url_categories: str) -> List[dict]:
        response = requests.get(url_categories)
        soup = BeautifulSoup(response.text, 'html.parser')
        categories_container = soup.find('div', {'class': 'mod_catalog_navigation'})
        categories = categories_container.find_all('li', {'class': 'catalog_navigation_item'})
        def wrapper_category_handler(category: BeautifulSoup) -> dict:
            name = category.find('a').text.strip()
            link = category.find('a')['href']
            category_data = {
                'name': name,
                'link': self.MAIN_URL + '/' + link
            }
            return category_data
        
        categories_data = list(map(
            wrapper_category_handler,
            categories
        ))
        return categories_data