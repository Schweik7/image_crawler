# 可以选择当height小于500的时候，变成750*500；当height大于500的时候变成500*750

# from PIL import Image
import cv2
import os
from icecream import ic
from tqdm import tqdm

os.chdir(os.path.dirname(__file__))

# E:\\spider->E:\\resized_image
width=750
height=500
path=".\\image"
resized_path=os.path.join(os.path.dirname(path),"resized_image")
path=path.rstrip('\\')
head,image_dir=os.path.split(path)
os.mkdir(resized_path)
for root, dirs, files in os.walk(path, topdown=False):
    print(f'{root}下共有{len(files)}张图片')
    print(f'正在修改{root}文件夹内图片大小')
    out_dir=root.replace(image_dir,"resized_image")
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)
    files=list(filter(lambda f:f.endswith('.jpg'),files))
    for _ in tqdm(files,desc="正在修改图片大小"):
        file=os.path.join(root, _)
        try:
            # img=Image.open(file)
            img=cv2.imread(file)
            w,h=img.size
            if h<500:  
                new_img=img.resize((width,height),Image.BILINEAR)
            else:
                new_img=img.resize((height,width),Image.BILINEAR)            
            img.close()
            new_img_path=os.path.join(out_dir,_)
            new_img.save(new_img_path)
        except OSError:
            print(f'[!] 该文件无法正常打开：{file}')
            img.close()
