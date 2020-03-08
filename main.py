"""Header Information

This module is written to gather the Facebook Events for all Berkeley RSOs. The approach is to first gather the names of all the RSOs on campus, query them against Facebook Developer API to find page_ids and then find events based on each page_id.



Execution:
    In terminal:

        $ python main.py

    Considerations:

        * This module is meant to be run automatically, twice a week on Sundays and Wednesdays. This ensures that all the data recieved is accurate and updated.all(i)

Attributes:


Using the Google Python Style Guide:
   http://google.github.io/styleguide/pyguide.html

"""
import requests
import json
from bs4 import BeautifulSoup
from selenium import webdriver
import time
import subprocess
import json


def get_rso_dict(url):
    club_list = requests.get(url).json()['value']
    rsos = []
    for rso in club_list:
        try:
            relevant_rso = {
                'name': rso['Name'],
                'cal_id': rso['Id'],
                'categories': rso['CategoryNames'],
                'active_events': []
            }
            if rso['WebsiteKey'] is not None:
                relevant_rso['website'] = rso['WebsiteKey'] + '.berkeley.edu'
            elif rso['ProfilePicture'] is not None:
                relevant_rso['picture'] = 'http://se-infra-imageserver2.azureedge.net/clink/images/' + rso['ProfilePicture'] ,

            rsos.append(relevant_rso)
        except Exception as inst:
            print('Error with ' + rso['Name'])
            print(inst)

    return rsos

def getEventData(src):
    dataList = []

    soup = BeautifulSoup(src, features="html.parser")
    upcoming_events = soup.find('div', attrs={'id': 'upcoming_events_card'})
    for event in upcoming_events.findAll("div", class_="_24er"):
        event_month = event.find("span", class_="_5a4-").text.strip()
        event_day = event.find("span", class_="_5a4z").text.strip()
        event_name = event.find("span", class_="_50f7").text.strip()
        event_time = event.find("div", class_="_4dml").find('span').text.strip()
        event_location = event.find("div", class_="_30n-").findChild().text.strip()
        event_link = 'https://www.facebook.com' + event.find("div", class_="_4dmk").findChild()['href']

        event_data = {
            'name': event_name,
            'month': event_month,
            'day': event_day,
            'time': event_time,
            'location': event_location,
            'link': event_link,
        }

        dataList.append(event_data)

    return dataList

def addRSOEvents(rsos):
    option = webdriver.ChromeOptions()
    option.add_argument('headless')
    driver = webdriver.Chrome('C:/Users/respe/chromedriver', options=option)

    driver.get('https://www.facebook.com')
    username = driver.find_element_by_id("email")
    password = driver.find_element_by_id("pass")
    submit   = driver.find_element_by_id("loginbutton")
    username.send_keys("8326910295")
    password.send_keys("enterPassHere")
    submit.click()

    for i in range(len(rsos)):
        rso = rsos[i]
        print("Percent Done: " + str((i / len(rsos)) * 100) + "%", end="")
        try:
            driver.get('https://www.facebook.com/search/pages/?q=' + rso['name'] + '%20berkeley')
            time.sleep(1)
            html = driver.page_source
            soup = BeautifulSoup(html, features="html.parser")
            first_result_link = soup.find('a', class_="_32mo")["href"].replace("https://www.facebook.com/", "", 1)
            page_id = first_result_link[0:first_result_link.find('/')]

            driver.get('https://www.facebook.com/pg/' + page_id + '/events/')
            time.sleep(1)
            html = driver.page_source

            rso['active_events'] = getEventData(html)
        except Exception as inst:
            print('error! RSO Violator: ' + rso['name'])
            print(inst, end="\n\n")

if __name__ == '__main__':
    initTime = time.time()

    rsos = get_rso_dict('https://callink.berkeley.edu/api/discovery/search/organizations?orderBy%5B0%5D=UpperName%20asc&top=2000&filter=&query=&skip=0')
    addRSOEvents(rsos)

    secondsDiff = time.time() - initTime
    print('The whole script took about ' + str("%.2f" % (secondsDiff // 60)) + " minutes and " + str("%.2f" % (secondsDiff % 60)) + " seconds to run")

    with open('berkeley-events.json', 'w') as outfile:
        json.dump(rsos, outfile, indent=4)
