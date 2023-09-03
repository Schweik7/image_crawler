from datetime import datetime
from DrissionPage import WebPage
from DrissionPage.chromium_element import ChromiumElement
from DrissionPage.session_element import SessionElement
from DrissionPage.easy_set import configs_to_here, set_paths
from DrissionPage.errors import ElementNotFoundError
from DataRecorder import Recorder, DBRecorder
from loguru import logger
from dataclasses import dataclass, asdict
import sys
from time import sleep
from typing import Literal

# Flickr
# Unsplash
# Pixabay
# Pexels
# Pinterest
pexels_url = "https://www.pexels.com/search/{}"
pexels_url_2 = "https://www.pexels.com/zh-cn/search/{}"
pexels_img = "https://images.pexels.com/photos/1120049/pexels-photo-1120049.jpeg?auto=compress&cs=tinysrgb&dpr=1&w=500"

unsplash_url = "https://unsplash.com/s/photos/{}"
unsplash_img = "https://images.unsplash.com/photo-1548247416-ec66f4900b2e?ixid=MnwxMjA3fDB8MHxzZWFyY2h8NHx8Y2F0fGVufDB8fDB8fA%3D%3D&ixlib=rb-1.2.1&auto=format&fit=crop&w=600&q=60"

pixabay_url = "https://pixabay.com/images/search/{}"
pixabay_img = "https://cdn.pixabay.com/photo/2017/08/07/18/57/dog-2606759__340.jpg"

proxies = {
    "http": "http://127.0.0.1:10809",
    "https": "http://127.0.0.1:10809",
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
            self.recorder = Recorder("imager_src_info.csv", cache_size=10)
            self.recorder._encoding = "utf-8-sig"
        else:
            self.recorder = DBRecorder(
                "images.db", cache_size=10, table="images_src_info"
            )  # noqa: E501
        self.website = website
        self.to_jpg = to_jpg

    def mkdir(self, keyword):
        self.keyword = keyword
        picpath = f"./images/{keyword}"
        if not os.path.exists(picpath):
            os.makedirs(picpath)

    def unsplash_crawl(self, keywords: str = "cat", image_cnt: int = 200) -> bool:
        self.cur_image_cnt = 0
        self.page.get(unsplash_url.format(keywords))
        logger.info(f"[+] 开始搜索以{keywords}为关键词的图片")
        if button := self.page("Load more", timeout=5):
            button.click(by_js=True)  # 先按load more
            sleep(2.5)
            self.page.scroll.down(100)
            sleep(0.2)
            self.page.scroll.up(100)
            sleep(0.2)
            logger.info("[√] 点击了load more按钮")
        while self.cur_image_cnt < image_cnt:
            self.page.scroll.down(800)
            sleep(0.2)
            self.page.scroll.up(200)
            sleep(0.2)
            # figure[itemprop=image] 可获取所有的包括tag的图片信息元素组
            # img[data-test=photo-grid-masonry-img]可获取图片元素
            if len(self.page.s_eles("css:figure[itemprop=image]")) > image_cnt:
                for fig_ele in self.page.eles("css:figure[itemprop=image]"):
                    image = Image()
                    image.key_words = keywords
                    img_ele: ChromiumElement = fig_ele.ele(
                        "css:img[data-test=photo-grid-masonry-img]"
                    )
                    image.title = img_ele.attr("alt")
                    image.tag = fig_ele.child().child(index=2).raw_text.replace("\n", ";")
                    filename = f'images/{keywords}/{keywords}_{self.cur_image_cnt}_{datetime.now().strftime("%Y%m%d-%H%M")}'
                    if not self.to_jpg:
                        image.location = filename + ".avif"
                    else:
                        image.location = filename + ".jpg"
                    # image.link=img_ele.prop("currentSrc")#会返回一个plus.unsplash.com
                    image.link=fig_ele("css:a[itemprop=contentUrl]").link
                    # save方法中Path(path).mkdir(parents=True, exist_ok=True)
                    if not img_ele.prop('currentSrc'):
                        logger.warning(image.title,image.link)
                        continue
                    img_ele.save( # save函数主要是通过currentSrc存储的
                        path=os.path.dirname(image.location),
                        rename=os.path.basename(image.location),
                    )
                    logger.debug(image)
                    self.recorder.add_data(asdict(image))
                    self.cur_image_cnt += 1
                self.recorder.record()


if __name__ == "__main__":
    import os

    os.chdir(os.path.dirname(__file__))

    crawler = Image_crawler()
    crawler.unsplash_crawl(keywords="Night sky", image_cnt=30)
