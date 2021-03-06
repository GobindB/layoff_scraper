from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, \
    StaleElementReferenceException, ElementNotInteractableException, MoveTargetOutOfBoundsException
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from decorators import timer
import csv

import time
import re


# todo get rid of unnecessary mem wasting id_list, data writes on every iteration
class Scraper:

    def __init__(self, url):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
        self.url = "https://list.layoffs.fyi/?Location=SF%20Bay%20Area%7CSan%20Francisco"

    def begin(self, data_file):

        csv_columns = ['user_id', 'Name', 'email', 'department', 'job_title', 'company', 'skills', 'linkedIn',
                       'location']

        self.driver.implicitly_wait(60)
        self.driver.get(self.url)
        time.sleep(3)
        len_page = self.driver.execute_script("return document.body.scrollHeight;")
        ids = []
        final_list = dict()

        def process_string(input_string):
            """Process text output of webpage"""

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

        def click_screen(position, n):
            """clicks screen at irellevant position in case mail popup still open"""
            time.sleep(4)
            action = webdriver.common.action_chains.ActionChains(self.driver)
            action.move_to_element_with_offset(position, 20, 20)
            action.click()
            try:
                action.perform()
            except MoveTargetOutOfBoundsException:
                scroll(n - 1)
                scroll(n + 1)
                action.perform()

            time.sleep(1)

        def scroll(n):
            self.driver.execute_script("window.scrollTo({top:" + str(n * 180) + ",behavior: 'smooth',});")
            time.sleep(2)
            return n * 180

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

        @timer
        def get_core_data(n, id_list):
            """Returns true and appends core text to id[n] string if core data text exists, false if not."""
            # todo Relocation preference
            try:

                click_screen(self.driver.find_elements_by_xpath("//*[@id='app']/div/div/div/div[4]"
                                                                "/div/div[2]/div[2]/div/div[" + str(n + 1) + "]")[0], n)

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

        @timer
        def get_linkedIn(n):
            """Gets linkedIn URL"""
            try:
                time.sleep(1)
                linkedIn = self.driver.find_elements_by_xpath(
                    "// *[@id='app']/div/div/div/div[4]/div/div[2]/div[2]/div/div["
                    + str(n + 1) + "]/div/div/div/div/div/div[2]/div[2]/div/div/div[1]/a")

                if "linked" in linkedIn[0].get_attribute('href'):
                    ids[n] = ids[n] + "\nLINKEDIN\n" + linkedIn[0].get_attribute('href')
                    return True

            except (NoSuchElementException, IndexError) as e:
                print("no linkedIn...")
                ids[i] = ids[i] + "\nLINKEDIN: \nNULL"
                return False

        def open_mail(n, the_list, recursion=0):
            """Clicks mail link; returns true if opened false if not. Retries once if fail first time"""
            try:
                mail_button = self.driver.find_element_by_xpath("//*[@id='app']/div/div/div/div[4]/div/div[2]/div["
                                                                "2]/div/div[" + str(
                    n + 1) + "]/div/div/div/div/div/div["
                             "2]/div[2]/div/div/div[""2]/button")
                time.sleep(1)

                if 'Similar' in mail_button.text:
                    return False

                elif 'Share' in mail_button.text:
                    try:
                        mail_button = self.driver.find_elements_by_xpath(
                            "//*[@id='app']/div/div/div/div[4]/div/div[2]/div[2]/div/div[" + str(
                                n + 1) + "]/div/div/div/div/"
                                         "div/div[2]/div[2]/div/div/div[1]/button")
                        mail_button[0].click()

                        if not copy_email_address(n, the_list):
                            return False
                        else:
                            return True

                    except (ElementNotInteractableException, StaleElementReferenceException, NoSuchElementException,
                            ElementClickInterceptedException, IndexError) as e:
                        print("no mail...")
                        return False

                mail_button.click()

                if not copy_email_address(n, the_list):
                    return False
                else:
                    return True

            except (StaleElementReferenceException, NoSuchElementException) as e:

                print("Trying to open mail again... " + str(e))
                time.sleep(1)
                recursion += 1
                if recursion == 1:
                    print("error cant get mail " + str(e))
                    return False
                else:
                    scroll(n)
                    open_mail(n, the_list, recursion)
                    return True
            except (ElementNotInteractableException, ElementClickInterceptedException):
                self.driver.refresh()
                time.sleep(6)
                scroll(n)
                time.sleep(2)
                open_mail(n, the_list, recursion)
                return True

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
                print("Skipping this email data point.")
                return False

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

                    flag = get_core_data(i, ids)
                    if not flag:
                        print("Skipping this entire data point.\n")
                        ids.append("\nNULL\n" + "UID:\n" + str(i))
                        scroll(i)
                        time.sleep(2)
                        continue

                    # todo assess redundancy
                    get_linkedIn(i)

                    if not get_mail(i, ids):
                        ids[i] = ids[i] + "\nEMAIL\nNULL"
                        print("Skipping this email data point.")

                    process_string(ids[i].split('\n'))
                    writer.writerow(final_list)

                    print("COUNT: " + str(i + 1) + "\n" + str(final_list) + "\n")

        self.driver.close()
