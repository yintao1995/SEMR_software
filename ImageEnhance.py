# -*- coding: utf-8 -*-

from PIL import Image
from skimage import io
import numpy as np
import matplotlib.pyplot as plt

import datetime

#使绘图可显示汉字（黑体）
from pylab import mpl
mpl.rcParams['font.sans-serif'] = ['SimHei']


'''-------------------------------------------------------------------
    Name：rgb2gray
    Input：三维数组（三通道）
    Output：一维数组（灰度通道）
    Function：rgb图片转灰度图函数
-------------------------------------------------------------------'''
def rgb2gray(rgb):
    return np.dot(rgb[...,:3], [0.299, 0.587, 0.144])

'''-------------------------------------------------------------------
    Name：HistEqualFunc
    Input：二维数组（灰度通道）
    Output：一维数组（灰度通道）
    Function：直方图均衡化
-------------------------------------------------------------------'''
def HistEqualFunc(gray_Pic):    
    #灰度像素统计/图像遍历
    #NumPx=np.zeros([1,256]).astype(np.int32)
    NumPx=np.zeros(264)
    for i in range(gray_Pic.shape[0]):
        for j in range(gray_Pic.shape[1]):
            #print(i,',',j,'=',gray_Pic[i,j])
            NumPx[gray_Pic[i,j]]=NumPx[gray_Pic[i,j]]+1
    #概率密度分布函数
    #ProbPx=np.zeros([1,256])
    ProbPx=np.zeros(264)
    for i in range(264):
        ProbPx[i]=NumPx[i]/(gray_Pic.shape[0]*gray_Pic.shape[1]*1.0)
    #累计分布函数
    CumuPx=np.zeros(264)
    for i in range(264):
        if i==0:
            CumuPx[i]=ProbPx[i]
        else:
            CumuPx[i]=CumuPx[i-1]+ProbPx[i]
    #累计分布函数取整
    CumuPx=np.around(255*CumuPx).astype(np.int32)
    #灰度值均衡化
    for i in range(gray_Pic.shape[0]):
        for j in range(gray_Pic.shape[1]):
            gray_Pic[i,j]=CumuPx[gray_Pic[i,j]]
    #返回均衡化结果
    return gray_Pic

'''-------------------------------------------------------------------
    Name：MeanFilter
    Input：二维数组（灰度通道），图片宽，图片高，滤波器宽度
    Output：none
    Function：从左到右，从上到下滑动，均值滤波器
-------------------------------------------------------------------'''
def MeanFilter(gray_Pic,shadeSize):
    picHeight=grayPic.shape[0]
    picWidth=grayPic.shape[1]
    Filter=np.zeros([shadeSize,shadeSize])
    n=int((shadeSize-1)/2)
    mean_Pic=np.zeros([picHeight-n,picWidth-n])
    for i in range(0,picHeight-shadeSize):
        for j in range(0,picWidth-shadeSize):
            for h in range(shadeSize):
                for w in range(shadeSize):
                    Filter[w,h]=gray_Pic[i+h,j+w]
            #计算遮罩中的均值
            mean_Pic[i,j]=culMean(Filter)    
    
    return mean_Pic

'''-------------------------------------------------------------------
    Name：culMean
    Input：数组shade
    Output：该数组均值
    Function：求均值
-------------------------------------------------------------------'''
def culMean(shade):
    shadeSum=0
    for i in range(shade.shape[0]):
        for j in range(shade.shape[1]):
            shadeSum=shadeSum+shade[i,j]

    shadeMean=shadeSum/(shade.shape[0]*shade.shape[1])
    return shadeMean

'''-------------------------------------------------------------------
    Name：MedianFilter
    Input：二维数组（灰度通道），图片宽，图片高，滤波器宽度
    Output：median_Pic
    Function：从左到右，从上到下滑动，中值滤波器
-------------------------------------------------------------------'''
def MedianFilter(gray_Pic,shadeSize):
    picHeight=grayPic.shape[0]
    picWidth=grayPic.shape[1]
    Filter=np.zeros([shadeSize,shadeSize])
    n=int((shadeSize-1)/2)
    median_Pic=np.zeros([picHeight-n,picWidth-n])
    for i in range(0,picHeight-shadeSize):
        for j in range(0,picWidth-shadeSize):
            for h in range(shadeSize):
                for w in range(shadeSize):
                    Filter[w,h]=gray_Pic[i+h,j+w]
            #计算遮罩中的均值
            median_Pic[i,j]=culMedian(Filter)    
    
    return median_Pic

