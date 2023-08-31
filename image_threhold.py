import cv2
import numpy as np
from matplotlib import pyplot as plt
import os
os.chdir(os.path.dirname(__file__))
print( cv2.__version__ )
from PIL import Image
# img=Image.open('./bird.jpg')
cv2.namedWindow('image', cv2.WINDOW_NORMAL)
cv2.namedWindow('hsv', cv2.WINDOW_NORMAL)
# img=cv2.imread('./bird.jpg')
img=cv2.imread('./example_meng.png')
blur = cv2.blur(img,(5,5))
blur0=cv2.medianBlur(blur,5)
blur1= cv2.GaussianBlur(blur0,(5,5),0)
blur2= cv2.bilateralFilter(blur1,9,75,75)

hsv = cv2.cvtColor(blur2, cv2.COLOR_BGR2HSV)
cv2.imshow('hsv',hsv[:,:,0])
(thresh, im_bw) = cv2.threshold(hsv[:,:,0], 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
cv2.imshow('image', im_bw)


# low_blue = np.array([55, 0, 0])
# high_blue = np.array([118, 255, 255])
# mask = cv2.inRange(hsv, low_blue, high_blue)
# res = cv2.bitwise_and(img,img, mask= mask)

# cv2.imshow('image',res)
cv2.waitKey(0)
cv2.destroyAllWindows()
# cv2.IMREAD_COLOR：默认参数，读入一副彩色图片，忽略alpha通道
# cv2.IMREAD_GRAYSCALE：读入灰度图片
# cv2.IMREAD_UNCHANGED：顾名思义，读入完整图片，包括alpha通道
# img=cv2.imread('./image/2.jpg',0) # 0的是IMREAD_GRAYSCALE
# cv2.IMREAD_COLOR
# tinify.key="0C3kwbfXHGTjVwNmcVHjGdrdNkP983gh"
#  BGR 三个通道
# cv2.namedWindow('image', cv2.WINDOW_NORMAL)
# cv2.imshow('image',img)
# cv2.waitKey(0)
# cv2.destroyAllWindows()
# plt.imshow(img, cmap = 'gray', interpolation = 'bicubic')
# plt.xticks([]), plt.yticks([])  # to hide tick values on X and Y axis
# plt.show()
# cv2.imwrite('messigray.png',img)

# img = np.zeros((512,512,3), np.uint8)
# # Draw a diagonal blue line with thickness of 5 px
# cv2.line(img,(0,0),(511,511),(255,0,0),5)
# cv2.namedWindow('image',cv2.WINDOW_NORMAL)
# cv2.resizeWindow('image',1000,1000)#定义frame的大小
# cv2.imshow('image',img)
# cv2.waitKey(0)
# cv2.destroyAllWindows()
# def draw_circle(event, x, y, flags, param):
#     if event == cv2.EVENT_LBUTTONDBLCLK:
#         cv2.circle(img, (x, y), 100, (255, 0, 0), -1)


# # 创建图像与窗口并将窗口与回调函数绑定
# img = np.zeros((500, 500, 3), np.uint8)
# cv2.namedWindow('image')
# cv2.setMouseCallback('image', draw_circle)

# while (1):
#     cv2.imshow('image', img)
#     if cv2.waitKey(1)&0xFF == ord('q'):#按q键退出
#         break
# cv2.destroyAllWindows()