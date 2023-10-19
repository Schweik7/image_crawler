import sys
from utils import logger, read_column, cache_progress, rate_limit, Image, d, count_files_in_subdirs
import requests
import gc
from math import ceil
from pathlib import Path
from urllib.parse import urlencode  # url编码里的空格变成+
# import objgraph
# from memory_profiler import profile # 进行一下内存分析

# gc.set_debug(gc.DEBUG_LEAK)

PROGRESS_FILE = "progress_cache.json"
MAX_CRAWL_CNT = 1000
PAGE_CNT = 100 # 最大200
key = "39886586-e8295f58dd0994902919f822f"
crawled_cnt=0
# pixabay 的API图片每页可以达200
# https://pixabay.com/api/?key=39886586-e8295f58dd0994902919f822f&q=yellow+flowers&image_type=photo&pretty=true&page=XXXX&per_page=100

# 将json返回的对象和Image Class的字段进行对应
field_mapping = {
    "id": "id",
    "tags": "tags",
    "user": "author",
    "webformatURL": "preview_link"
}


# import xml.etree.ElementTree as ET
# original_iterparse = ET.iterparse

# def custom_iterparse(*args, **kwargs):
#     import traceback
#     stack_list=traceback.extract_stack()
#     formatted_stack = ''.join(traceback.format_list(stack_list))
#     logger.debug(f"Current stack trace:\n{formatted_stack}")
#     return original_iterparse(*args, **kwargs)

# ET.iterparse = custom_iterparse

def get_search_url(key_words, page=1):
    data = {
        "key": key,
        "q": key_words,
        "image_type": "photo",
        # "pretty": "true",  # 是否缩进；不缩进省流量
        "page": page,
        "per_page": PAGE_CNT
    }
    encode_data = urlencode(data)
    return f"https://pixabay.com/api/?{encode_data}"

# @profile
@cache_progress  # 将记录下当前列表中成功的参数；每次启动时读取成功参数 #
def pixabay_crawl_list(element):
    global crawled_cnt
    logger.debug(f"[+] 开始爬取{element} 关键词")
    res = requests.get(get_search_url(element)).json() 
    crawled_cnt+=1
    hits = res['totalHits']
    logger.info(
        f"[+] 已爬取{crawled_cnt}个关键词。{element}共有{res['total']}张图片，其中有{hits}张图片可供下载")
    hits = 500 if hits >= 500 else hits 
    # if hits==0: # 应该对表格做一些操作
    #     logger.
    pages = ceil(hits/PAGE_CNT)  # ceil是天花板 TODO：我觉得使用200可以减少api使用
    for i in range(pages):
        with rate_limit(90):  # 每分钟是100次，留余量
            logger.info(f"[+] 开始爬取第{i+1}页")
            resp = requests.get(get_search_url(element, page=i+1)).json()
            # logger.debug(resp)
            for im in resp['hits']:
                mapped_data = {
                    field_mapping[key]: value for key, value in im.items()
                    if key in field_mapping
                }
                mapped_data['tags'] = mapped_data['tags'].split(
                    ', ')  # "rough sunflower, flower, plant"
                image = Image(**mapped_data)
                image.platform = 'pixabay'
                # "https://pixabay.com/photos/rough-sunflower-flower-plant-8102444/"
                image.description = im['pageURL'].split(
                    '/')[-2].rsplit('-', 1)[0]
                image.title = Path(
                    f"photo by {image.author} on {image.platform},{image.description},{image.id}").stem
                # 靠忘了存到数据库了
                d.add(
                    file_url=image.preview_link,
                    goal_path=f"images/{element}",
                    rename=image.title,  # pixabay下下来是有png有jpg，unsplash才是
                    file_exists="skip",
                )
                logger.debug(f"[+] 开始下载图片{image.description}")
                del image  # 释放资源

            d.wait()  # 每次将这个关键词爬完再爬取下一个，不然会出现爆内存的情况。
            # 内存占用大大降低，有很大改善——当然后面内存占用又慢慢上来了
    gc.collect()

            


if __name__ == "__main__":
    keywords_list = read_column("爬虫关键词1017.xlsx",column='B')
    image_counter = count_files_in_subdirs(Path("./images"))
    remaining_keywords_list = list(
        set(keywords_list)-set(image_counter.keys()))
    logger.info(f"[+] 有{len(remaining_keywords_list)}个关键词等待爬取")
    pixabay_crawl_list(remaining_keywords_list)

