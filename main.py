# The commented code are the features which I'm currently working on.
# They are unstable, do not use them.

import json
import os
from selenium import webdriver
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.options import Options
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from pathlib import Path
import threading
import patoolib
import shutil
import argparse
import requests


parser = argparse.ArgumentParser()
quality_group = parser.add_mutually_exclusive_group()
quality_group.add_argument('-hq', '--highquality', help='sets the quality option to high', action='store_true')
quality_group.add_argument('-lq', '--lowquality', help='sets the quality option to low', action='store_true')

browser_mode_group = parser.add_mutually_exclusive_group()
browser_mode_group.add_argument('-hd', '--head', help='opens the browser in head mode', action='store_true')
browser_mode_group.add_argument('-hl', '--headless', help='opens the browser in headless mode', action='store_true')

image_destiny_group = parser.add_mutually_exclusive_group()
image_destiny_group.add_argument('-k', '--keep', help='keeps the downloaded images', action='store_true')
image_destiny_group.add_argument('-d', '--delete', help='deletes the downloaded images', action='store_true')

parser.add_argument('-url', help='Paste the url of the comic you want after this argument')


args = parser.parse_args()


# Browser Mode Input
if args.head:
    browser_mode = 'head'
elif args.headless:
    browser_mode = 'headless'
else:
    browser_mode = input('Choose browser mode (head/headless): ')

# Comic Quality Input
if args.highquality:
    quality_set = 'high'
elif args.lowquality:
    quality_set = 'low'
else:
    quality_set = input('Choose quality of the comic (high/low): ')


# Image Destiny Input 
if args.keep:
    delete_image = 'no'
elif args.delete:
    delete_image = 'yes'
else:
    delete_image = input('Do you want to delete images after they get converted to cbr (yes/no): ')

# Comic Url Input
if args.url:
    comic_url = args.url
else:
    comic_url = input('Paste the url of the comic: ')

# comic_url = input("Paste the url of the comic (Enter 'search' to open search mode): ")

# if comic_url == 'search':
#     comic_name = input("Enter comic name: ")
#     year = int(input(f'Enter year of publication of {comic_name} #1: '))
#     if year == 1:
#         issue_number = 1
#     else:
#         issue_number = int(input(f'Which issue of {comic_name} you want: '))


timeout = 25
i = 1
downloading = True

img_urls = {
    'count': None
}

options = Options()

if browser_mode == 'headless':
    options.headless = True

extensions_path = str(Path('extensions').resolve())


browser = webdriver.Firefox(service_log_path=os.path.devnull, options=options, executable_path=GeckoDriverManager().install())
browser.install_addon(extensions_path + r"\ublock_origin-1.29.2-an+fx.xpi")
browser.install_addon(extensions_path + r"\@easyimageblocker.xpi")


# if comic_url == 'search':    
#     url = "https://readcomiconline.to/"

#     browser.get(url)

#     search_bar = WebDriverWait(browser, timeout).until(EC.presence_of_element_located((By.ID, "keyword")))
#     search_bar.send_keys(comic_name + Keys.ENTER)

#     if year == 1:
#         comic = WebDriverWait(browser, timeout).until(EC.presence_of_element_located((By.XPATH, r"(//*[@class='listing']//a)[1] | (//*[@class='list']//a)[1]")))
#         comic.click()
#     else:
#         comic = WebDriverWait(browser, timeout).until(EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, f"{year}")))
#         comic.click()        

#     if year != 1:        
#         top_issue = WebDriverWait(browser, timeout).until(EC.presence_of_element_located((By.XPATH, r"(//*[@class='listing']//a)[1] | (//*[@class='list']//a)[1]")))
#         top_issue_name = top_issue.text
#         top_issue_number = int(top_issue_name.partition("#")[-1])
#         required_issue = top_issue_number - (int(issue_number) - 1)
#         issue = WebDriverWait(browser, timeout).until(EC.presence_of_element_located((By.XPATH, f"(//*[@class='listing']//a)[{required_issue}] | (//*[@class='list']//a)[{required_issue}]")))
#         issue.click()
# else:
#     browser.get(comic_url)

browser.get(comic_url)

if quality_set == 'high':
    quality = Select(WebDriverWait(browser, timeout).until(EC.presence_of_element_located((By.ID, "selectQuality"))))
    quality.select_by_value("hq")


def img_finder(page):
    try:
        img_xpath = r'//*[@id="imgCurrent"]'
        img = WebDriverWait(browser, timeout).until(EC.presence_of_element_located((By.XPATH, img_xpath)))
        link = img.get_attribute('src')
        img_urls.update({f'{page}': link})
        page_number = Select(WebDriverWait(browser, timeout).until(EC.presence_of_element_located((By.ID, "selectPage"))))
        page_number.select_by_visible_text(str(page+1))
    except:
        global downloading
        downloading = False

print('\nScraping readcomiconline...')
while downloading:
    img_finder(i)
    i += 1


img_urls.update({'count': f'{i}'})
json_url_object = json.dumps(img_urls, indent=1)
with open('img_urls_file.json', 'w') as urlfile:
    urlfile.write(json_url_object)

print('Scraped readcomiconline successfully for your comic')
browser.quit()


thread_list = []
path = str(Path('downloads').resolve())
img_files = []

def download_img(json_img_object, img, path):
    img_link = json_img_object.get(f'{img}')
    r = requests.get(img_link, stream = True)
    file_name = f'{path}' + f'\\{img}.jpg'
    with open(file_name, 'wb') as image:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                image.write(chunk)


with open('img_urls_file.json', 'r') as images:
    json_img_object = json.load(images)

img_count = int(json_img_object.get('count'))

print("Downloading comic pages...")
for img in range(1, img_count):
    thread = threading.Thread(target=download_img, args=[json_img_object, img, path])
    thread.start()
    thread_list.append(thread)

for threads in thread_list:
    threads.join()

for r, d, f in os.walk(path):
    for file in f:
        if '.jpg' in file:
            img_files.append(os.path.join(r, file))

print("Converting images into cbr format...")
images = tuple(img_files)



comic_meta_data_arr = comic_url.split('/')
comic_name = comic_meta_data_arr[4]
issue_number = (comic_meta_data_arr[5].split('?'))[0]



patoolib.create_archive(f"{path}\\" + f"{comic_name} {issue_number}.cbr", images, verbosity=-1)

os.remove('img_urls_file.json')

if delete_image == 'yes':
    print("Deleting the images...")
    for f in img_files:
        os.remove(f)
else:
    print(f"Moving downloaded images to pages folder...")
    pages_folder_path = str(Path('pages').resolve())
    new_pages_folder_path = pages_folder_path + f'\\{comic_name} {issue_number}'
    os.mkdir(new_pages_folder_path)
    for f in img_files:
        shutil.move(f, new_pages_folder_path)

print("Download Complete")