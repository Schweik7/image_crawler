import cv2
import numpy as np
import matplotlib.pyplot as plt
from icecream import ic
import os
from typing import Optional
from sqlmodel import Field, SQLModel, Session, create_engine, select
from addict import Dict
import json

ic(cv2.__version__)
ic.disable()
os.chdir(os.path.dirname(__file__))

# image_info = {
#     "2classes": {"rgb":...,"hsv": [[1, 2, 3], [4, 5, 6]], "propotion": [0.4, 0.6]},
#     "3classes": {"rgb":...,"hsv": [[1, 2, 3], [4, 5, 6], [7,8,9]], "propotion": [0.2, 0.3,0.5]},
#     ...
#     ...
# }


class ImageInfo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    image_path: str  # 图片路径和名称字段
    image_info: str  # 如前面注释,分类后的字符串


def classify(blur_val, filename):
    image_info = Dict()  # 方便json式的读取写入值的字典模块
    img0 = cv2.imread(filename)
    images.append(cv2.cvtColor(img0, cv2.COLOR_BGR2RGB))
    img = cv2.blur(img0, blur_val)
    images.append(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    ic(img.shape)
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
        centers = np.uint8(centers)  # centers是一个包含分类后bgr像素的值,只有n个,shape为n,3
        centers_img_like = np.array([centers])  # shape需要是1,n,3才能cvtColor
        hsv = cv2.cvtColor(centers_img_like, cv2.COLOR_BGR2HSV)
        unique, counts = np.unique(labels, return_counts=True, axis=0)
        propotion = [round(i / counts.sum(), 4) for i in counts]
        image_info[f"{i}classes"]["rgb"] = centers.tolist()
        image_info[f"{i}classes"]["hsv"] = hsv.tolist()
        image_info[f"{i}classes"]["propotion"] = propotion
    image_infoes.append(
        ImageInfo(image_path=filename, image_info=json.dumps(image_info))
    )


engine = create_engine("sqlite:///image_info.db", echo=False)
SQLModel.metadata.create_all(engine)

MAX_CLASS = 4  # 阿蒙在这里修改最大的分类数，将会从二分类到你指定的数目都分类一遍，现在是2到4
assert MAX_CLASS > 1
images = []
image_infoes = []

blur_val = (50, 50)  # 模糊距离
image_dir = r"E:\spider"
with Session(engine) as session:
    for root, dirs, files in os.walk(image_dir, topdown=False):
        for _ in files:
            file = os.path.join(root, _)
            if file.endswith(".jpg"):
                statement = select(ImageInfo).where(ImageInfo.image_path == file)
                if not session.exec(statement).first():
                    classify(blur_val=blur_val, filename=file)
    session.bulk_save_objects(image_infoes)
    session.commit()
