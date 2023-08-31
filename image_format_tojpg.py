import pillow_avif
from PIL import Image
import os
from icecream import ic
from tqdm import tqdm
os.chdir(os.path.dirname(__file__))

img_cnt=0
del_jpeg=False
for root, dirs, files in tqdm(os.walk("E:/spider", topdown=False),desc="正在转换文件夹"):
    print(f'{root}下共有{len(files)}张图片')
    for _ in tqdm(files,desc="正在转换图片格式……"):
        file=os.path.join(root, _)
        if file.endswith('.jpeg'):
            try:
                img=Image.open(file)
                img.save(os.path.splitext(file)[0]+'_origin'+'.jpg','jpeg')
                img.close()
            except OSError:
                print(f'[!] 该文件无法正常转换：{file}')
                imgnew = img.convert('RGB')
                imgnew.save(os.path.splitext(file)[0]+'_origin'+'.jpg','jpeg')
                img.close()
            if del_jpeg:
                os.remove(file)
        # break

