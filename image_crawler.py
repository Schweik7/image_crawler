import os
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from time import sleep
from typing import Literal
import json
from DataRecorder import DBRecorder, Recorder
from DrissionPage import WebPage
from DrissionPage.chromium_element import ChromiumElement
from DrissionPage.easy_set import configs_to_here, set_paths
from DrissionPage.errors import ElementNotFoundError
from loguru import logger
import openpyxl
# Flickr
# Pexels
# Pinterest
pexels_url = "https://www.pexels.com/search/{}"
pexels_url_2 = "https://www.pexels.com/zh-cn/search/{}"

website_urls={
    "unsplash":"https://unsplash.com/s/photos/{}",
    "pixabay" : "https://pixabay.com/images/search/{}"
}

proxies = {
    "http": "http://127.0.0.1:10809",
    "https": "http://127.0.0.1:10809",
}

fake_headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",  # noqa
    "Accept-Charset": "UTF-8,*;q=0.5",
    "Accept-Encoding": "gzip,deflate,sdch",
    "Accept-Language": "en-US,en;q=0.8",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.74 Safari/537.36 Edg/79.0.309.43",  # noqa
}


@dataclass
class Image:
    key_words: str | None = None
    title: str | None = None
    # size: (int, int) | None
    location: str | None = None
    link: str | None = None
    tag: str | None = None


class Image_crawler:
    def __init__(
        self,
        website: str = "unsplash",
        console_log_level: str = "INFO",
        file_log_level: str = "DEBUG",
        recoder: Literal["csv", "db"] = "csv",
        to_jpg: bool = False,
    ):
        logger.remove()  # 删除默认的控制台处理器
        logger.add(
            sys.stderr,
            level=console_log_level,
        )
        logger.add("mylog.log", rotation="5 MB", level=file_log_level)

        if not os.path.exists("user_data"):  # 如果没有用户配置文件夹
            logger.info("[!] 没有发现配置。创建配置……")
            configs_to_here()
            set_paths(user_data_path="./user_data")
        self.page = WebPage()
        if recoder == "csv":
            self.recorder = Recorder("imager_src_info.csv", cache_size=20)
            self.recorder._encoding = "utf-8-sig"
        else:
            self.recorder = DBRecorder(
                "images.db", cache_size=10, table="images_src_info"
            )  # noqa: E501
        self.website = website
        self.to_jpg = to_jpg
        if to_jpg:
            logger.info("[+] 将会将avif格式的图片转换为jpg格式")

    def mkdir(self, keyword):
        self.keyword = keyword
        picpath = f"./images/{keyword}"
        if not os.path.exists(picpath):
            os.makedirs(picpath)

    def unsplash_crawl(self, keywords: str = "cat", image_cnt: int = 200) -> bool:
        self.page_init(keywords,website="unsplash")
        if button := self.page("Load more", timeout=3):
            button.click(by_js=True, timeout=2.5)  # 先按load more
            sleep(2.5)
            self.page.scroll.to_top()
            logger.info("[√] 点击了load more按钮")
        else:
            logger.warning("[!] Load more按钮没有点击，请自己手动点击一下！")
        last_processed_index=-1
        fail_cnt=0
        # 在获取了千张左右的图片后，会一直"Make something awesome"并且不刷图片
        # 我们将图片长度不更新的行为定义为fail
        while self.cur_image_cnt < image_cnt and fail_cnt<10: 
            #  and "Make something awesome" not in self.page.html
            self.page.scroll.down(800)
            sleep(0.15)
            self.page.scroll.up(200)
            sleep(0.15)
            # figure[itemprop=image] 可获取所有的包括tag的图片信息元素组
            # img[data-test=photo-grid-masonry-img]可获取图片元素
            image_eles=self.page.eles("css:figure[itemprop=image]")
            if len(image_eles)==last_processed_index+1:
                fail_cnt+=1
                continue
            for fig_ele in image_eles[last_processed_index:]: # 这里应该
                self.unsplash_image_extract(keywords, fig_ele)
            last_processed_index=len(image_eles)-1
            self.recorder.record()
        return True

    def page_init(self, keywords,website="unsplash"):
        self.cur_image_cnt = 0
        self.page.get(website_urls[website].format(keywords)) # 不同网站用不用的搜索网址
        # self.page.download_set.by_browser()
        self.page.download_set.by_DownloadKit()  # 是通过requests进行下载的
        logger.info(f"[+] 开始搜索以{keywords}为关键词的图片")

    def unsplash_image_extract(self, keywords, fig_ele):
        image = Image()
        image.key_words = keywords
        img_ele: ChromiumElement = fig_ele.ele(
                        "css:img[data-test=photo-grid-masonry-img]"
                    )
        image.title = img_ele.attr("alt")
        image.tag = (
                        fig_ele.child().child(index=2).raw_text.replace("\n", ";")
                    )
        filename = (
                        f"images/{keywords}/{keywords}_{self.cur_image_cnt}_"
                        f'{datetime.now().strftime("%Y%m%d-%H%M")}'
                    )
        if not self.to_jpg:
            image.location = filename + ".avif"
        else:
            image.location = filename + ".jpg"
        path = os.path.dirname(image.location)
        rename = os.path.basename(image.location)
                    # image.link=img_ele.prop("currentSrc")#会返回一个plus.unsplash.com
        image.link = fig_ele("css:a[itemprop=contentUrl]").link
                    # save方法中Path(path).mkdir(parents=True, exist_ok=True)
        if not img_ele.prop("currentSrc"):
            logger.info(f"[x] 标题为{image.title}的图片将单独下载")
            self.page.download.add(file_url=img_ele.attr("src"),goal_path=path,
                                   rename=rename,headers=fake_headers,proxies=proxies) 
            # self.page.download(
            #                 file_url=img_ele.attr("src"),
            #                 goal_path=path,
            #                 rename=rename,
            #                 file_exists="overwrite",
            #                 headers=fake_headers,
            #                 proxies=proxies,
            #             )
        else:
                        # save函数主要是通过currentSrc存储的
            img_ele.save(path=path, rename=rename)
        logger.debug(image)
        self.recorder.add_data(asdict(image))
        self.cur_image_cnt += 1


    def pixabay_crawl(self, keywords: str = "cat", image_cnt: int = 200) -> bool:
        self.page_init(keywords=keywords,website="pixabay")
        while self.cur_image_cnt<image_cnt:
            self.page.scroll.down(800)
            sleep(0.2)
            self.page.scroll.up(200)
            sleep(0.2)
            if len(figs:=self.page.eles('css:div[class^="column"] img')) > image_cnt:
                for fig in figs:
                    pass
        def pixabay_image_extract(self, keywords, fig_ele):
            image=Image()
            image.key_words=keywords
            pass

