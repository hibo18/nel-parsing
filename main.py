import logging

import config

from parser.handler import ParserHandler


# Change level to 'logging.WARNING' if you don't wan't see logs 
logging_level = logging.INFO


def main() -> None:

    # Initial handler
    handler = ParserHandler(
        path_webdriver=config.webdrive_path,
        ignore_scrapers=config.ignore_scrapers,
        logging_level=logging_level
    )

    # Get all products...
    products = handler.get_products()

    # Save all products...
    handler.save_csv(config.csv_path, products)


if __name__ == "__main__":
    main()