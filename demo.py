from DrissionPage import WebPage
page=WebPage()
fileurl="https://images.unsplash.com/photo-1519810755548-39cd217da494?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxzZWFyY2h8NDV8fE5pZ2h0JTIwc2t5fGVufDB8fDB8fHww&w=1000&q=80"
page.download(
    file_url=fileurl,
    file_exists="overwrite",
    show_msg=True,
)