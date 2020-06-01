from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, \
    StaleElementReferenceException, ElementNotInteractableException
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from decorators import timer
import csv

import time
import re


# todo get rid of unnecessary mem wasting id_list, data writes on every iteration
class Scraper:

    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
        self.url = "https://list.layoffs.fyi/?Prior%20Department=Engineering"

    def begin(self, data_file):

        csv_columns = ['user_id', 'Name', 'email', 'department', 'job_title', 'company', 'skills', 'linkedIn', 'location']


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

        def simple_refresh(n):
            self.driver.refresh()
            time.sleep(5)
            scroll(n)
            time.sleep(1)

        def click_screen(position):
            time.sleep(3)
            action = webdriver.common.action_chains.ActionChains(self.driver)
            action.move_to_element_with_offset(position, 20, 20)
            action.click()
            action.perform()
            time.sleep(1)

        def scroll(n):
            self.driver.execute_script("window.scrollTo({top:" + str(n * 200) + ",behavior: 'smooth',});")
            return n * 200
            time.sleep(3)

        # todo probably dont need this anymore
        def check_mail_or_linked(variable, n):
            try:
                if "linked" in variable:
                    ids[n] = ids[n] + "\nLINKEDIN\n" + variable
                    return True
                elif "@" in variable:
                    ids[n] = ids[n] + "\nEMAIL\n" + variable
                    return True
                else:
                    return False
            except IndexError:
                return False

        def get_core_data(n, id_list):
            # todo Relocation preference
            try:

                click_screen(self.driver.find_elements_by_xpath("//*[@id='app']/div/div/div/div[4]"
                                                                "/div/div[2]/div[2]/div/div[" + str(n + 1) + "]")[0])

                data = self.driver.find_elements_by_xpath(
                    "//*[@id='app']/div/div/div/div[4]/div/div[2]/div[2]/div/div[" + str(n + 1) + "]")[0].text

                if data == '':
                    return False
                else:
                    user_info = data + "\nUID\n" + str(n)
                    id_list.append(user_info)

                return True
            except IndexError:
                return False

        def get_linkedIn(n):
            try:
                linkedIn = self.driver.find_elements_by_xpath(
                    "// *[@id='app']/div/div/div/div[4]/div/div[2]/div[2]/div/div["
                    + str(n + 1) + "]/div/div/div/div/div/div[2]/div[2]/div/div/div[1]/a")

                check_mail_or_linked(linkedIn, n)

            except (NoSuchElementException, IndexError) as e:
                ids[i] = ids[i] + "\nLINKEDIN: \nNULL"

        def open_mail(n, the_list):
            try:
                time.sleep(1)
                mail_button = self.driver.find_element_by_xpath("//*[@id='app']/div/div/div/div[4]/div/div[2]/div["
                                                                "2]/div/div[" + str(n + 1) +
                                                                "]/div/div/div/div/div/div[""2]/div[2]/div/div/div["
                                                                "2]/button")
                time.sleep(1)
                mail_button.click()

                if not copy_email_address(n, the_list):
                    return False
                else:
                    return True

            except (ElementNotInteractableException, StaleElementReferenceException, NoSuchElementException,
                    ElementClickInterceptedException) as e:

                print("Trying to open mail again... " + str(e))
                scroll(n + 1)
                time.sleep(1)
                click_screen(mail_button)
                mail_button = self.driver.find_element_by_xpath("//*[@id='app']/div/div/div/div[4]/div/div[2]/div["
                                                                "2]/div/div[" + str(n + 1) +
                                                                "]/div/div/div/div/div/div[""2]/div[2]/div/div/div["
                                                                "2]/button")
                try:
                    time.sleep(3)
                    mail_button.click()
                except Exception as e:
                    print("error cant get mail " + str(e))
                    return False

        def copy_email_address(n, the_list):
            try:
                time.sleep(3)
                email = self.driver.find_element_by_class_name('modal-body')
                email = email.text
                if check_mail_or_linked(email, n):
                    return True
                else:
                    return False
            except (NoSuchElementException, IndexError):
                the_list[n] = the_list[n] + "\nEMAIL: \nNULL"
                return True

        @timer
        def get_mail(n, the_list):

            if not open_mail(n, the_list):
                return False
            else:
                return True

        with open(data_file, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
            writer.writeheader()
            page_position = 0

            while page_position < len_page:
                for i in range(100000):
                    page_position = scroll(i)
                    time.sleep(1)

                    if not get_core_data(i, ids):
                        print("Skipping this entire data point.")
                        ids.append("\nNULL\n" + "UID:\n" + str(i))
                        simple_refresh(i)
                        continue

                    get_linkedIn(i)

                    if not get_mail(i, ids):
                        ids[i] = ids[i] + "\nEMAIL\nNULL"
                        print("Skipping this email data point.")

                    process_string(ids[i].split('\n'))
                    writer.writerow(final_list)

                    print("COUNT: " + str(i + 1) + "\n" + str(final_list) + "\n")

                    scroll(i)

        self.driver.close()
