from typing import Optional
import PySimpleGUI as sg
import cv2
from dotenv import load_dotenv
from icecream import ic
import os
from matplotlib import pyplot as plt
from sqlalchemy import engine
from sqlmodel import Field, SQLModel, Session, create_engine, select
import json
import numpy as np
from addict import Dict


class ImageMark(SQLModel, table=True):
    image_path: str = Field(default=None, index=True, primary_key=True)  # 图片名称，设为索引方便查询
    is_proper_size: Optional[int]  # 0是原始尺寸，-1代表难以抉择，1是新尺寸
    best_size: Optional[str]
    classes: Optional[int] # 0是默认值，-1代表难以抉择，其他则是最好的分类尺寸
    blur_val: Optional[str]


def image_generator(img_root, table=ImageMark, my_filter=None):  # 使用生成器来每次选择图片
    for root, dirs, files in os.walk(img_root, topdown=False):
        if IN_AMENG_PC:
            files = filter(
                lambda f: f.endswith(".jpg") and "_origin" in f, files
            )
        else:
            files = filter(lambda f: os.path.splitext(f)[1] in image_exts, files)
        for _ in files:
            file = os.path.join(root, _)
            statement = select(table).where(table.image_path == file)
            if not session.exec(statement).first():
                yield file


ic(cv2.__version__)
os.chdir(os.path.dirname(__file__))
load_dotenv(dotenv_path="./.env", verbose=True, override=True)
IN_AMENG_PC = os.getenv("IN_AMENG_PC").casefold() == "True".casefold()
MAX_CLASS = int(os.getenv("MAX_CLASS"))
ic(MAX_CLASS)
engine = create_engine("sqlite:///image_info.db", echo=False)
SQLModel.metadata.create_all(engine)
session = Session(engine)
image_root_path = ".\\image" if not IN_AMENG_PC else "E:\\spider"
# 从gitignore里找的图片后缀
image_exts = [
    ".jpg",
    ".jpeg",
    ".jpe",
    ".jif",
    ".jfif",
    ".jfi",
    ".jp2",
    ".j2k",
    ".jpf",
    ".jpx",
    ".jpm",
    ".mj2",
    ".jxr",
    ".hdp",
    ".wdp",
    ".gif",
    ".raw",
    ".webp",
    ".png",
    ".apng",
    ".mng",
    ".tiff",
    ".tif",
    ".svg",
    ".svgz",
    ".pdf",
    ".xbm",
    ".bmp",
    ".dib",
    ".ico",
]


