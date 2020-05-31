from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, \
    StaleElementReferenceException, ElementNotInteractableException
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from decorators import timer
import time
import json
import re
from string import digits


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
        final_list = dict()

        def process_string(input_string):

            final_list["Name"] = input_string[0]

            # todo condense, iterate through list of option and sub variables
            try:
                if input_string[input_string.index('PRIOR COMPANY') + 1] != 'LOCATION':
                    final_list['company'] = re.sub(r'\d+', '', input_string[input_string.index('PRIOR COMPANY') + 1])
            except (ValueError, IndexError):
                final_list['company'] = 'NULL'

            try:
                if input_string[input_string.index('LOCATION') + 1] != 'PRIOR DEPARTMENT':
                    final_list['location'] = re.sub(r'\d+', '', input_string[input_string.index('LOCATION') + 1])
            except (ValueError, IndexError):
                final_list['location'] = 'NULL'

            try:
                if input_string[input_string.index('PRIOR DEPARTMENT') + 1] != 'PRIOR JOB TITLE':
                    final_list['department'] = re.sub(r'\d+', '', input_string[input_string.index('PRIOR DEPARTMENT') + 1])
            except (ValueError, IndexError):
                final_list['department'] = 'NULL'

            try:
                if input_string[input_string.index('PRIOR JOB TITLE') + 1] != 'SKILLS':
                    final_list['skills'] = re.sub(r'\d+', '', input_string[input_string.index('PRIOR JOB TITLE') + 1])
            except (ValueError, IndexError):
                final_list['skills'] = 'NULL'

            try:
                if input_string[input_string.index('LINKEDIN') + 1] != 'NULL':
                    final_list['linkedIn'] = input_string[input_string.index('LINKEDIN') + 1]
            except (ValueError, IndexError):
                final_list['linkedIn'] = 'NULL'

            try:
                if input_string[input_string.index('EMAIL') + 1] != 'NULL':
                    final_list['email'] = input_string[input_string.index('EMAIL') + 1]
            except (ValueError, IndexError):
                final_list['email'] = 'NULL'

            final_list['user_id'] = input_string[input_string.index('UID') + 1]

            return final_list

        def refresh_and_update(n, id_list):
            print("Reloading...")
            self.driver.refresh()
            time.sleep(10)
            scroll(i)
            id_list.pop()
            if not get_core_data(n, id_list):
                return False
            get_linkedIn(n)
            return True

        def simple_refresh(n):
            self.driver.refresh()
            time.sleep(10)
            scroll(n)

        def scroll(n):
            self.driver.execute_script("window.scrollTo(0," + str(n * 4) + ")")
            return n * 4

        def check_mail_or_linked(variable, n):
            try:
                if "linked" in variable[0].get_attribute('href'):
                    ids[n] = ids[n] + "\nLINKEDIN\n" + variable[0].get_attribute('href')
                    return True
                elif "@" in variable[0].get_attribute('href'):
                    ids[n] = ids[n] + "\nEMAIL\n" + variable[0].get_attribute('href')[7:]
                    return True
                else:
                    return False
            except IndexError:
                return False

        def get_core_data(n, id_list, recursion_limit=2):
            # todo Relocation preference, string handling
            try:

                user_info = self.driver.find_elements_by_xpath(
                    "//*[@id='app']/div/div/div/div[4]/div/div[2]/div[2]/div/div[" + str(n + 1) + "]")[0].text + \
                            "\nUID\n" + str(n)

                id_list.append(user_info)

                return True
            except IndexError:
                time.sleep(3)
                simple_refresh(n)
                print("Trying to fetch core data again...")
                if recursion_limit == 0:
                    return False
                else:
                    get_core_data(n, id_list, recursion_limit - 1)

        def get_linkedIn(n):
            # todo error handling for when no email and no linkedin (unpredictable behavior); continue, when refresh
            try:
                # click email button, copy email
                linkedIn = self.driver.find_elements_by_xpath(
                    "// *[@id='app']/div/div/div/div[4]/div/div[2]/div[2]/div/div["
                    + str(n + 1) + "]/div/div/div/div/div/div[2]/div[2]/div/div/div[1]/a")

                check_mail_or_linked(linkedIn, n)

            except (NoSuchElementException, IndexError) as e:
                ids[i] = ids[i] + "\nLINKEDIN: \nNULL"

        def open_mail(n, the_list, recursion_limit=3):
            try:
                time.sleep(3)
                # click email button
                mail_button = self.driver.find_element_by_xpath("//*[@id='app']/div/div/div/div[4]/div/div[2]/div["
                                                                "2]/div/div[ " + str(
                    n + 1) + "]/div/div/div/div/div/div["
                             "2]/div[2]/div/div/div["
                             "2]/button")
                mail_button.click()
                time.sleep(4)
                if not copy_email_address(n, the_list):
                    return False
                else:
                    return True
            except (
                    ElementClickInterceptedException, ElementNotInteractableException,
                    StaleElementReferenceException, NoSuchElementException) as e:
                print("Trying to open mail again... " + str(e))
                refresh_and_update(n, the_list)
                if recursion_limit == 0:
                    return False
                open_mail(n, the_list, recursion_limit - 1)

        def close_mail(n, the_list):

            try:
                time.sleep(1)
                close_mail_button = self.driver.find_element_by_xpath(
                    "//*[@id='__BVID__" + str(89 + (n * 4)) + "___BV_modal_footer_']/button")
                close_mail_button.click()
                scroll(n)
                return True

            except ElementClickInterceptedException:
                simple_refresh()
            except (StaleElementReferenceException, NoSuchElementException):
                pass

        def copy_email_address(n, the_list):
            try:
                email = self.driver.find_elements_by_xpath(
                    "//*[@id='__BVID__" + str(89 + (n * 4)) + "___BV_modal_body_']/a")

                if not check_mail_or_linked(email, n):
                    return False

                return True
            except (NoSuchElementException, IndexError):
                the_list[n] = the_list[n] + "\nEMAIL: \nNULL"
                return True

        @timer
        def get_mail(n, the_list):

            if not open_mail(n, the_list):
                return False
            elif not close_mail(n, the_list):
                return False
            else:
                return True

        page_position = 0
        while page_position < len_page:
            for i in range(1000):
                page_position = scroll(i)
                time.sleep(1)

                if not get_core_data(i, ids):
                    print("Skipping this entire data point.")
                    ids.append("\nNULL\n" + "UID:\n" + str(i))
                    continue

                get_linkedIn(i)

                if not get_mail(i, ids):
                    ids[i] = ids[i] + "\nEMAIL: \nNULL"
                    print("Skipping this email data point. \nCOUNT: " + str(i + 1) + "\n" + ids[i] + "\n")
                    continue

                process_string(ids[i].split('\n'))
                file.write(json.dumps(final_list))

                print("COUNT: " + str(i + 1) + "\n" + str(final_list) + "\n")

        self.driver.close()

# todo get rid of unnecessary id_list
