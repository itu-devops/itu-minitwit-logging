import time
import schedule
import requests
from random import choice, randint
from bs4 import BeautifulSoup
import logging

logging.getLogger("chardet.charsetprober").setLevel(logging.INFO)
logging.basicConfig(level=logging.DEBUG)


FRONTEND_URL = "http://minitwit:5000"


def job():
    page = randint(0, 100)
    timeline_url = f"{FRONTEND_URL}/public?p={page}"

    print(f"GET: {timeline_url}")
    r = requests.get(timeline_url)
    soup = BeautifulSoup(r.content, "html.parser")
    tweets = soup.find("ul", {"class": "messages"}).findAll("strong")

    tweet = choice(tweets)
    user_timeline_url = f"{FRONTEND_URL}/{tweet.text}"

    logging.debug(f"Client Simulator GET: {user_timeline_url}")
    requests.get(user_timeline_url)


schedule.every(2).seconds.do(job)


while True:
    schedule.run_pending()
    time.sleep(1)
