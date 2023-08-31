from PIL import Image
import os
from icecream import ic
from tqdm import tqdm
from typing import Optional
from sqlmodel import Field, SQLModel, Session, create_engine, select

os.chdir(os.path.dirname(__file__))

class ImageSize(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    image_path: str= Field(default=None,index=True)  # 图片路径和名称字段，设为索引方便查询
    width: int 
    height: int

engine = create_engine("sqlite:///image_info.db", echo=False)
SQLModel.metadata.create_all(engine)  # 必须要放到申明的sqlmodel后面才能生成表
session = Session(engine)
imgs=[]
for root, dirs, files in os.walk("E:\\spider", topdown=False):
    # print(f'{root}下共有{len(files)}张图片')
    files=list(filter(lambda f:f.endswith('.jpg'),files))
    for _ in tqdm(files,desc="正在输出图片信息到数据库……"):
        file=os.path.join(root, _)
        # if file.endswith('.jpg'):
        try:
            img=Image.open(file)
            w,h=img.size
            img.close()
            imgs.append(ImageSize(image_path=file,width=w,height=h))
        except OSError:
            print(f'[!] 该文件无法正常打开：{file}')
            img.close()
session.bulk_save_objects(imgs)
session.commit()
session.close()