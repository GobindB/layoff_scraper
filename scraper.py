from layoff_list import Scraper
import sys

"""Command line args: <output_file>.csv, URL to scrape"""

__name__ = '__main__'

Scraper = Scraper(str(sys.argv[2]))

try:
    Scraper.begin(str(sys.argv[1]))
except Exception as e:
    print("Error occurred,  " + str(e))
    Scraper.driver.close()

