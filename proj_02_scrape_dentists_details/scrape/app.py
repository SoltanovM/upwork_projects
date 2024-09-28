import re
import os
import boto3
import pandas as pd
import shutil
import pathlib
import warnings
from selenium import webdriver
from datetime import datetime, timedelta
from selenium.common.exceptions import NoSuchElementException
import selenium.webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from time import sleep, time
import sys
from pathlib import Path
from selenium.webdriver.chrome.webdriver import WebDriver
from bs4 import BeautifulSoup

warnings.filterwarnings("ignore")

pathDownload = os.path.join("..", "downloads")
Path(pathDownload).mkdir(parents=True, exist_ok=True)


def open_webdriver():
    url = "https://www.zorgkaartnederland.nl/tandartsenpraktijk"
    chrome_options = get_chrome_options()
    driver = webdriver.Chrome(options=chrome_options)
    # params = {"behavior": "allow", "downloadPath": pathDownload}
    # driver.execute_cdp_cmd("Page.setDownloadBehavior", params)
    driver.get(url)
    return driver


def get_total_page_number(driver: WebDriver):
    totalPageNumber = driver.find_elements(By.XPATH, '//a[@class="page-link"]')[
        -1
    ].get_attribute("text")
    totalPageNumber = int(totalPageNumber)
    return totalPageNumber


def get_chrome_options():
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=2560,1440")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-setuid-sandbox")
    chrome_options.add_argument("--headless")
    # chrome_options.add_argument("--user-data-dir=/home/ubuntu/.config/google-chrome/Default")
    return chrome_options


def get_current_page_instituition_urls(driver: WebDriver):
    XPATH_TABLE_DIV = '//div[@class="filter-results"]'
    table = driver.find_elements(By.XPATH, XPATH_TABLE_DIV)[0]
    XPATH_INSTITIONS = 'div[@class="filter-result"]'
    instDivs = table.find_elements(By.XPATH, XPATH_INSTITIONS)

    instUrls = []
    for instDiv in instDivs:
        # instDiv = instDivs[0]
        elements = instDiv.find_elements(By.XPATH, ".//a")
        for element in elements:
            instUrls.append(element.get_attribute("href"))

    return instUrls


def get_all_instituition_urls(driver: WebDriver):
    totalPageNumber = get_total_page_number(driver)
    allInstUrls = []
    for i in range(1, totalPageNumber + 1):
        print(f"{i=}/{totalPageNumber}")
        urlPage = f"https://www.zorgkaartnederland.nl/tandartsenpraktijk/pagina{i}"
        driver.get(urlPage)
        currentPageInstUrls = get_current_page_instituition_urls(driver)
        currentPageInstUrls = list(set(currentPageInstUrls))
        allInstUrls.extend(currentPageInstUrls)
    return allInstUrls


def get_address(driver: WebDriver):
    addressElement = driver.find_element(By.XPATH, "//address")
    addressElement.find_elements(By.XPATH, "./font")
    address_html = addressElement.get_attribute("innerHTML")
    address_lines = address_html.split("<br>")
    address_lines = [line.strip() for line in address_lines]
    address = "; ".join(address_lines)

    # closeBtn = driver.find_element(By.XPATH, '//button[@class="btn-close"]')
    # closeBtn.click()
    # driver.refresh()
    return address


def get_name(driver: WebDriver):
    instName = driver.find_element(
        By.XPATH, '//h1[@data-sticky-header="name"]'
    ).get_attribute("innerHTML")
    instName = instName.strip()
    return instName


def get_phone_number(driver: WebDriver):
    telElement = driver.find_element(By.XPATH, '//a[starts-with(@href, "tel:")]')
    phoneNumber = telElement.get_attribute("innerHTML")
    phoneNumber = str(phoneNumber).strip()
    return phoneNumber


def get_inst_url(driver: WebDriver):
    urlElement = driver.find_element(
        By.XPATH, '//a[starts-with(@href, "http")][@class="underline"]'
    )
    instWebsiteUrl = urlElement.get_attribute("innerHTML")
    instWebsiteUrl = str(instWebsiteUrl).strip()
    return instWebsiteUrl


def get_dentist_details_urls(driver: WebDriver):
    XPATH_TABLE_DIV = '//div[@class="filter-results"]'
    table = driver.find_elements(By.XPATH, XPATH_TABLE_DIV)[0]
    XPATH_INSTITIONS = 'div[@class="filter-result"]'
    dentistDivs = table.find_elements(By.XPATH, XPATH_INSTITIONS)

    dentistUrls = []
    for dentistDiv in dentistDivs:
        elements = dentistDiv.find_elements(By.XPATH, ".//a")
        for element in elements:
            dentistUrls.append(element.get_attribute("href"))
    dentistUrls = list(set(dentistUrls))

    return dentistUrls


def get_dentist_name(driver: WebDriver):
    dentistName = driver.find_element(
        By.XPATH, '//h1[@data-sticky-header="name"]'
    ).get_attribute("innerHTML")
    return str(dentistName).strip()


