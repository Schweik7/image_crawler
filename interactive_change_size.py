import cv2
from dotenv import load_dotenv
from icecream import ic
import os
from typing import Optional
from sqlalchemy import engine
from sqlmodel import Field, SQLModel, Session, create_engine, select
import PySimpleGUI as sg
import json
# from tqdm import tqdm


class ImageMark(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    image_path: str = Field(default=None, index=True)  # 图片路径和名称字段，设为索引方便查询
    is_proper_size: int = Field(
        default=0, index=False
    )  # 0是默认值，-1代表难以抉择，1代表原图已经是合适的图片了，2代表有新的合适的尺寸
    best_size: str = Field(default=None, index=True)


ic(cv2.__version__)
# ic.disable()
os.chdir(os.path.dirname(__file__))
load_dotenv(dotenv_path="./.env", verbose=True, override=True)
IN_AMENG_PC = os.getenv("IN_AMENG_PC").casefold()=="True".casefold()
ic(IN_AMENG_PC)
engine = create_engine("sqlite:///image_info.db", echo=False)
SQLModel.metadata.create_all(engine)  # 必须要放到申明的sqlmodel后面才能生成表
session = Session(engine)
path = ".\\image" if not IN_AMENG_PC else "E:\\spider"
ic(path)

def image_generator(img_root, table=ImageMark):  # 使用生成器来每次选择图片
    for root, dirs, files in os.walk(img_root, topdown=False):
        if IN_AMENG_PC:
            files = filter(lambda f: f.endswith(".jpg") and "_origin" in f, files)
        else:
            files = filter(lambda f: f.endswith(".jpg"), files)
        for _ in files:
            file = os.path.join(root, _)
            statement = select(table).where(table.image_path == file)
            if not session.exec(statement).first():
                # ic(file)
                yield file


class GUI:
    def __init__(self) -> None:
        self.ig = image_generator(img_root=path)
        self.filename = None
        self.cur_img = None
        self.sz_width=None
        self.sz_height=None
        self.origin_size=None

    def get_next_file(self):
        try:
            self.filename = next(self.ig)
        except StopIteration:
            ic("[+] All images have been processed.Exit.")
            exit(0)

    def next(self, only_resize=True, format="png",initial=False):
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
            *self.origin_size,_=self.cur_img.shape
            ic(height,width)
            if height < 500:
                self.sz_height,self.sz_width = int(height * 1.5), int(width * 1.5)
            else:
                self.sz_height,self.sz_width = height, width

        if not initial:
            window["Resize_width_slider"].update(self.sz_width)
            window["Resize_width_spin"].update(self.sz_width)
            window["Resize_height_slider"].update(self.sz_height)
            window["Resize_height_spin"].update(self.sz_height)
            window["origin_width"].update(f"Origin_width:{self.origin_size[1]}")
            window["origin_height"].update(f"Origin_height:{self.origin_size[0]}")
            window["filename"].update(f"file:{self.filename}")
        # 是否沙雕，dsize竟然是width在前，height在后
        img_2 = cv2.resize(
            self.cur_img, dsize=(self.sz_width,self.sz_height), interpolation=cv2.INTER_LINEAR
        )
        if format == "png":
            img_right = cv2.imencode(".png", img_2)[1].tobytes()
            return img_right
        elif format == "jpg":
            return img_2


def update(only_resize=True):
    img_right = gui.next(only_resize=only_resize)
    if not only_resize:
        window["Image_left"].update(data=gui.img_left)
    window["Image_right"].update(data=img_right)


gui = GUI()
img_right = gui.next(only_resize=False,initial=True)
img_left = gui.img_left

layout = [
    [sg.Text(f"file:{gui.filename}",key="filename",text_color="yellow")],
    [
        sg.Button("Select", size=(4, 2)),  # 确认选中
        sg.Button("Skip", size=(4, 2)),
        # sg.Button("Prev", size=(4, 2)),
        sg.Button("Hard_to_resize"),
        sg.Text(f"Origin_width:{gui.origin_size[1]}",key="origin_width",text_color="yellow"),
        sg.Text(f"Origin_height:{gui.origin_size[0]}",key="origin_height",text_color="yellow"),
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
            default_value=gui.sz_width
        ),
        sg.Exit()
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
            default_value=gui.sz_height
        ),
    ]
]
window = sg.Window("Interactive Resize", layout, finalize=False,grab_anywhere_using_control=True)  # finalize为True的话，才能绑定return


while True:
    event, values = window.read(timeout=200)  # Poll every 100 ms
    if event == "__TIMEOUT__":
        continue
    if event == "Exit" or event == sg.WIN_CLOSED:
        break
    elif event == "Hard_to_resize":  # hard to classify将标记classes为-1
        image_mark = ImageMark(
            image_path=gui.filename,
            is_proper_size=-1,
        )
        session.add(image_mark)
        session.commit()
        update(only_resize=False)
    elif event == "Skip":
        update(only_resize=False)
    elif event == "Select":
        image_mark = ImageMark(
            image_path=gui.filename,
            is_proper_size=2,
            best_size=json.dumps(f"{gui.sz_height},{gui.sz_width}"),
        )
        session.add(image_mark)
        session.commit()
        update(only_resize=False)
    elif event.startswith("Resize_"):  # 同步spin与slider的值
        if event=="Resize_width_slider":
            gui.sz_width=int(float(values["Resize_width_slider"]))
            window["Resize_width_spin"].update(gui.sz_width)
        elif event=="Resize_height_slider":
            gui.sz_height=int(float(values["Resize_height_slider"]))
            window["Resize_height_spin"].update(gui.sz_height)
        elif event=="Resize_width_spin":
            gui.sz_width=int(float(values["Resize_width_spin"]))
            window["Resize_width_slider"].update(gui.sz_width)  
        elif event=="Resize_height_spin":
            gui.sz_height=int(float(values["Resize_height_spin"]))
            window["Resize_height_slider"].update(gui.sz_height)            
        update(only_resize=True)


session.close()
window.close()