class GUI:
    def __init__(self) -> None:
        self.ig = image_generator(img_root=image_root_path)
        self.default_blur_val = [50, 50]
        self.filename = None
        self.cur_blur_val = [50, 50]
        # self.image_info=Dict()
        self.tooltip = Dict()

    def get_next_file(self):
        try:
            self.filename = next(self.ig)
        except StopIteration:
            ic("[+] all images have been processed.Exit.")
            exit(0)

    def resize_next_file(self, only_resize=True, format="png", initial=False):
        """返回resize图片后的数据

        Args:
            only_resize (bool, optional): 是否读取下一张图片。如果不读取，将不会更新self.cur_img及self.filename. Defaults to True.
            format (str, optional): 目前由于pysimplegui只支持png，因此只有png可以选. Defaults to "png".

        Returns:
            bytes数组: 右侧resize后图片的数据
        """
        if not only_resize:
            self.get_next_file()
            self.cur_img = cv2.imread(self.filename)
            self.img_left = cv2.imencode(".png", self.cur_img)[1].tobytes()
            height, width, _ = self.cur_img.shape
            ic(height, width)
            if height < 500:
                self.sz_height, self.sz_width = int(height * 1.5), int(width * 1.5)
            else:
                self.sz_height, self.sz_width = height, width

        if not initial:
            window["Resize_width_slider"].update(self.sz_width)
            window["Resize_width_spin"].update(self.sz_width)
            window["Resize_height_slider"].update(self.sz_height)
            window["Resize_height_spin"].update(self.sz_height)
            window["Origin_width"].update(f"Origin_width:{self.origin_size[1]}")
            window["Origin_height"].update(f"Origin_height:{self.origin_size[0]}")
            window["Filename"].update(f"File:{self.filename}")
            image_mark.best_size=json.dumps(f"{self.sz_height},{self.sz_width}")
        # dsize参数竟然是width在前，height在后
        img_2 = cv2.resize(
            self.cur_img,
            dsize=(self.sz_width, self.sz_height),
            interpolation=cv2.INTER_LINEAR,
        )
        if format == "png":
            img_right = cv2.imencode(".png", img_2)[1].tobytes()
            return img_right
        elif format == "jpg":
            return img_2

    def classify_next_file(self, next_file=True, blur_val=[50, 50]):
        """生成给定模糊距离下的图片数组"""
        if next_file:
            self.get_next_file()
        self.cur_blur_val = blur_val
        img0 = cv2.resize(cv2.imread(self.filename), None, fx=0.5, fy=0.5)
        plt_images[0] = cv2.imencode(".png", img0)[1].tobytes()  # 第一张图是原图
        img = cv2.blur(img0, blur_val)
        plt_images[1] = cv2.imencode(".png", img)[1].tobytes()  # 第二张是模糊后图像
        data = img.reshape((-1, 3))  # flatten 为一维图像
        data = np.float32(data)
        criteria = (
            cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
            10,
            1.0,
        )  # 定义中心 (type,max_iter,epsilon)
        flags = cv2.KMEANS_RANDOM_CENTERS  # 设置标签
        for i in range(2, MAX_CLASS + 1):
            compactness, labels, centers = cv2.kmeans(
                data, i, None, criteria, 10, flags
            )  # labels是每个像素的分类：0,1,2...的
            # 图像转换回uint8二维类型
            centers = np.uint8(centers)  # centers是一个包含分类后bgr像素的值,只有n个
            centers_img_like = np.array([centers])  # shape需要是1,n,3才能cvtColor
            hsv = cv2.cvtColor(centers_img_like, cv2.COLOR_BGR2HSV)
            unique, counts = np.unique(labels, return_counts=True, axis=0)
            propotion = [round(i / counts.sum(), 4) for i in counts]
            self.tooltip[
                f"{i}classes"
            ] = f"""{i} classes
            rgb:{centers.tolist()}
            hsv:{hsv.tolist()}
            propotion:{propotion}
            """
            res = centers[labels.flatten()]
            dst = res.reshape((img.shape))
            plt_images[i] = cv2.imencode(".png", dst)[1].tobytes()  # 后面几张都是不同分类的图像


