from layoff_list import Scraper

__name__ = '__main__'
Scraper = Scraper()
Scraper.begin('layoff_list_operations.csv')
# try:
#
# except Exception as e:
#     print("Error occurred,  " + str(e))
#     Scraper.driver.close()

