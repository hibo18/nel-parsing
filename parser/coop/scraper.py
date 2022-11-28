import requests

from typing import List
from bs4 import BeautifulSoup

from parser.exceptions import ConnectionError


class CoopScraper:

    def __init__(self) -> None:
        pass

    def get_categories(self, url_category: str) -> List[dict]:
        response = requests.get(url_category)
        soup = BeautifulSoup(response.text, 'html.parser')