def make_window(theme):
    sg.theme(theme)
    menu_def = [
        ["&Application", ["&Open Folder", "---", "&Exit"]],
        ["&Help", ["How To &Use", "---", "&About"]],
    ]
    # right_click_menu_def = [[], ["Nothing", "More Nothing", "Exit"]]
    right_click_menu_def = None
    resize_layout = [
        [sg.Menu(menu_def, key="Menu")],
        [
            sg.Button("Hard_to_resize"),
            sg.Text(
                f"Origin_width:{gui.origin_size[1]}",
                key="Origin_width",
                text_color="yellow",
            ),
            sg.Text(
                f"Origin_height:{gui.origin_size[0]}",
                key="Origin_height",
                text_color="yellow",
            ),
            sg.Text("Resize_width"),
            sg.Spin(
                [sz for sz in range(300, 1000)],
                font=("Helvetica 20"),
                initial_value=gui.sz_width,
                change_submits=True,
                key="Resize_width_spin",
            ),
            sg.Text("Resize_height"),
            sg.Spin(
                [sz for sz in range(300, 1000)],
                font=("Helvetica 20"),
                initial_value=gui.sz_height,
                change_submits=True,
                key="Resize_height_spin",
            ),
            sg.Slider(
                range=(300, 1000),
                orientation="h",
                size=(10, 20),
                change_submits=True,
                key="Resize_width_slider",
                font=("Helvetica 20"),
                default_value=gui.sz_width,
            ),
            sg.Button("Back_to_origin_size"),
        ],
        [
            sg.Image(data=img_left, k=f"Image_left", enable_events=True),
            sg.Image(data=img_right, k=f"Image_right", enable_events=True),
            sg.Slider(
                range=(300, 1000),
                orientation="v",
                size=(10, 20),
                change_submits=True,
                key="Resize_height_slider",
                font=("Helvetica 20"),
                default_value=gui.sz_height,
            ),
        ],
    ]
    if MAX_CLASS <= 3:
        img_col_1 = [
            sg.Image(
                data=img,
                k=f"-IMAGE_{index}-",
                enable_events=True,
                tooltip=gui.tooltip.get(f"{index}classes", None),
            )
            for index, img in enumerate(plt_images)
        ]
        img_col_2 = None
    else:
        img_col_1 = [
            sg.Image(
                data=img,
                k=f"-IMAGE_{index}-",
                enable_events=True,
                tooltip=gui.tooltip.get(f"{index}classes", None),
            )
            for index, img in enumerate(plt_images[:3])
        ]
        img_col_2 = [
            sg.Image(
                data=img,
                k=f"-IMAGE_{index+3}-",
                enable_events=True,
                tooltip=gui.tooltip.get(f"{index+3}classes", None),
            )
            for index, img in enumerate(plt_images[3:])
        ]
    classify_layout = [
        [
            sg.Text("当前模糊距离："),
            sg.Input(default_text="50", size=(10, 1), k="-blur_val-"),
        ],
        img_col_1,
        # img_col_2 if img_col_2 else [sg.T("have a nice day!")],
        img_col_2 or [sg.T("have a nice day!")],
    ]
    headings = ["Classes", "RGB", "HSV", "Propotion"]
    data = []
    image_info_layout = (
        [
            sg.Table(
                values=data,
                headings=headings,
                max_col_width=25,
                background_color="black",
                auto_size_columns=True,
                display_row_numbers=True,
                justification="right",
                num_rows=2,
                alternating_row_color="black",
                key="Table",
                row_height=25,
            )
        ],
    )
    layout = [
        [
            sg.Text(
                "Meng's Image Tool",
                size=(38, 1),
                justification="center",
                font=("Helvetica", 16),
                relief=sg.RELIEF_RIDGE,
                k="Heading",
                enable_events=True,
            ),
            sg.Text(
                text=f"File:{gui.filename}", key="Filename", text_color="yellow"
            ),  # 图片路径
            sg.Button("Skip", size=(4, 2)),
            sg.Button("Hard_to_classify", size=(16, 2)),
            sg.Button("Select", size=(8, 2)),  # 确认选中
            sg.Exit(),
        ]
    ]
    layout += [
        [
            sg.TabGroup(
                [
                    [
                        sg.Tab("Resize Image", resize_layout),
                        sg.Tab("Classify Image", classify_layout),
                        # sg.Tab("Image Info", image_info_layout),
                    ]
                ],
                key="TAB GROUP",
            )
        ]
    ]

    return sg.Window(
        "Meng's Image Tool",
        layout,
        finalize=True,
        right_click_menu=right_click_menu_def,
        grab_anywhere_using_control=True,
    )


def update(update_resize=False, update_classify=False, next_file=False, **kwargs):
    blur_val = kwargs.get("blur_val", [50, 50])
    if next_file:
        image_mark.image_path=None
        image_mark.is_proper_size=None
        image_mark.best_size=None
        image_mark.classes=None
        image_mark.blur_val=None
        img_right = gui.resize_next_file(only_resize=False)
        window["Image_left"].update(data=gui.img_left)
        window["Image_right"].update(data=img_right)
        gui.classify_next_file(next_file=False, blur_val=blur_val)
        window["-blur_val-"].update(value=blur_val[0])
        for index, img in enumerate(plt_images):
            window[f"-IMAGE_{index}-"].update(data=img)
            window[f"-IMAGE_{index}-"].set_tooltip(
                gui.tooltip.get(f"{index}classes", None)
            )
    if update_classify:
        gui.classify_next_file(next_file=False, blur_val=blur_val)
        window["-blur_val-"].update(value=blur_val[0])
        for index, img in enumerate(plt_images):
            window[f"-IMAGE_{index}-"].update(data=img)
            window[f"-IMAGE_{index}-"].set_tooltip(
                gui.tooltip.get(f"{index}classes", None)
            )
    if update_resize:
        img_right = gui.resize_next_file(only_resize=True)
        window["Image_right"].update(data=img_right)


