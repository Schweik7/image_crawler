import sys
from utils import logger, read_first_column, cache_progress, rate_limit, Image,d
import requests

from math import ceil
from pathlib import Path
from urllib.parse import urlencode  # url编码里的空格变成+

# import requests


PROGRESS_FILE = "progress_cache.json"
MAX_CRAWL_CNT = 1000
PAGE_CNT = 100
key = "39886586-e8295f58dd0994902919f822f"

# pixabay 的API图片每页可以达200
# https://pixabay.com/api/?key=39886586-e8295f58dd0994902919f822f&q=yellow+flowers&image_type=photo&pretty=true&page=XXXX&per_page=100

# 将json返回的对象和Image Class的字段进行对应
field_mapping = {
    "id": "id",
    "tags": "tags",
    "user": "author",
    "webformatURL": "preview_link"
}


def get_search_url(key_words, page=1):
    data = {
        "key": key,
        "q": key_words,
        "image_type": "photo",
        "pretty": "true",  # 是否缩进
        "page": page,
        "per_page": PAGE_CNT
    }
    encode_data = urlencode(data)
    return f"https://pixabay.com/api/?{encode_data}"


@cache_progress  # 将记录下当前列表中成功的参数；每次启动时读取成功参数
def pixabay_crawl_list(element):
    logger.debug(f"[+] 开始爬取{element} 关键词")
    cnt = 0
    res = requests.get(get_search_url(element)).json()

    hits = res['totalHits']
    logger.info(
        f"[+] 关键词{element}共有{res['total']}张图片，其中有{hits}张图片可供下载")
    hits = 500 if hits >= 500 else hits
    pages = ceil(hits/PAGE_CNT) # ceil是天花板
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
                mapped_data['tags'] = mapped_data['tags'].split(', ') # "rough sunflower, flower, plant"
                image = Image(**mapped_data)
                image.platform = 'pixabay'
                # "https://pixabay.com/photos/rough-sunflower-flower-plant-8102444/"
                image.description = im['pageURL'].split(
                    '/')[-2].rsplit('/', 1)[0]
                image.title = Path(
                    f"photo by {image.author} on {image.platform},{image.description},{image.id}").stem
                # 靠忘了存到数据库了
                if cnt <= hits:
                    d.add(
                        file_url=image.preview_link,
                        goal_path=f"images/{element}",
                        rename=image.title, # pixabay下下来是有png有jpg，unsplash才是
                        file_exists="skip",
                    )
                    logger.debug(f"[+] 开始下载图片{image.description}")
                    del image # 释放资源
                else:
                    return 1


if __name__ == "__main__":
    keywords_list = read_first_column("复愈性环境0917.xlsx")
    Path('.').
    pixabay_crawl_list(keywords_list)
