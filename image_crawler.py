from icecream import ic

# from playwright.sync_api import sync_playwright, Response
from DrissionPage import WebPage
from datetime import datetime

# Flickr
# Unsplash
# Pixabay
# Pexels
# Pinterest
pexels_url = "https://www.pexels.com/search/{}"
pexels_url_2 = "https://www.pexels.com/zh-cn/search/{}"
pexels_img = "https://images.pexels.com/photos/1120049/pexels-photo-1120049.jpeg?auto=compress&cs=tinysrgb&dpr=1&w=500"

google_url = "https://www.google.com.hk/search?q={}&tbm=isch"

unsplash_url = "https://unsplash.com/s/photos/{}"
unsplash_img = "https://images.unsplash.com/photo-1548247416-ec66f4900b2e?ixid=MnwxMjA3fDB8MHxzZWFyY2h8NHx8Y2F0fGVufDB8fDB8fA%3D%3D&ixlib=rb-1.2.1&auto=format&fit=crop&w=600&q=60"

pixabay_url = "https://pixabay.com/images/search/{}"
pixabay_img = "https://cdn.pixabay.com/photo/2017/08/07/18/57/dog-2606759__340.jpg"

freenaturestock_url = "https://freenaturestock.com/?s={}"
freenaturestock_img = (
    "https://freenaturestock.com/wp-content/uploads/freenaturestock-1770-768x426.jpg"
)

httpbin_get_url = "http://httpbin.org/get"

fake_headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",  # noqa
    "Accept-Charset": "UTF-8,*;q=0.5",
    "Accept-Encoding": "gzip,deflate,sdch",
    "Accept-Language": "en-US,en;q=0.8",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.74 Safari/537.36 Edg/79.0.309.43",  # noqa
}
proxies = {
    "http": "http://127.0.0.1:25378",
    "https": "http://127.0.0.1:25378",
}


class Image_crawler:
    def __init__(self, website="unsplash", brower="chrome"):
        self.website = website
        self.brower = brower
        self.img_count = 0
        self.auto_scroll_js = """
        ()=>{
            function start_scroll(){
                down1_scroll=setInterval(()=>window.scrollBy(0,300),1000);
                up1_scroll=setInterval(()=>window.scrollBy(0,-150),3000);
                down2_scroll=setInterval(()=>window.scrollBy(0,500),5000);
                up2_scroll=setInterval(()=>window.scrollBy(0,-300),4000);
            }
            setTimeout(start_scroll,1000);
        }
        """

    def mkdir(self, keyword):
        self.keyword = keyword
        picpath = f"./image/{keyword}"
        if not os.path.exists(picpath):
            os.makedirs(picpath)

    def download(self, res, suffix):
        self.img_count += 1
        with open(
            f'./image/{self.keyword}/{self.keyword}_{self.img_count}_{datetime.now().strftime("%Y%m%d%H%M%S")}.{suffix}',
            "wb",
        ) as f:
            f.write(res.body())

    def unsplash_crawl(self, keyword="cat"):
        # 之前是使用playwright编写的，但是那个太重型了。现在喜欢DrissionPage了
        # def onresponse(res: Response):
        #     ic(res.url)
        #     if (
        #         res.url.startswith("https://images.unsplash.com/photo-")
        #         and "ixid" in res.url
        #     ):
        #         ic("!!!!!!!!!!!", res.url)
        #         self.download(res, suffix="avif")

        # self.mkdir(keyword)

        # with sync_playwright() as p:  # in REPL,use p=sync_playwright().start()
        #     if self.brower == "chrome":
        #         browser = p.chromium.launch(headless=False, slow_mo=100, devtools=True)
        #     page = browser.new_page()
        #     page.on("response", onresponse)
        #     page.goto(unsplash_url.format(keyword), timeout=0)
        #     page.evaluate(self.auto_scroll_js)  # 注释，这里是自动滚屏
        #     page.wait_for_timeout(1000 * 1000)


if __name__ == "__main__":
    import requests
    import os

    os.chdir(os.path.dirname(__file__))
    crawler = Image_crawler()
    crawler.unsplash_crawl("Night sky")
