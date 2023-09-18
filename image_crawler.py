import os
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from time import sleep
from typing import Literal
import json
from DataRecorder import DBRecorder, Recorder
from loguru import logger
import openpyxl
import playwright
from playwright.sync_api import sync_playwright
from pathlib import Path
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
        user_data_dir=Path('user_data')
        if not user_data_dir.exists() and not user_data_dir.isdir():  # 如果没有用户配置文件夹
            logger.info("[!] 没有发现配置。创建配置……")
            user_data_dir.mkdir()
        self.brower_init()
        self.recorder_init(recoder)  
        self.website = website
        self.to_jpg = to_jpg
        if to_jpg:
            logger.info("[+] 将会将avif格式的图片转换为jpg格式")

    def recorder_init(self, recoder):
        if recoder == "csv":
            self.recorder = Recorder("imager_src_info.csv", cache_size=20)
            self.recorder._encoding = "utf-8-sig"
        else:
            self.recorder = DBRecorder(
                "images.db", cache_size=10, table="images_src_info"
            )

    def brower_init(self):
        p = sync_playwright().start()
        try:
            browser = p.chromium.connect_over_cdp(endpoint_url="http://localhost:9222")
            default_context = browser.contexts[0]
            self.page = default_context.pages[0]
            logger.info("[+] 使用已有的浏览器")
        except playwright._impl._api_types.Error:
            logger.info("[!] 未发现已有的浏览器，启动浏览器")
            # 默认启动时，除非devtools是True，headless是True的
            # 只要不手动运行browser.close()，浏览器就不会关闭
            browser=p.chromium.launch_persistent_context(user_data_dir="./user_data",headless=False,devtools=True,args=["--remote-debugging-port=9222"])
            self.page=browser.new_page()

    def mkdir(self, keyword):
        self.keyword = keyword
        picpath = Path(f"./images/{keyword}")
        picpath.mkdir(exist_ok=True)

    def unsplash_crawl(self, keywords: str = "cat", image_cnt: int = 200) -> bool:
                def onresponse(res: Response):
            ic(res.url)
            if (
                res.url.startswith("https://images.unsplash.com/photo-")
                and "ixid" in res.url
            ):
                ic("!!!!!!!!!!!", res.url)
                self.download(res, suffix="avif")


        self.page_init(keywords,website="unsplash")
        try:
            self.page.click("text=Load more")
            logger.info("[√] 点击了load more按钮")
        except Exception as e:
            logger.warning("[!] Load more按钮没有点击，请自己手动点击一下！")
            # button.click(by_js=True, timeout=2.5)  # 先按load more
        self.page.evaluate("window.scrollTo(0, 0)") # 滚动到top位置
        
        last_processed_index=-1
        fail_cnt=0
        while self.cur_image_cnt < image_cnt and fail_cnt<10: 
            #  and "Make something awesome" not in self.page.html
            self.page.evaluate("window.scrollBy(0, 800)")
            sleep(0.15)
            self.page.evaluate("window.scrollBy(0, -200)")
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
        self.page.goto(website_urls[website].format(keywords)) # 不同网站用不用的搜索网址
        logger.info(f"[+] 开始搜索以{keywords}为关键词的图片")

    def unsplash_image_extract(self, keywords, fig_ele):
        image = Image()
        image.key_words = keywords
        img_ele = fig_ele.ele(
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


crawler = Image_crawler()
@cache_progress # 将记录下当前列表中成功的参数；每次启动时读取成功参数
def unsplash_crawl_list(element):
    crawler.unsplash_crawl(keywords=element, image_cnt=1000)

logger.remove()  # 删除默认的控制台处理器
logger.add(
    sys.stderr,
    level="DEBUG",
)
logger.add("mylog.log", rotation="5 MB", level="INFO")


if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))
    keywords_list=read_first_column('复愈性环境0917.xlsx')
    unsplash_crawl_list(keywords_list)





