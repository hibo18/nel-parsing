import logging
import json
from parser.dirk.scraper import DirkScraper


logging.basicConfig(level=logging.INFO, format="[%(asctime)s] | %(levelname)s - %(message)s")


def main() -> None:
    data = DirkScraper().get_products()
    with open("data.json", 'w+', encoding='utf-8') as file:
        json.dump(data, file)


if __name__ == "__main__":
    main()