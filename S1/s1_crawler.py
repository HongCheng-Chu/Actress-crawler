import requests
import requests_html
import os
import time
import json
import random
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from lxml import etree
from datetime import datetime

import savefiles
from S1 import s1_updater
from av_manager import AvManager

avc_manager = AvManager()
avc_manager.company = 'S1'


def get_html(url):
    response = requests.get(url, headers = get_headers(), allow_redirects=True)
    return response.text # text return Unicode data -> get text


def get_content(url):
    response = requests.get(url, headers = get_headers(), timeout = 10)
    return response.content # content return bytes(binary) data -> get image, video, file and etc


def download_obj(data, path):
    with open(path, "wb") as file:
        file.write(data)
        file.close()


def get_headers():
    ua = UserAgent()
    headers = {'user-agent': ua.random, 'cookie': avc_manager.cookie}
    return headers


def search_girls():

    ChromeOptions = Options()

    ChromeOptions.add_argument('--headless')

    prefs = {"profile.managed_default_content_settings.images": 2}
    ChromeOptions.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(chrome_options = ChromeOptions)

    time.sleep(5)

    driver.get("https://s1s1s1.com/actress")

    time.sleep(5)

    infos = driver.find_elements_by_xpath("//div[@class='p-hoverCard']")

    actresses = []

    for info in infos:

        root = etree.HTML(info.get_attribute('innerHTML'))

        name_list = root.xpath("//p[@class='name']")

        url_list = root.xpath("//a[@class='img']")

        headshot_list = root.xpath("//a[@class='img']/img")

        actresses.append({'name': name_list[0].text, 'url': url_list[0].get('href'), 'headshot': headshot_list[0].get('data-src')})

    cookie = [item["name"] + "=" + item["value"] for item in driver.get_cookies()]

    cookiestr = ";".join(item for item in cookie)

    driver.quit()

    return actresses, cookiestr


def get_post(url, next_page):

    post_links = []

    image_links = []

    if next_page == 'none':

        page_html = get_html(url)

        page_soup = BeautifulSoup(page_html, 'html.parser')

        cards = page_soup.find("div", {'class':"swiper-slide c-low--6"}).find_all("a", {'class':"item"})

        for card in cards:

            post_links.append(card["href"])

            image = card.find("img")["data-src"]

            image_links.append(image)
            
        time.sleep(2)

    while not next_page == 'none':

        page_html = get_html(url)

        page_soup = BeautifulSoup(page_html, 'html.parser')

        cards = page_soup.find("div", {'class':"swiper-slide c-low--6"}).find_all("a", {'class':"item"})

        for card in cards:

            post_links.append(card["href"])

            image = card.find("img")["data-src"]

            image_links.append(image)

        try:
            next_page = page_soup.find("a", {"rel": "next"})["href"]

        except:
            next_page = 'none'

        url = next_page

        time.sleep(2)

    return post_links, image_links


def get_video(cards, images, name):

    videos = []

    for card, image in zip(cards, images):

        page_html = get_html(card)

        page_soup = BeautifulSoup(page_html, 'html.parser')

        datas = page_soup.find_all("div", {"class": "td"})

        day = datas[1].find("a", {"class": "c-tag c-main-bg-hover c-main-font c-main-bd"})["href"];

        issue_day = day.split('/')[-1].strip()

        issue_number = card.split('/')[-1].split('?')[0]

        issue_title = page_soup.find("h2", {"class": "p-workPage__title"}).getText().strip()

        videos.append({'day': issue_day, 'number': issue_number, 'name': name, 'title': issue_title, 'video': image, 'company': 'S1'})

        time.sleep(3)
    
    return videos


def Download_video(videos):

    for video in videos:
        
        dirpath = r'.\Girls_video.\{0}'.format(data['name'])
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)

        image = get_content(video['image'])

        file_type = video['image'].split('.')[-1]

        file_name = video['day'] + " " + video['number'] + " " + video['name'] + " " + video['title']

        file_path = r'.\girls_video.\{0}\{1}.{2}'.format(video['name'], file_name, file_type)

        try:
            download_obj(image, file_path)

            print('{0} download success'.format(file_name))

        except:
            print('{0} download fail'.format(file_name))

        time.sleep(2)
       
        
def get_data(actress, url):

    html = get_html(url)

    soup = BeautifulSoup(html, "html.parser")

    try :
        next_page = soup.find("a", {"rel": "next"})["href"]

    except:
        next_page = 'none'

    posts, images = get_post(url, next_page)

    videos = get_video(posts, images, actress['name'])

    savefiles.sql_saved(videos, avc_manager.company)
    
    '''
    The following function is choose on you.
    Recommend to use MySQL download which is more quickly.
    '''

    #Download_video(videos)
    #print('Download all post image & video success')
    


def main(sql_password):

    start = time.time()
    
    actresses, cookie = search_girls()

    avc_manager.cookie = cookie
    avc_manager.sql_password = sql_password

    savefiles.save_actresslist(actresses, SQL_password, avc_manager.company)

    for actress in actresses:
        
        last_update_day = savefiles.check_day(actress['name'], avc_manager.company, sql_password)

        if last_update_day:
            s1_updater.main(last_update_day['day'], actress, actress['url'], sql_password, cookie)

        else:
            get_data(actress, actress['url'])

        print('{0} video items save complete.'.format(actress['name']))
    
    print(' Success !!!! ╮(╯  _ ╰ )╭')
    
    end = time.time()

    total_time = end - start

    hour = total_time // 3600

    min = (total_time - 3600 * hour) // 60

    sec = total_time - 3600 * hour - 60 * min

    print(f'Totel spend time:{int(hour)}h {int(min)}m {int(sec)}s')