def get_profession(driver: WebDriver):
    profession = driver.find_element(
        By.XPATH, '//p[@data-sticky-header="taxonomy"]'
    ).get_attribute("innerHTML")
    return str(profession).strip()


def get_gender(driver: WebDriver):
    genderDiv = driver.find_element(By.XPATH, '//div[contains(text(), "Geslacht")]')
    nextDiv = genderDiv.find_element(By.XPATH, "following-sibling::div[1]")
    return str(nextDiv.text).strip()


def get_works_at(driver: WebDriver):
    worksDiv = driver.find_element(By.XPATH, '//div[contains(text(), "Werkzaam bij")]')
    nextDiv = worksDiv.find_element(By.XPATH, "following-sibling::div[1]")
    placesElements = nextDiv.find_elements(By.XPATH, '//a[@class="address_content"]')
    places = []
    placeLinks = []
    for placeElement in placesElements:
        places.append(str(placeElement.text).strip())
        placeLinks.append(str(placeElement.get_attribute("href")).strip())
    return {"places": places, "placeLinks": placeLinks}


def get_score(driver: WebDriver):
    scoreElement = driver.find_element(
        By.XPATH, '//div[@data-sticky-header="score"]'
    ).get_attribute("innerHTML")
    soup = BeautifulSoup(scoreElement, "html.parser")
    score = soup.get_text(strip=True)
    return score


def get_dentist_data(driver: WebDriver):
    dentistName = get_dentist_name(driver)
    profession = get_profession(driver)
    gender = get_gender(driver)
    worksAt = get_works_at(driver)
    score = get_score(driver)
    dfDentist = pd.DataFrame(
        {
            "dentistName": dentistName,
            "profession": profession,
            "gender": gender,
            "worksAt": [worksAt],
            "score": score,
        }
    )
    return dfDentist


def get_dentists(driver: WebDriver):
    dentistUrls = get_dentist_details_urls(driver)
    dfDentistCons = pd.DataFrame()
    for index, dentistUrl in enumerate(dentistUrls):
        print(f"Getting dentist infos - {index}/{len(dentistUrls)}")
        # dentistUrl = dentistUrls[1]
        driver.get(dentistUrl)
        dfDentist = get_dentist_data(driver)
        dfDentistCons = pd.concat([dfDentistCons, dfDentist])
    return dfDentistCons


def get_instituition_data(driver: WebDriver, url: str):
    driver.get(url)
    instName = get_name(driver)

    XPATH_DETAILSBTN = '//i[@class="icon-home color-theme me-2"]'
    detailsBtn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, XPATH_DETAILSBTN))
    )

    detailsBtn = driver.find_element(By.XPATH, XPATH_DETAILSBTN)

    # driver.execute_script("arguments[0].scrollIntoView(true);", detailsBtn)

    detailsBtn.click()
    sleep(1)

    # ------------------------ Instituition Details ---------------

    address = get_address(driver)
    try:
        phoneNumber = get_phone_number(driver)
    except:
        phoneNumber = "-"
    try:
        instWebsiteUrl = get_inst_url(driver)
    except:
        instWebsiteUrl = "-"
    dfInstituition = pd.DataFrame(
        {
            "instName": [instName],
            "address": [address],
            "phoneNumber": [phoneNumber],
            "instWebsiteUrl": [instWebsiteUrl],
        }
    )

    # ------------------------ dentists --------------------------

    urlDentists = f"{url}/specialisten"
    driver.get(urlDentists)
    dfDentistCons = get_dentists(driver)

    # ------------------------ staging --------------------------
    saveDir = f"{pathDownload}/{instName}"
    Path(saveDir).mkdir(parents=True, exist_ok=True)
    dfDentistCons.to_csv(f"{saveDir}/dentists.csv", index=False)
    dfInstituition.to_csv(f"{saveDir}/instituition_infos.csv", index=False)


def main():
    driver = open_webdriver()
    # allInstUrls = get_all_instituition_urls(driver)
    # dfUrls = pd.DataFrame({"urls": allInstUrls})
    # dfUrls.to_csv(f"{pathDownload}/all_instituition_urls.csv", index=False)
    dfUrls = pd.read_csv(f"{pathDownload}/all_instituition_urls.csv")
    allInstUrls = dfUrls.urls.to_list()
    dfResult = pd.DataFrame()

    dfErrors = pd.DataFrame()
    for i, url in enumerate(allInstUrls):
        # url = allInstUrls[30]
        if i >= 30:
            print(f"Getting infos of instituition - {i}/{len(allInstUrls)}")
            try:
                get_instituition_data(driver, url)
            except Exception as err:
                print(f"ERROR - {err}")
                dfErrors = pd.concat(
                    [dfErrors, pd.DataFrame({"error": [err], "index": [i]})]
                )
    dfErrors.to_csv("ERRORS.csv", index=False)


main()
