from layoff_list import Scraper
import sys

"""Command line args: <output_file>.csv, URL to scrape"""

__name__ = '__main__'
# str(sys.argv[2])
Scraper = Scraper('tst')
# str(sys.argv[1])
try:
    Scraper.begin('layoff_list_product_bay.csv')
except Exception as e:
    print("Error occurred,  " + str(e))
    Scraper.driver.close()

