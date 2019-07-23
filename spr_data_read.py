# _*_ coding:utf-8 _*_
import matplotlib.pyplot as plt
import numpy as np

def read_data(path, sep, fn=''): # path为文件路径, fn为无后缀的文件名, sep为分隔符 #目前仅支持jdx和txt文件
    if(fn):
        filename = path+'/'+fn
    else:
        filename = path
    data = {}
    with open(filename, 'r',encoding='UTF-8') as file_obj:
        for line in file_obj.readlines():
            #print(line)
            temp = line.strip().split(sep)  # 每行按Tab分割成两部分
            try:
                x_data = float( temp[0].strip() )
                y_data = float( temp[1].strip() )
                data[x_data] = y_data  # 按键值对存入字典
            except:
                pass
    return data


def visual_data(a,section=None):

                                                            # 参数a是一个字典,其中的键是x轴,值是y轴
                                                            # 参数section是人工校准区域,输入(a,b)则截取这一片段进行拟合求得极小值
    #采样
    N=5
    x_data = list(a.keys())
    x1=[x_data[i] for i in range(0,len(x_data),N)]
    y_data = list(a.values())
    y1 = [y_data[i] for i in range(0, len(y_data), N)]

    # plt.plot(x1,y1)
    # plt.scatter(x1,y1,s=5)
    #归一化
    y_max = max(y1)
    n_y1 = [a/y_max for a in y1] #采样+归一
    # fig1=plt.figure("Spectrum")
    # plt.plot(x1, n_y1)
    ymax=max(y_data)
    n_y=[a/ymax for a in y_data] #不采样+归一


    if not section:
        #基础算法寻找极小值

        temp = find_min(n_y1,N)
        print('temp:',temp)
        if not temp:
            return x_data,n_y,0
        # print(x1[temp[0]],temp[1])  #共振波长x1[temp[0]]
        # print("rough estimation:",x1[temp[0]])
        # plt.axvline(x1[temp[0]],c='blue',alpha=0.3)

        #截取在“最小值”左右各20nm的步长区域
        length=20
        #index=cut_list(x1,580,630)
        index = cut_list(x1, x1[temp[0]]-length, x1[temp[0]]+length)
        cut_x=x_data[N*index[0]:N*index[1]]
        cut_y=n_y[N*index[0]:N*index[1]]
        # plt.plot(cut_x,cut_y)
    else: #否则人工指定截取、拟合区域
        index=cut_list(x_data,section[0],section[1])
        cut_x=x_data[index[0]:index[1]]
        cut_y=n_y[index[0]:index[1]]
        # plt.plot(cut_x,cut_y)

    #对截取的区域进行多项式拟合
    cut_x=np.array(cut_x)
    cut_y=np.array(cut_y)
    z1=np.polyfit(cut_x,cut_y,3)  #z1为拟合后的系数
    p1=np.poly1d(z1)
    print(p1)  # p1为拟合的多项式
    fitted_y=p1(cut_x)
    # plt.plot(cut_x,fitted_y,c='red')

    #对拟合后的多项式直接寻找最小值即可
    min_y=min(fitted_y)

    for i in range(0,len(cut_x)):
        if fitted_y[i]==min_y:
            resonance_wavelength=cut_x[i]
            break
    return x_data,n_y,resonance_wavelength
            # print("fitted resonance wavelength :",resonance_wavelength)
            # plt.axvline(resonance_wavelength, c='red', alpha=0.5)

    # plt.text(500 , 0.2, "resonance wavelength="+str(resonance_wavelength)+"nm")
    # plt.show()

def cut_list(list,a1,a2): #将列表L从x轴a1-a2截取出来,其中L中的数字是单增的
    for i in range(len(list)):# 从前往后
        if list[i]<a1:
            pass
        else:
            i1=i
            break
    if list[-1] < a2:  # 如果范围超出了数据。直接返回最后一个
        return i1,-1
    for i in range(i1,len(list)):
        if list[i]<a2:
            pass
        else:
            i2=i
            break
    return i1,i2 #返回index


def find_min(a,N): # 求一串数字列表的极小值
    # plt.plot(a)
    # print(len(a))
    # print(500/N,len(a)-750/N)
    # print(a[int(len(a)-750/N)])
    for i in range(round(500/N), len(a)-round(250/N)):
        # print(a[400])
        if a[i-1] < a[i] or a[i+1] < a[i]:
            pass

        # elif a[i-1] > a[i] and a[i+1] > a[i]:  # bug：相等
        else:
            if a[i-round(50/N)] > a[i] and a[i+round(50/N)] > a[i]:
                print( a[i-round(50/N)] ,a[i+round(50/N)] )
            #i是极小值处于列表中的第i个数,a[i]是对应的y值
                return i,a[i]

if __name__ == "__main__":
    path="C:/Users/yintao/PycharmProjects/SPR_System/Test_Data/test1.txt"
    data=visual_data(read_data(path,'\t'))
    #
    fig=plt.figure(figsize=(10,5),dpi=100)
    plt.plot(data[0],data[1])
    plt.axvline(data[2],c='red',alpha=0.5)
    # plt.text(500 , 0.2, "resonance wavelength="+str(data[2])+"nm")
    plt.text(500 , 0.2, "resonance wavelength="+str(data[2])+"nm")
    label=['-12°']
    plt.legend(label)
    plt.show()