def read_first_column(filename):
    workbook = openpyxl.load_workbook(filename)
    sheet = workbook.active
    column_data = [cell.value for cell in sheet['A'] if cell.value is not None]
    return column_data

PROGRESS_FILE = "progress_cache.json"

def save_progress(data):
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(data, f)

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {}

def cache_progress(func):
    def wrapper(*args, **kwargs):
        data = load_progress()
        list_to_process = args[0]
        starting_index = data.get('last_completed', -1) + 1
        for i in range(starting_index, len(list_to_process)):
            try:
                func(list_to_process[i], **kwargs)
                data['last_completed'] = i
                save_progress(data)
            except Exception as e:
                print(f"Failed on index {i} due to {e}")
                break

    return wrapper


# crawler = Image_crawler()
# @cache_progress # 将记录下当前列表中成功的参数；每次启动时读取成功参数
# def unsplash_crawl_list(element):
#     crawler.unsplash_crawl(keywords=element, image_cnt=1000)

if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))
    from playwright.sync_api import sync_playwright
    u = 'https://www.baidu.com/'
    sy = sync_playwright()
    qd = sy.start()
    browser = qd.chromium.connect_over_cdp(endpoint_url="http://localhost:9222")
    default_context = browser.contexts[0]
    page = default_context.pages[0]
    page.goto(u)
    # qd.stop()
    # keywords_list=read_first_column('复愈性环境0917.xlsx')
    # unsplash_crawl_list(keywords_list)





