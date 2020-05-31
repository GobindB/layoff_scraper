from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, \
    StaleElementReferenceException, ElementNotInteractableException
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from decorators import timer, debug
import time
import json
import re


# todo get rid of unnecessary mem wasting id_list, data writes on every iteration
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

            # todo condense, iterate through list of options and sub variables
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
                    final_list['department'] = re.sub(r'\d+', '',
                                                      input_string[input_string.index('PRIOR DEPARTMENT') + 1])
            except (ValueError, IndexError):
                final_list['department'] = 'NULL'

            try:
                if input_string[input_string.index('PRIOR JOB TITLE') + 1] != 'SKILLS':
                    final_list['job_title'] = re.sub(r'\d+', '',
                                                     input_string[input_string.index('PRIOR JOB TITLE') + 1])
            except (ValueError, IndexError):
                final_list['skills'] = 'NULL'

            try:
                if input_string[input_string.index('SKILLS') + 1] != 'UID':
                    final_list['skills'] = re.sub(r'\d+', '', input_string[input_string.index('SKILLS') + 1])
            except (ValueError, IndexError):
                final_list['skills'] = 'NULL'

            try:
                if input_string[input_string.index('LINKEDIN') + 1] != 'EMAIL':
                    final_list['linkedIn'] = input_string[input_string.index('LINKEDIN') + 1]
            except (ValueError, IndexError):
                final_list['linkedIn'] = 'NULL'

            try:
                final_list['email'] = input_string[input_string.index('EMAIL') + 1]
            except (ValueError, IndexError):
                final_list['email'] = 'NULL'

            final_list['user_id'] = input_string[input_string.index('UID') + 1]

            return final_list

        @debug
        def refresh_and_update(n, id_list):
            print("Reloading...")
            self.driver.refresh()
            time.sleep(10)
            scroll(i)
            time.sleep(3)
            id_list.pop()
            if not get_core_data(n, id_list):
                return False
            get_linkedIn(n)
            get_mail(n, id_list)
            return True

        @debug
        def simple_refresh(n):
            print("Reloading...")
            self.driver.refresh()
            time.sleep(10)
            scroll(n)
            time.sleep(3)

        def click_screen(position):
            action = webdriver.common.action_chains.ActionChains(self.driver)
            action.move_to_element_with_offset(position, 20, 20)
            action.click()
            action.perform()

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
            # todo Relocation preference
            try:

                user_info = self.driver.find_elements_by_xpath(
                    "//*[@id='app']/div/div/div/div[4]/div/div[2]/div[2]/div/div[" + str(n + 1) + "]")[0].text + \
                            "\nUID\n" + str(n)

                id_list.append(user_info)

                return True
            except IndexError:
                print("Trying to fetch core data again...")
                if recursion_limit == 0:
                    print("recursive limit reached, skipping...")
                    return False
                else:
                    refresh_and_update(n)

        def get_linkedIn(n):
            try:
                linkedIn = self.driver.find_elements_by_xpath(
                    "// *[@id='app']/div/div/div/div[4]/div/div[2]/div[2]/div/div["
                    + str(n + 1) + "]/div/div/div/div/div/div[2]/div[2]/div/div/div[1]/a")

                check_mail_or_linked(linkedIn, n)

            except (NoSuchElementException, IndexError) as e:
                ids[i] = ids[i] + "\nLINKEDIN: \nNULL"

        def open_mail(n, the_list, recursion_limit=2):
            try:
                time.sleep(3)
                # click email button
                mail_button = self.driver.find_element_by_xpath("//*[@id='app']/div/div/div/div[4]/div/div[2]/div["
                                                                "2]/div/div[" + str(n + 1) +
                                                                "]/div/div/div/div/div/div[""2]/div[2]/div/div/div["
                                                                "2]/button")
                time.sleep(2)
                mail_button.click()

                if not copy_email_address(n, the_list):
                    return False
                else:
                    return True

            except (ElementNotInteractableException, StaleElementReferenceException, NoSuchElementException) as e:

                print("Trying to open mail again... " + str(e))
                if recursion_limit == 0:
                    print("recursive limit reached, skipping email...")
                    return False
                else:
                    time.sleep(2)
                    refresh_and_update(n, the_list)
                    if open_mail(n, the_list, recursion_limit - 1):
                        return True
                    return False

            except ElementClickInterceptedException:

                click_screen(mail_button)

                mail_button = self.driver.find_element_by_xpath("//*[@id='app']/div/div/div/div[4]/div/div[2]/div["
                                                                "2]/div/div[" + str(
                    n + 1) + "]/div/div/div/div/div/div["
                             "2]/div[2]/div/div/div["
                             "2]/button")
                mail_button.click()
                return True

        def close_mail(n):

            try:
                time.sleep(2)
                close_mail_button = self.driver.find_element_by_xpath(
                    "//*[@id='__BVID__" + str(89 + (n * 4)) + "___BV_modal_footer_']/button")
                time.sleep(1)
                close_mail_button.click()
                scroll(n)
                return True

            except (ElementClickInterceptedException, StaleElementReferenceException, NoSuchElementException):
                click_screen(close_mail_button)
                return True

        def copy_email_address(n, the_list):
            try:
                time.sleep(3)
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
            else:
                close_mail(n)
                return True

        page_position = 0
        while page_position < len_page:
            for i in range(100000):
                page_position = scroll(i)
                time.sleep(1)

                if not get_core_data(i, ids):
                    print("Skipping this entire data point.")
                    simple_refresh(i)
                    ids.append("\nNULL\n" + "UID:\n" + str(i))
                    continue

                get_linkedIn(i)

                if not get_mail(i, ids):
                    ids[i] = ids[i] + "\nEMAIL\nNULL"
                    print("Skipping this email data point.")

                process_string(ids[i].split('\n'))
                file.write(json.dumps(final_list))

                print("COUNT: " + str(i + 1) + "\n" + str(final_list) + "\n")

        self.driver.close()
