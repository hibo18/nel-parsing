import logging
import json
from parser.hoogvliet.scraper import HoogvlieScraper


logging.basicConfig(level=logging.INFO, format="[%(asctime)s] | %(levelname)s - %(message)s")


def main() -> None:
    data = HoogvlieScraper().get_products()
    with open('data.json', 'w+', encoding='utf-8') as file:
        json.dump(data, file)


if __name__ == "__main__":
    main()