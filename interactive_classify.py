import cv2
import numpy as np
import matplotlib.pyplot as plt
from icecream import ic
import os
from typing import Optional
from sqlalchemy import engine
from sqlmodel import Field, SQLModel, Session, create_engine, select
from matplotlib.widgets import Button
import PySimpleGUI as sg
from addict import Dict
from dotenv import load_dotenv
import json


class BestKmeansClasses(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    image_path: str
    classes: str
    blur_val: str = "[50,50]"


ic(cv2.__version__)
os.chdir(os.path.dirname(__file__))
engine = create_engine("sqlite:///image_info.db", echo=False)
SQLModel.metadata.create_all(engine)  # 必须要放到申明的sqlmodel后面才能生成表
session = Session(engine)
load_dotenv(dotenv_path="./.env", verbose=True, override=True)
IN_AMENG_PC = os.getenv("IN_AMENG_PC")=="True"
path = ".\\image" if not IN_AMENG_PC else "E:\\spider"

def image_generator(img_root=path):  # 使用生成器来每次选择图片
    for root, dirs, files in os.walk(img_root, topdown=False):
        for _ in files:
            file = os.path.join(root, _)
            if file.endswith(".jpg"):
                statement = select(BestKmeansClasses).where(
                    BestKmeansClasses.image_path == file
                )
                if not session.exec(statement).first():
                    yield file


class GUI:
    def __init__(self) -> None:
        self.ig = image_generator()
        self.default_blur_val = [50, 50]
        self.filename = None
        self.cur_blur_val = [50, 50]
        # self.image_info=Dict()
        self.tooltip=Dict()

    def prev(self, event):
        pass

    def next_demo(self):
        """next demo用于产生示例的图片"""
        try:
            filename = next(self.ig)
        except StopIteration:
            ic("[+] all images have been processed.Exit.")
            exit(0)
        img0 = cv2.imread(filename)
        for i in range(MAX_CLASS + 1):
            plt_images[i] = cv2.imencode(".png", img0)[1].tobytes()  #

    def get_next_file(self):
        try:
            self.filename = next(self.ig)
        except StopIteration:
            ic("[+] all images have been processed.Exit.")
            exit(0)

    def next(self, next_file=True, blur_val=[50, 50]):
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
            # self.image_info[f"{i}classes"]["rgb"] = centers.tolist()
            # self.image_info[f"{i}classes"]["hsv"] = hsv.tolist()
            # self.image_info[f"{i}classes"]["propotion"] = propotion
            self.tooltip[f"{i}classes"]=f'''{i} classes
            rgb:{centers.tolist()}
            hsv:{hsv.tolist()}
            propotion:{propotion}
            '''
            res = centers[labels.flatten()]
            dst = res.reshape((img.shape))
            plt_images[i] = cv2.imencode(".png", dst)[1].tobytes()  # 后面几张都是不同分类的图像


def flash(blur_val=[50, 50], next_file=True):
    window["-blur_val-"].update(value=blur_val[0])
    gui.next(next_file=next_file, blur_val=blur_val)
    for index, img in enumerate(plt_images):
        window[f"-IMAGE_{index}-"].update(data=img)
        window[f"-IMAGE_{index}-"].set_tooltip(gui.tooltip.get(f"{index}classes",None))

MAX_CLASS = 5
assert MAX_CLASS > 1
plt_images = [0 for i in range(MAX_CLASS + 1)]
blur_val = [50, 50]
gui = GUI()
gui.next()

if MAX_CLASS <= 3:
    img_col_1 = [
        sg.Image(data=img, k=f"-IMAGE_{index}-", enable_events=True,tooltip=gui.tooltip.get(f"{index}classes",None))
        for index, img in enumerate(plt_images)
    ]
    img_col_2 = None
else:
    img_col_1 = [
        sg.Image(data=img, k=f"-IMAGE_{index}-", enable_events=True,tooltip=gui.tooltip.get(f"{index}classes",None))
        for index, img in enumerate(plt_images[:3])
    ]
    img_col_2 = [
        sg.Image(data=img, k=f"-IMAGE_{index+3}-", enable_events=True,tooltip=gui.tooltip.get(f"{index+3}classes",None))
        for index, img in enumerate(plt_images[3:])
    ]

layout = [
    [
        sg.Button("Skip", size=(4, 2)),
        # sg.Button("Prev", size=(4, 2)),
        sg.Button("Hard_to_classify", size=(16, 2)),
        sg.Text("当前模糊距离："),
        sg.Input(default_text="50", size=(10, 1), k="-blur_val-"),
    ],
    img_col_1,
    img_col_2 if img_col_2 else [sg.T("have a nice day!")],
    [sg.Exit()],
]
window = sg.Window("interactive_classify", layout, finalize=True,grab_anywhere_using_control=True)
window["-blur_val-"].bind("<Return>", "_Enter")  # 使输入能响应enter键


while True:
    event, values = window.read(timeout=200)  # Poll every 100 ms
    if not event == "__TIMEOUT__":
        ic(event, values)
    if event == "Exit" or event == sg.WIN_CLOSED:
        break
    elif event == "Hard_to_classify":  # hard to classify将标记classes为-1
        image_classes_info = BestKmeansClasses(
            image_path=gui.filename,
            classes=-1,
            blur_val=f'[{values["-blur_val-"]},{values["-blur_val-"]}]',
        )
        session.add(image_classes_info)
        session.commit()
        flash(blur_val=[int(values["-blur_val-"]), int(values["-blur_val-"])])
    elif event == "Skip":
        flash()
    elif event.startswith("-IMAGE_"): # 选择分类
        image_classes_info = BestKmeansClasses(
            image_path=gui.filename,
            classes=event[7],
            blur_val=f'[{values["-blur_val-"]},{values["-blur_val-"]}]',
        )
        session.add(image_classes_info)
        session.commit()
        flash(blur_val = [int(values["-blur_val-"]), int(values["-blur_val-"])])
    elif event == "-blur_val-_Enter": # 调整模糊距离
        blur_val = [int(values["-blur_val-"]), int(values["-blur_val-"])]  # str to list
        flash(blur_val, next_file=False)

session.close()
window.close()
 
