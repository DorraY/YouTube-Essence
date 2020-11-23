import os
import shutil
import time

import re

import pafy

import requests

from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
# from selenium.webdriver.chrome.options import Options
from selenium.webdriver.firefox.options import Options

from webdriver_manager.firefox import GeckoDriverManager

CHROMEDRIVER_PATH = "/usr/bin/chromedriver"
YOUTUBE_BASE_URL = "https://www.youtube.com/"

options = Options()
#options.headless = True
# driver = webdriver.Chrome(executable_path=ChromeDriverManager.install(), chrome_options=options)
driver = webdriver.Firefox(executable_path=GeckoDriverManager().install(), options=options)
channelUrl = ''
channelName = ''


def make_soup(url):
    try:
        response = requests.get(url)
        soupdata = BeautifulSoup(response.content, "html.parser")
        return soupdata
    except:
        print("An error occured. Cannot proceed...")
        exit(-1)


def validateChannelUrl(link):
    global driver

    if re.match("^((http|https)://)(www\.)youtube\.com/(channel/|user/|c/)[a-zA-Z0-9\-\_]{1,}$", link) is None:
        print("Wrong channel URL")
        print("Try including the whole URL starting by http/https...")
        return False

    try:
        driver.get(link)
    except TimeoutException:
        print("This is taking too long, unable to proceed...")
        driver.quit()
        exit(-1)

    if driver.current_url == "https://www.youtube.com/error?src=404":
        print("Non existant channel")
        return False
    return True


def getChannelFromUser():
    global channelUrl
    channelUrl = input("Enter the channel's url: ").strip()
    while not validateChannelUrl(channelUrl):
        channelUrl = input("Enter the channel's url: ").strip()
    return channelUrl


def retrieveAllVideos(link):
    global driver
    link = link.strip("/") + "/videos"
    try:
        driver.get(link)
        time.sleep(5)
        scroll_pause_time = 1
        screen_height = driver.execute_script("return window.screen.height;")  # get the screen height of the web
        i = 1

        while True:

            # scroll one screen height each time
            driver.execute_script("window.scrollTo(0, {screen_height}*{i});".format(screen_height=screen_height, i=i))
            i += 1
            time.sleep(scroll_pause_time)
            # update scroll height each time after scrolled, as the scroll height can change after we scrolled the page
            scroll_height = driver.execute_script("return document.documentElement.scrollHeight")

            # Break the loop when the height we need to scroll to is larger than the total scroll height
            if screen_height * i > scroll_height:
                break

        videosPageSoup = BeautifulSoup(driver.page_source, "html.parser")

        allAs = videosPageSoup.findAll('a', attrs={"id": "thumbnail"})
        videosUrls = []
        for A in allAs:
            try:
                videosUrls.append(YOUTUBE_BASE_URL.strip("/") + A["href"])


            except KeyError:
                pass

        return videosUrls
    except ConnectionRefusedError:
        print("External connection occured. Try again later.")
        exit(-1)


def downloadVideo(videoLink):
    try:

        # Specifying an API key is optional
        # , as pafy includes one. However,
        # it is prefered that software calling pafy provides it’s own API key,
        # and the default may be removed in the future.
        pafy.set_api_key(yourApiKey)
        ytbVideo = pafy.new(videoLink)

        stream = ytbVideo.getbest(preftype="mp4")
        stream.download()
        print(ytbVideo.title, " downloaded...")
    except OSError:  # if the video is labeled as private, then an error would occur and we won't be able to extract it
        pass


def main():
    global channelUrl
    global channelName
    global driver
    channelUrl = getChannelFromUser().strip("/")
    try:
        channelName = make_soup(channelUrl).get("title")

    except TimeoutException:
        print("This is taking too long, unable to proceed...")
        exit(-1)

    channelName = driver.title.replace("- YouTube", '').strip()
    print("Channel ", channelName, " retreived successfully....")
    allVideosUrls = retrieveAllVideos(channelUrl)

    print("Channel contains ", len(allVideosUrls), " videos.")
    userChoice = input("Want to download them all or abort? Y/N ")

    while userChoice.upper() not in ["Y", "N"]:
        userChoice = input("Wrong choice. Download all or abort ? Y/N ")

    if userChoice.upper() == "N":
        print("Ciao")
        exit(0)
    else:
        if not os.path.exists(channelName):
            os.mkdir(channelName)
            os.chdir(channelName)
            for videoUrl in allVideosUrls:
                downloadVideo(videoUrl)

            driver.quit()

        else:
            shutil.rmtree(channelName)  # delete directory with its contents
            os.mkdir(channelName)
            os.chdir(channelName)
            for videoUrl in allVideosUrls:
                downloadVideo(videoUrl)
            driver.quit()

        print("Finished!")


main()
