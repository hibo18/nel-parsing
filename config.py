from pathlib import Path


ignore_scrapers = [
    'JumboScraper', 
    'DirkScraper',
]

"""
    
    List ignore_scrapers:

    [
        'AldiScraper',
        'CoopScraper',
        'DekaScraper',
        'DirkScraper',
        'HoogvlieScraper',
        'JanlindersScraper',
        'JumboScraper',
        'PoieszScrapper',
        'VomarScraper',
    ]

"""

webdrive_path = Path('chromedriver.exe')

csv_path = Path('data.csv')