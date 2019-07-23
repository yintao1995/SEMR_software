import matplotlib.pyplot as plt
import numpy as np
from scipy import signal


def cut_list(list,a1,a2): #将列表L从x轴a1-a2截取出来,其中L中的数字是单增的
    for i in range(len(list)):# 从前往后
        if list[i]<a1:
            pass
        else:
            i1=i
            break
    for i in range(i1,len(list)):
        if list[i]<a2:
            pass
        else:
            i2=i
            break
    return i1,i2 #返回index

def raman_read(path,fc=None,section=None): #路径、截止频率，选区
    filename=path
    x_data=[]
    y_data=[]
    with open(filename,'r') as file_obj:
        lines=file_obj.readlines()[8:] # 前8行不是数据
        for line in lines:
            temp=line.strip().split(";")
            x_data.append(float(temp[1])) # 数据的第二列为x轴
            y_data.append(float(temp[2])) # 第三列为y轴
    # fig1=plt.figure("whole range")
    # plt.plot(x_data,y_data)
    if not section:
        return x_data,y_data


    index=cut_list(x_data,section[0],section[1])
    x_data=x_data[index[0]:index[1]]
    y_data=y_data[index[0]:index[1]]
    print(len(x_data))

    # plt.plot(x_data,y_data)

    z=np.polyfit(x_data,y_data,1) # 系数
    p1=np.poly1d(z)  # 拟合式
    # print(p1)

    fitted_y_data=p1(x_data)
    # plt.plot(x_data,fitted_y_data)

    detrend_y=y_data-fitted_y_data
    # plt.plot(x_data,detrend_y)
    # plt.plot(x_data,signal.detrend(y_data))

    #使用低通滤波器处理
    b,a=signal.butter(3,fc,'low') #阶数+归一化截止频率
    filter_y=signal.filtfilt(b,a,detrend_y)
    # fig = plt.figure("800-2000 range")

    return x_data,filter_y
    # plt.plot(x_data,filter_y)
    # plt.xlabel("Raman shift($cm^{-1}$)")


    # def call_back(event):
    #     if event.button == 2: #用鼠标滚轮标记
    #         plt.text(event.xdata, event.ydata, str(round(event.xdata)),color='red' )
    #         fig.canvas.draw_idle()
    # fig.canvas.mpl_connect('button_press_event',call_back)
    #
    # plt.show()


# raman_read("C:/Users/yintao/Desktop/NEW0024.trt",0.35)