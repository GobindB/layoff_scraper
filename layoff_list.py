from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, \
    StaleElementReferenceException, ElementNotInteractableException
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from decorators import debug, timer
import time


class Scraper:

    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
        self.url = "https://list.layoffs.fyi/?Prior%20Department=Engineering"

    def begin(self, data_file):

        file = open(data_file, "w")

        self.driver.implicitly_wait(60)
        self.driver.get(self.url)
        len_page = self.driver.execute_script("return document.body.scrollHeight;")
        ids = []

        @debug
        @timer
        def refresh(n, id_list):
            print("Reloading...")
            self.driver.refresh()
            time.sleep(10)
            scroll(i)
            id_list.pop()
            get_core_data(n, id_list)
            get_linkedIn(n)

        def scroll(n):
            self.driver.execute_script("window.scrollTo(0," + str(n * 4) + ")")
            return n * 4

        def check_mail_or_linked(variable, n):
            if "linked" in variable[0].get_attribute('href'):
                ids[n] = ids[n] + "\nLINKEDIN \n" + variable[0].get_attribute('href')
                return True
            elif "@" in variable[0].get_attribute('href'):
                ids[n] = ids[n] + "\nEMAIL: \n" + variable[0].get_attribute('href')[7:]
                return True
            else:
                return False

        def get_core_data(n, id_list):
            # todo Relocation preference, string handling
            try:
                id_list.append(self.driver.find_elements_by_xpath(
                    "//*[@id='app']/div/div/div/div[4]/div/div[2]/div[2]/div/div[" + str(n + 1) + "]")[0].text + \
                               "\nUID:\n" + str(n))
            except IndexError:
                time.sleep(3)
                self.driver.refresh()
                time.sleep(10)
                scroll(n)
                print("Trying to fetch core data again...")
                get_core_data(n, id_list)

        def get_linkedIn(n):
            """todo error handling for when no email and no linkedin (unpredictable behavior); continue, when refresh
             core data is missed"""
            try:
                # click email button, copy email
                linkedIn = self.driver.find_elements_by_xpath(
                    "// *[@id='app']/div/div/div/div[4]/div/div[2]/div[2]/div/div["
                    + str(n + 1) + "]/div/div/div/div/div/div[2]/div[2]/div/div/div[1]/a")

                check_mail_or_linked(linkedIn, n)

            except (NoSuchElementException, IndexError) as e:
                ids[i] = ids[i] + "\nLINKEDIN: \nNULL"

        def open_mail(n, the_list):
            try:
                time.sleep(1)
                # click email button
                mail_button = self.driver.find_element_by_xpath("//*[@id='app']/div/div/div/div[4]/div/div[2]/div["
                                                                "2]/div/div[ " + str(
                    n + 1) + "]/div/div/div/div/div/div["
                             "2]/div[2]/div/div/div["
                             "2]/button")
                mail_button.click()
                # todo see if the right button has been clicked save time searching for close bttn
                # id mail_button has something from clipboard?? then continue
            except (
                    ElementClickInterceptedException, ElementNotInteractableException,
                    StaleElementReferenceException):
                refresh(n, the_list)
                print("Trying to open mail again...")
                open_mail(n, the_list)

        @timer
        def close_mail(n, the_list):
            try:
                email = self.driver.find_elements_by_xpath(
                    "//*[@id='__BVID__" + str(89 + (n * 4)) + "___BV_modal_body_']/a")

                if not check_mail_or_linked(email, n):
                    return False

            except (NoSuchElementException, IndexError):
                ids[i] = ids[i] + "\nEMAIL: \nNULL"

            try:
                time.sleep(1)
                close_mail_button = self.driver.find_element_by_xpath(
                    "//*[@id='__BVID__" + str(89 + (n * 4)) + "___BV_modal_footer_']/button")
                close_mail_button.click()
                scroll(n)
                return True

            except ElementClickInterceptedException:
                refresh(n, the_list)
            except (StaleElementReferenceException, NoSuchElementException):
                pass

        @timer
        def get_mail(n, the_list):
            open_mail(n, the_list)

            if not close_mail(n, the_list):
                return False

        page_position = 0
        while page_position < len_page:
            for i in range(1000):
                page_position = scroll(i)
                time.sleep(1)

                get_core_data(i, ids)
                get_linkedIn(i)

                if get_mail(i, ids):
                    continue

                print("COUNT: " + str(i + 1) + "\n" + ids[i] + "\n")
                file.write(ids[i] + "\n")

        self.driver.close()