'''-------------------------------------------------------------------
    Name：culMedian
    Input：数组shade
    Output：该数组中值
    Function：求中值
-------------------------------------------------------------------'''
def culMedian(shade):
    shadeLine=shade.flatten()#二维展成一维
    n=int((shadeLine.shape[0]-1)/2)
    shadeRank=np.argsort(shadeLine)#排序得序号
    shadeMedian=shadeLine[shadeRank[n]]#取中值
    return shadeMedian

'''-------------------------------------------------------------------
    Name：IdealFilter
    Input：二维数组（灰度通道）,滤波器大小,滤波器选择
    Output：二维数组（灰度通道）
    Function：理想滤波器,mask_H高通,mask_L低通,mask_B带通
-------------------------------------------------------------------'''
def IdealFilter(gray_Pic,DL,DH,mode):
    h,w=gray_Pic.shape
    #高通
    mask_H=np.ones(gray_Pic.shape,np.uint8)
    mask_H[h//2-DL:h//2+DL,w//2-DL:w//2+DL]=0
    #低通
    mask_L=np.zeros(gray_Pic.shape,np.uint8)
    mask_L[h//2-DH:h//2+DH,w//2-DH:w//2+DH]=1
    #带通
    mask_B=mask_H*mask_L
    #傅里叶变换
    Pic_fft=np.fft.fft2(gray_Pic)
    Pic_ffts=np.fft.fftshift(Pic_fft)
    #选择滤波器
    if (mode==1):
        Pic_mask=Pic_ffts*mask_L
    elif (mode==2):
        Pic_mask=Pic_ffts*mask_H
    else:
        Pic_mask=Pic_ffts*mask_B
    #傅里叶逆变换
    Pic_iffts=np.fft.ifftshift(Pic_mask)
    Pic_ifft=np.fft.ifft2(Pic_iffts)
    _Pic=np.abs(Pic_ifft)
    return _Pic

'''-------------------------------------------------------------------
    Name：ButterworthFilter
    Input：二维数组（灰度通道）,低通滤波器大小,高通滤波器大小,滤波器选择
    Output：二维数组（灰度通道）
    Function：巴特沃斯滤波器,huv_L低通,huv_H高通,huv_B带通
-------------------------------------------------------------------'''
def ButterworthFilter(gray_Pic,D0_L,D0_H,mode):
    h,w=gray_Pic.shape
    duv=np.ones([h,w])
    huv_H=np.zeros([h,w])
    huv_L=np.ones([h,w])
    for u in range(h):
        for v in range(w):
            duv[u,v]=(((u-(h//2)-0.5)**2)+((v-(w//2)-0.5)**2))**0.5
            #高通
            huv_H[u,v]=1-1/(1+(duv[u,v]/D0_H)**2)
            #低通
            huv_L[u,v]=1/(1+(duv[u,v]/D0_L)**2)
    #带通
    huv_B=huv_H*huv_L
    #傅里叶变换
    Pic_fft=np.fft.fft2(gray_Pic)
    Pic_ffts=np.fft.fftshift(Pic_fft)
    #选择滤波器
    if (mode==1):
        Pic_mask=Pic_ffts*huv_L
    elif (mode==2):
        Pic_mask=Pic_ffts*huv_H
    else:
        Pic_mask=Pic_ffts*huv_B
    #傅里叶逆变换
    Pic_iffts=np.fft.ifftshift(Pic_mask)
    Pic_ifft=np.fft.ifft2(Pic_iffts)
    _Pic=np.abs(Pic_ifft)
    return _Pic

'''-------------------------------------------------------------------
    Name：GaussFilter
    Input：二维数组（灰度通道）,低通滤波器大小,高通滤波器大小，滤波器选择
    Output：二维数组（灰度通道）
    Function：高斯滤波器,huv_H高通,huv_L低通,huv_B带通
-------------------------------------------------------------------'''
def GaussFilter(gray_Pic,D0_L,D0_H,mode):
    h,w=gray_Pic.shape
    duv=np.ones([h,w])
    huv_H=np.zeros([h,w])
    huv_L=np.ones([h,w])
    for u in range(h):
        for v in range(w):
            duv[u,v]=(((u-(h//2)-0.5)**2)+((v-(w//2)-0.5)**2))**0.5
            #高通
            huv_H[u,v]=1-np.exp(-(duv[u,v]**2)/(2*D0_H**2))
            #低通
            huv_L[u,v]=np.exp(-(duv[u,v]**2)/(2*D0_L**2))
    #带通
    huv_B=huv_H*huv_L
    #傅里叶变换
    Pic_fft=np.fft.fft2(gray_Pic)
    Pic_ffts=np.fft.fftshift(Pic_fft)
    #选择滤波器
    if (mode==1):
        Pic_mask=Pic_ffts*huv_L
    elif (mode==2):
        Pic_mask=Pic_ffts*huv_H
    else:
        Pic_mask=Pic_ffts*huv_B
    #傅里叶逆变换
    Pic_iffts=np.fft.ifftshift(Pic_mask)
    Pic_ifft=np.fft.ifft2(Pic_iffts)
    _Pic=np.abs(Pic_ifft)
    return _Pic

'''-------------------------------------------------------------------
    主程序：图片读取、频域滤波、显示结果
-------------------------------------------------------------------'''
def enhance_image(path,*mybox):
#用skimage读取图片/numpy数组格式
    fileName = path
    rgbPic=io.imread(fileName)
    if mybox and len(mybox)==4:
        #rgbPic=rgbPic[mybox[0]:mybox[0]+mybox[1],mybox[2]:mybox[2]+mybox[3]]
        rgbPic=rgbPic[mybox[1]:mybox[1]+mybox[3],mybox[0]:mybox[0]+mybox[2]]
    
    #将rgb图片转为灰度图并取整
    grayPic=np.around(rgb2gray(rgbPic)).astype(np.int32)
    gray_Pic=np.around(rgb2gray(rgbPic)).astype(np.int32)
    '''
    new1=IdealFilter(grayPic,12,80,1)
    new2=ButterworthFilter(grayPic,40,30,1)
    new3=GaussFilter(grayPic,25,25,1)
    '''
    ###参数设定：
    HFH2_filter = 27
    FHF1_filter = 23
    FHF3_filter = 20
    FHF4_filter = 20

    #增强-滤波-增强
    HFH1=HistEqualFunc(gray_Pic)
    HFH2=GaussFilter(HFH1,HFH2_filter,25,1)

    #滤波-增强-滤波
    FHF1=GaussFilter(gray_Pic,FHF1_filter,25,1)
    FHF2=HistEqualFunc(FHF1.astype(int))
    FHF3=GaussFilter(FHF2,FHF3_filter,25,1)
    FHF4=ButterworthFilter(FHF2,FHF4_filter,30,1)

    ###打印内容：
    Print = '图'+fileName+'：\n\n'
    Print = Print+'增强-滤波：\n滤波下限='+np.str(HFH2_filter)+'\n\n'
    Print = Print+'滤波-增强-滤波：\n1次滤波下限='+np.str(FHF1_filter)+'\n2次滤波下限='+np.str(FHF3_filter)+'\n3次滤波下限='+np.str(FHF4_filter)+'\n\n'


    fig=plt.figure('enhanced effect',figsize=(20,10))
    plt.subplot(2,4,1).imshow(rgbPic,cmap ='gray')
    plt.subplot(2,4,2).imshow(grayPic,cmap ='gray')
    plt.subplot(2,4,3).imshow(HFH1,cmap ='gray')
    plt.subplot(2,4,4).imshow(HFH2,cmap ='gray')

    '''
    plt.subplot(2,4,4).text(0.1,0.1,Print,fontsize=12)
    plt.xticks([])
    plt.yticks([])
    '''
    plt.subplot(2,4,5).imshow(FHF1,cmap ='gray')
    plt.subplot(2,4,6).imshow(FHF2,cmap ='gray')
    plt.subplot(2,4,7).imshow(FHF3,cmap ='gray')
    plt.subplot(2,4,8).imshow(FHF4,cmap ='gray')

    now = datetime.datetime.now()
    nowTime = np.str(now.year)+np.str(now.month)+np.str(now.day)+np.str(now.hour)+np.str(now.minute)+np.str(now.second)
    #fig.savefig('save/FHF_'+fileName+'_'+nowTime+'.jpg')

    plt.show()
#enhance_image('F:/desktop/test11.jpg',50,150,0,50)