gui = GUI()
img_right = gui.resize_next_file(only_resize=False, initial=True)
img_left = gui.img_left
plt_images = [0 for i in range(MAX_CLASS + 1)]
gui.classify_next_file(next_file=False)
blur_val = [50, 50]

window = make_window(sg.theme())
window["-blur_val-"].bind("<Return>", "_Enter")  # 使输入能响应enter键
image_mark=ImageMark()
while True:
    event, values = window.read(timeout=200)
    # if not event == "__TIMEOUT__":
    #     ic(event, values)
    if event == "Exit" or event == sg.WIN_CLOSED:
        break
    elif (
        event == "Hard_to_classify"
    ):  
        image_mark.image_path=gui.filename
        image_mark.classes=-1
        image_mark.blur_val=f'[{values["-blur_val-"]},{values["-blur_val-"]}]'
        session.merge(image_mark)
        session.commit()
        update(next_file=True)
    elif event == "Skip":
        update(next_file=True)
    elif event.startswith("-IMAGE_"):  # 选择分类，此时尚不需要提交至数据库
        image_mark.image_path=gui.filename
        image_mark.classes=event[7] if int(event[7]) >= 2 else 0
        image_mark.blur_val = f'[{values["-blur_val-"]},{values["-blur_val-"]}]'
        session.merge(image_mark)
        session.commit()
        update(update_classify=True, blur_val=blur_val)
        # TODO 点击图片分类加一个底框
    elif event == "-blur_val-_Enter":  # 调整模糊距离
        blur_val = [int(values["-blur_val-"]), int(values["-blur_val-"])]  # str to list
        update(update_classify=True, blur_val=blur_val)
    elif event == "Hard_to_resize":  # hard to classify将标记classes为-1，直接提交到数据库
        image_mark.image_path=gui.filename
        image_mark.is_proper_size=-1
        session.merge(image_mark)
        session.commit()
        update(next_file=True)
    elif event == "Select":  # 直接提交到数据库
        image_mark.image_path=gui.filename
        image_mark.is_proper_size=is_proper_size=1 if gui.sz_height != gui.cur_img.shape[0] or gui.sz_width!=gui.cur_img.shape[1] else 0
        image_mark.best_size=json.dumps(f"{gui.sz_height},{gui.sz_width}")
        session.merge(image_mark)
        session.commit()
        update(next_file=True)
    elif event.startswith("Resize_"):  # 同步spin与slider的值
        if event == "Resize_width_slider":
            gui.sz_width = int(float(values["Resize_width_slider"]))
            window["Resize_width_spin"].update(gui.sz_width)
        elif event == "Resize_height_slider":
            gui.sz_height = int(float(values["Resize_height_slider"]))
            window["Resize_height_spin"].update(gui.sz_height)
        elif event == "Resize_width_spin":
            gui.sz_width = int(float(values["Resize_width_spin"]))
            window["Resize_width_slider"].update(gui.sz_width)
        elif event == "Resize_height_spin":
            gui.sz_height = int(float(values["Resize_height_spin"]))
            window["Resize_height_slider"].update(gui.sz_height)
        update(update_resize=True)
    elif event == "About":
        window.disappear()
        sg.popup("Image tool program, created for Meng.")
        window.reappear()
    elif event == "Open Folder":
        folder_or_file = sg.popup_get_folder(
            "Choose your root folder where images located"
        )
        gui.ig = image_generator(img_root=folder_or_file)  # 不知道单选一个图片会怎么样……
    elif event == "Back_to_origin_size":
        height, width, _ = gui.cur_img.shape
        gui.sz_width = width
        gui.sz_height = height
        window["Resize_width_spin"].update(gui.sz_width)
        window["Resize_height_spin"].update(gui.sz_height)
        window["Resize_width_slider"].update(gui.sz_width)
        window["Resize_height_slider"].update(gui.sz_height)
        update(update_resize=True)