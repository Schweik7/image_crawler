from utils import logger, read_first_column, cache_progress, rate_limit, Image, d, count_files_in_subdirs

from DownloadKit import DownloadKit
from loguru import logger
from unsplash.api import Api
from unsplash.auth import Auth
from pathlib import Path

d = DownloadKit()
# import requests


PROGRESS_FILE = "progress_cache.json"
MAX_CRAWL_CNT = 1000
cnt = 0
client_id = "thVc9EKQoTPwEosXS-pwE09StgC_a6lDyh5E6xMgeJU"
client_secret = "p7-P3Gg0682dRat9cHE2B3u5IiF8u9G61NeVRHwCbLE"
redirect_uri = "urn:ietf:wg:oauth:2.0:oob"
code = ""
scope = ["public"]

auth = Auth(client_id, client_secret, redirect_uri, scope=scope)
api = Api(auth)


def loop_download(element, res):
    global cnt
    for i in range(res["total_pages"]):  # 这里一般是有334页，30*334==10000
        # for i in range(3):
        photos = api.search.photos(element, per_page=30, page=i)["results"]
        for photo in photos:
            photo.title = Path(
                f"photo by {photo.user.name} on Unsplash,\
                    {photo.alt_description},{photo.id}"
            ).stem
            cnt += 1
            if cnt <= 1200:
                d.add(
                    file_url=photo.urls.regular,
                    goal_path=f"images/{element}",
                    rename=photo.title + ".avif",
                    file_exists="skip",
                )
                logger.debug(f"[+] 开始下载图片{photo.alt_description}")
            else:
                return -1


@cache_progress  # 将记录下当前列表中成功的参数；每次启动时读取成功参数
def unsplash_crawl_list(element):

    # crawler.unsplash_crawl(keywords=element, image_cnt=1000)
    res = api.search.photos(element, per_page=10)  # 一般默认会返回10000张
    logger.info(f"[+] {element} 有 {res['total']} 张可供下载")
    if loop_download(element, res) == -1:
        d.wait()
        logger.info("[√] 下载完毕约1000张图片")


if __name__ == "__main__":
    keywords_list = read_first_column("复愈性环境0917.xlsx")
    unsplash_crawl_list(keywords_list)
# When retrieving a list of objects, an abbreviated or summary version of that object is returned
# - i.e., a subset of its attributes. To get a full detailed version of that object, fetch it individually.

# Authorization: Client-ID YOUR_ACCESS_KEY
# or in url ?client_id=YOUR_ACCESS_KEY
# host="https://api.unsplash.com/"
# header={
#     "Accept-Version" = "v1"
# }
