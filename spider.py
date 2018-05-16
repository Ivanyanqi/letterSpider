import requests
from requests.exceptions import RequestException
import re
import time
import multiprocessing as mp
import pymongo
'''
    爬取猫眼电影top100,并保存到文件中去
'''

url = 'https://maoyan.com/board/4?'

client = pymongo.MongoClient()
db = client['maoyan']
def load_page(offset):
    try:
        # 猫眼验证 'user-agent'
        headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.117 Safari/537.36'
        }
        reponse = requests.get(url + 'offset=' + str(offset), headers=headers)
        return reponse.text
    except RequestException:
        print('请求失败!')

def parse_page(result):
    #正则提取数据
    pattern = re.compile('<dd.*?<img.*?data-src="(.*?)".*?<p class="name">.*?>(.*?)</a></p>.*?'
               '<p class="star">(.*?)</p>.*?<p class="releasetime">(.*?)</p>.*?'
               '<p class="score">.*?integer.*?>(.*?)</i>.*?fraction.*?>(.*?)</i>.*?</dd>',re.S);
    resultList = re.findall(pattern, result)
    for e in resultList:
        yield {
            'name': e[1],
            'actors': e[2].strip(),
            'date': e[3],
            'score': e[4] + e[5],
            'imgUrl': e[0]
        }

# 正常抓取
def main():
    start = time.time()
    for result in [load_page(i*10) for i in range(10)]:
        for item in parse_page(result):
            with open('./result.txt','a+') as f:
                f.write(str(item) + '\n')
    end = time.time()
    print(end - start)

def save_to_mongo(result):
    db.films.insert(result)
    print('save to mongo')

#多进程改造 ,推荐
def multi_main():
    start = time.time()
    pool = mp.Pool()
    pages = pool.map(load_page, (i*10 for i in range(10)))
    for result in pages:
        for item in parse_page(result):
            with open('./result.txt','a+') as f:
                f.write(str(item) + '\n')
    end = time.time()
    print(end - start)

def main_to_db():
    start = time.time()
    pool = mp.Pool()
    pages = pool.map(load_page, (i * 10 for i in range(10)))
    for result in pages:
        for item in parse_page(result):
            save_to_mongo(item)
    end = time.time()
    print(end - start)

def process_data(offset):
    result = load_page(offset)
    for item in parse_page(result):
        with open('./result.txt', 'a+') as f:
            f.write(str(item) + '\n')

# 写入的顺序错乱 , 所以抓取top榜单不合适,
def multi_main_a():
    start = time.time()
    pool = mp.Pool()
    pool.map(process_data, (i * 10 for i in range(10)))
    end = time.time()
    print(end - start)

if __name__ == '__main__':
    # main()
    # multi_main()
    # multi_main_a()
    main_to_db()