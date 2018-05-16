'''
 抓取今日头条街拍美图，并存入mongodb中
'''
import os
from hashlib import md5

import requests
import json
import re
import pymongo

import multiprocessing as mp

BASE_URL = 'https://www.toutiao.com/search_content/?'
client = pymongo.MongoClient()
db = client['toutiao']

def get_list(offset,keyword,count=1):
    #构造请求参数
    param = {
        'offset': offset,
        'format': 'json',
        'keyword': keyword,
        'autoload': 'true',
        'count' : 20,
        'cur_tab': 3,
        'from': 'gallery'
    }
    #转化为url参数
    try:
        response = requests.get(BASE_URL, param, timeout=10)
        if response.status_code == 200:
            return response.json()
    except requests.RequestException:
        count = count + 1
        if count <= 3:
            get_list(offset, keyword, count)
        return None

def get_detail(url,count=1):
    #添加user-agent,否则爬取不了
    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.text
    except requests.RequestException:
        count = count + 1
        if count <= 3:
            get_list(url, count)
        return None

def get_sub_url(data):
    for item in data['data']:
        yield item['article_url']

def parse_detail(page):
    # 提取title和图片连接，media-user
    title = re.compile('<title>(.*?)</title>', re.S)
    mediaInfo = re.compile('mediaInfo: {.*?name:.*?\'(.*?)\',', re.S)
    gallery = re.compile('gallery: JSON.parse\((.*?)\)')
    if page:
        return {
            'title': re.search(title, page).group(1),
            'mediaInfo': re.search(mediaInfo, page).group(1),
            'gallery': re.search(gallery, page).group(1)
        }


def parse_gallery(gallery, title='default'):
    data = json.loads(json.loads(gallery))
    pic_urls = []
    for item in data['sub_images']:
        pic_urls.append(item['url'])
        download_pic(item['url'], title)
    return pic_urls

def save_to_mongo(data):
    if db.pic.insert(data):
        print('save to mongo')
    else:
        print('fail save to mongo')


def download_pic(url, title):
    try:
        res = requests.get(url)
        if res.status_code == 200:
            save_image(res.content, title)
    except requests.RequestException:
        print('download fail')


def save_image(content, title):
    dir_path = '{0}/{1}'.format('/Users/yanqi/picture', title)
    if not os.path.exists(dir_path):
        os.mkdir(dir_path, 0o755)
    file_path = '{0}/{1}.{2}'.format(dir_path, md5(content).hexdigest(), 'jpg')
    if not os.path.exists(file_path):
        with open(file_path, 'wb') as f:
            f.write(content)


def process_data(offset, keyword):
    data = get_list(offset, keyword)
    if data and 'data' in data.keys():
        for item in get_sub_url(data):
            data = parse_detail(get_detail(item))
            pic_urls = parse_gallery(data['gallery'], data['title'])
            data['gallery'] = pic_urls
            save_to_mongo(data)

def main():
    pool = mp.Pool()
    # map 只能传一个参数，starmap传多个参数
    pool.starmap(process_data, [(i*20, '街拍') for i in range(10)])

if __name__ == '__main__':
    main()
