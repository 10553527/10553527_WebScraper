import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from time import sleep
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
import pandas
from bs4 import BeautifulSoup

print('### Web of Knowledge ###\n### Web Scraper ###')

url_list = []
add_url = True
delay = 20
correspondence_list = []

# Credentials and Add URL(s)
usr = input('Username: ')
pwd = input('Password: ')

while add_url:
    url = input('Enter URL: ')
    url_list.append(url)
    print('Press "Y" to Add Another or "N" to Start Scraping.')
    user_response = input('Response: ')
    if user_response == 'Y':
        continue
    elif user_response == 'N':
        print('Scraping...')
        add_url = False
    else:
        print('Incorrect Input Detected... Terminating Application...')
        sys.exit()

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

for url in url_list:

    driver.get(url)
    print('Opening Page...')

    sleep(5)

    try:
        driver.find_element(By.ID, 'username').send_keys(usr)
        print('Username Entered.')

        driver.find_element(By.ID, 'password').send_keys(pwd)
        print('Password Entered.')

        login_element = driver.find_element(By.NAME, '_eventId_proceed')
        driver.execute_script('arguments[0].click();', login_element)
        print('Awaiting DUO Authentication...')

        sleep(10)
        
        # MFA
        driver.switch_to.frame(driver.find_element(By.XPATH, '//*[@id="duo_iframe"]'))

        try:
            WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH,
                                                                            '//*[@class="auth-button positive"]')))
            WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, '//*[@class="auth-button positive"]'))
                                           )
            push_notification = driver.find_element(By.XPATH, '//*[@class="auth-button positive"]')
            driver.execute_script('arguments[0].click();', push_notification)
            print('DUO Notification Sent.')
        except NoSuchElementException:
            print('No Element.')
        except TimeoutException:
            print('Waiting for Server...')

        try:
            WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH,
                                                                            '//*[@class="positive auth-button"]')))
            WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, '//*[@class="positive auth-button"]')))
            push_notification = driver.find_element(By.XPATH, '//*[@class="positive auth-button"]')
            driver.execute_script('arguments[0].click();', push_notification)
            print('DUO Notification Sent.')
        except NoSuchElementException:
            print('No Element.')
        except TimeoutException:
            print('Waiting for Server...')
    except NoSuchElementException:
        print('See Window... Verification Failed or Not Required.')

    sleep(10)

    # Reject Cookies
    try:
        WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.XPATH,
                                                                           '//*[@id="onetrust-reject-all-handler"]')))
        WebDriverWait(driver, delay).until(EC.element_to_be_clickable((By.XPATH,
                                                                       '//*[@id="onetrust-reject-all-handler"]')))
        reject_cookies = driver.find_element(By.XPATH, '//*[@id="onetrust-reject-all-handler"]')
        driver.execute_script("arguments[0].click();", reject_cookies)
        print('Rejecting Cookies...')
    except TimeoutException:
        print('Timeout.')
    except NoSuchElementException:
        print('No Element.')

    # Print List of Articles on Page    
    soup = BeautifulSoup(driver.page_source, features='html.parser')

    print(soup.prettify())

    article_list = soup.find_all(class_=['title title-link font-size-18 ng-star-inserted'])
    print('### List of Articles on Page ###')
    for article in article_list:
        print(f'{article.text}')

    count = 0
    keep_going = True

    while keep_going is True:

        while count < 50:

            # Wait for Relevant Elements in URL to Load
            try:
                WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.ID, 'headerLogo'))
                                                                   )
                header = driver.find_element(By.XPATH, '//a[@id="headerLogo"]')
                driver.execute_script("return arguments[0].scrollIntoView(true);", header)
            except TimeoutException:
                print('Waiting for Server...')

            try:
                WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.CLASS_NAME, 'title title-link '
                                                                                                  'font-size-18 ng-star'
                                                                                                  '-inserted')))
                print('Page is Ready!')
            except TimeoutException:
                print('Waiting for Server...')

            # Click the Article Link
            try:
                elements = driver.find_elements(By.XPATH, '//a[@class="title title-link font-size-18 ng-star-inserted"]'
                                                )
                elements[count].click()
                print('Clicking Link...')
            except IndexError:
                print(f'Index of Last Item in List < {count}.')
                keep_going = False
                break

            sleep(5)

            # Find Relevant Elements and Append to correspondence_list as List
            try:
                author_name = driver.find_element(By.XPATH, '//*[@id="SumAuthTa-FrAuthStandard-author-en-0"]')
                author_email = driver.find_element(By.XPATH, '//a[@id="AiinTa-AuthRepEmailAddr-0"]')
                author_address = driver.find_element(By.XPATH, '//*[@id="AiinTa-RepAddressFull-[object Object]"]')
                correspondence_list.append([author_name.text.strip("()"), author_email.text, author_address.text])
            except NoSuchElementException:
                print('No Element.')
            except StaleElementReferenceException:
                print('Stale Element.')
            except TimeoutException:
                print('Waiting for Server...')

            count += 1

            driver.execute_script("window.history.go(-1)")

        # Go to Next Page     
        try:
            next_page = WebDriverWait(driver, delay).until(EC.element_to_be_clickable((By.XPATH,
                                                                                       '//*[@aria-label="Bottom Next '
                                                                                       'Page"]')))
            driver.execute_script('arguments[0].click();', next_page)
            count = 0
        except TimeoutException:
            print('End of Journal.')
            keep_going = False

print('Scraping Complete! List in PycharmProjects.')

# Create DataFrame from correspondence_list
df = pandas.DataFrame(correspondence_list, columns=['Name', 'Email', 'Address'])
df.to_csv('authors.csv', encoding='utf-8', index=False)

input_one = input('Press Any Key to Exit.')
sys.exit()
