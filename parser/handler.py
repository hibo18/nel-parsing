import logging
import csv

from typing import List

from parser.aldi.scraper import AldiScraper
from parser.coop.scraper import CoopScraper
from parser.deka.scraper import DekaScraper
from parser.dirk.scraper import DirkScraper
from parser.hoogvliet.scraper import HoogvlieScraper
from parser.janlinders.scraper import JanlindersScraper
from parser.jumbo.scraper import JumboScraper
from parser.poiesz.scraper import PoieszScrapper
from parser.vomar.scraper import VomarScraper


class ParserHandler:

    SCRAPER_CLASSES = [
        AldiScraper,
        CoopScraper,
        DekaScraper,
        DirkScraper,
        HoogvlieScraper,
        JanlindersScraper,
        JumboScraper,
        PoieszScrapper,
        VomarScraper,
    ]

    def __init__(self, path_webdriver: str, ignore_scrapers: list, logging_level) -> None:

        logging.basicConfig(level=logging_level, format="[%(asctime)s] | %(levelname)s - %(message)s")

        scrapers = self.SCRAPER_CLASSES

        def wrapper_scraper_handler(scraper: str):
            if scraper.__name__ in ignore_scrapers:
                return None
            if scraper.__name__ == 'JumboScraper':
                return scraper(path_webdriver)
            return scraper()
        
        scrapers = list(map(
            wrapper_scraper_handler,
            scrapers
        ))
        self.scrapers = list(filter(
            lambda scraper: scraper is not None,
            scrapers
        ))

        logging.info("ALL SCRAPERS INITIALIZED")

    def get_products(self) -> List[dict]:
        basic_classes = [
            'AldiScraper',
            'CoopScraper',
            'DirkScraper',
            'HoogvlieScraper',
            'JanlindersScraper',
            'JumboScraper',
            'PoieszScrapper',
            'VomarScraper',
        ]

        discount_classes = [
            'DekaScraper',
            'JanlindersScraper',
        ]

        offer_classes = [
            'PoieszScrapper',
        ]

        active_scrapers = self.scrapers
        all_products = []

        for scraper in active_scrapers:
            class_name = scraper.__class__.__name__
            if class_name in basic_classes:
                products = scraper.get_products()
                all_products += products
            if class_name in discount_classes:
                products = scraper.get_discounts()
                all_products += products
            if class_name in offer_classes:
                products = scraper.get_offers()
                all_products += products
            
        return all_products

    def save_csv(self, path: str, data: List[dict]) -> None:
        
        columns = [
            'Product_ID', 
            'Product_link', 
            'Product_image_link',
            'Product_name',
            'Product_measure',
            'Product_price',
            'Product_old_price',
            'Sale'
        ]

        def wrapper_unpack_product(product: dict) -> list:
            row = []
            name = product.get('id')
            row.append(name)
            url = product.get('url')
            row.append(url)
            img_url = product.get('img_url')
            row.append(img_url)
            name = product.get('name')
            row.append(name)
            measure = product.get('description')
            row.append(measure)
            price = product.get('price')
            row.append(price)
            old_price = product.get('old_price')
            row.append(old_price)
            sale = product.get('sale')
            row.append(sale)

            return row

        data = list(map(
            wrapper_unpack_product,
            data
        ))

        with open(path, 'w', encoding='utf-8') as csvfile:

            writer = csv.writer(csvfile, delimiter = ",", lineterminator="\r")

            writer.writerow(columns)
            writer.writerows(data)
