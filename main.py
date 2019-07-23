# -*- coding: utf-8 -*-
"""
Created on Sun Oct 12 13:53:58 2014
@author: kun

Updated on Oct 2018
@author: Tao
"""

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import QApplication, QMainWindow
# from pyExcelerator import *
from PIL import Image
import numpy as np
import matplotlib
from guiqwt.plot import CurveDialog
from guiqwt.builder import make
matplotlib.use("Qt5Agg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar


import dialog_setPara
import dialog_setNum
import dialog_confirm
import dialog_orienAngle
import dialog_adsorption
import dialog_surfaceCover
import dialog_table
import P_d_dialog
import Mymath
import threadForProcessData
from hue_of_image import hue_of_image, draw_image
from spr_data_read import read_data, visual_data, cut_list
from raman_data_read import raman_read
from ImageEnhance import enhance_image
import json
import sys
import os
import psutil
import numpy
from scipy.optimize import curve_fit
from scipy import signal
import math
from time import *

#定义一些阈值可以在设置中更改
var_len1 = 100
var_thres1 = 0.000004*100000.0
smooth_len1 = 3
smooth_num1 = 1
peak_step1 = 3
#phi_step = 50
phi_step = 10
fit_type = 0

var_len2 = 15
#var_thres2 = 0.00002*100000.0
#var_thres2 = 50
var_thres2 = 10
smooth_len2 = 10
smooth_num2 = 3
peak_step2 = 20
peak_thres = 0.01
#peak_thres = 0.03


##人为设置拟合范围，针对吸附常数测量
time_from1 = 0
time_to1 = 300
##人为设置拟合范围，针对脱附速率的测量
time_from2 = 40
time_to2 = 240

# QTextCodec.setCodecForTr(QTextCodec.codecForName("utf8"))
# Qt5中去掉了setCodecForTr

class MainWindow(QMainWindow):
 
    def __init__(self,parent=None):
        super(MainWindow,self).__init__(parent)
        #参数初始化
        #程序一初始化：
        self.var_len1 = var_len1
        self.var_thres1 = var_thres1
        self.smooth_len1 = smooth_len1
        self.smooth_num1 = smooth_num1
        self.peak_step1 = peak_step1
        self.phi_step = phi_step
        self.fit_type = fit_type
        #程序二初始化：
        self.var_len2 = var_len2
        self.var_thres2 = var_thres2
        self.smooth_len2 = smooth_len2
        self.smooth_num2 = smooth_num2
        self.peak_step2 = peak_step2
        self.peak_thres = peak_thres
        #泵参数设置：
        self.flag_reverse = True
        self.SerialPort = 1
        #参数初始化结束
        
        self.setWindowTitle(self.tr("多光谱融合表界面原位分析测试系统"))
        #第一个tal
        graphicsView=QGraphicsView()
        scene=QGraphicsScene()
        scene.addPixmap(QPixmap('icon/logo.png'))
        graphicsView.setScene(scene)
        
        self.tabWidget = QTabWidget(self)
        self.tabWidget.addTab(graphicsView, "Welcome")
        self.tabWidget.setFont(QFont("Helvetica",10,QFont.Normal))
        self.tabWidget.setTabsClosable(True)  # 使得标签页可以关闭
        self.tabWidget.tabCloseRequested.connect(self.removeTab)
        # self.connect(self.tabWidget,SIGNAL("tabCloseRequested(int)"),self.removeTab)

        
        #加到一个区块中
        self.stack=QStackedWidget()   
        self.stack.setFrameStyle(QFrame.Panel|QFrame.Raised)    
        self.stack.addWidget(self.tabWidget)
        self.setCentralWidget(self.stack)
        #菜单
        #toolbar = MyTool()
        self.createActions()
        self.createMenus()
        self.createToolBars()
        
        #停靠窗口2
        dock2=QDockWidget(self.tr("Results Show"),self)
        dock2.setFont(QFont("Helvetica",10,QFont.Normal))
        dock2.setFeatures(QDockWidget.DockWidgetFloatable|QDockWidget.DockWidgetClosable)
        self.addDockWidget(Qt.RightDockWidgetArea,dock2)
        self.listWidget_result = QListWidget()
        dock2.setWidget(self.listWidget_result)
        
        #左侧第一栏
        self.listWidget_1=QListWidget()
        self.listWidget_1.insertItem(0,self.tr("Open DAQ"))
        self.listWidget_1.insertItem(1,self.tr("Load File"))
        self.listWidget_1.insertItem(2,self.tr("Process"))
        self.listWidget_1.insertItem(3,self.tr("Clear"))
        
        self.groupbox1=QGroupBox()  
        self.groupbox1.setTitle(self.tr("Polarized Interferometry"))
        self.groupbox1.setFont(QFont("Helvetica",8,QFont.Bold))
        self.groupbox1.setCheckable(True)
        self.groupbox1.setChecked(False)
        self.groupbox1.showMinimized()
        # self.connect(self.groupbox1,SIGNAL("clicked(bool)"),self.selectType1)
        self.groupbox1.clicked.connect(self.selectType1)
        # 选择这一测试模块，则其他模块关闭；关闭这一模块，则下一个模块被选择
        vlayout1=QVBoxLayout(self.groupbox1)
        vlayout1.setContentsMargins(10,10,10,10)
        ## vlayout1.setContentsMargins(10,10,10,10) # 在Qt5中，QVBoxLayout的setMargin方法已经替换成了setContentsMargins
        vlayout1.setAlignment(Qt.AlignCenter)
        vlayout1.addWidget(self.listWidget_1)
        
        #左侧第二栏
        self.listWidget_2=QListWidget()
        self.listWidget_2.insertItem(0,self.tr("Open Spectra Suite"))
        # self.listWidget_2.insertItem(1, self.tr("Draw & Process"))
        # self.listWidget_2.insertItem(2, self.tr("Ad/de-sorption"))

        self.listWidget_2.insertItem(1,self.tr("Load Dark Spectrum"))
        self.listWidget_2.insertItem(2,self.tr("Load Ref Spectrum"))
        self.listWidget_2.insertItem(3,self.tr("Load Signal Spectrum"))
        self.listWidget_2.insertItem(4,self.tr("Process"))
        self.listWidget_2.insertItem(5,self.tr("load some spectrum"))
        self.listWidget_2.insertItem(6,self.tr("clear"))
        
        self.groupbox2=QGroupBox()
        self.groupbox2.setTitle(self.tr("Polarized Absorption Spectrometry"))
        self.groupbox2.setFont(QFont("Helvetica",8,QFont.Bold))
        self.groupbox2.setCheckable(True)
        self.groupbox2.setChecked(False)
        self.groupbox2.showMinimized()
        # self.connect(self.groupbox2,SIGNAL("clicked(bool)"),self.selectType2)
        self.groupbox2.clicked.connect(self.selectType2)
        vlayout2=QVBoxLayout(self.groupbox2)   
        vlayout2.setContentsMargins(10,10,10,10)   
        vlayout2.setAlignment(Qt.AlignCenter)   
        vlayout2.addWidget(self.listWidget_2)  

        ##############
        self.listWidget_25=QListWidget()
        self.listWidget_25.insertItem(0, self.tr("Open Spectra Suite"))
        self.listWidget_25.insertItem(1, self.tr("Draw & Process"))
        self.listWidget_25.insertItem(2, self.tr("Ad/de-sorption"))
        self.listWidget_25.insertItem(3, self.tr("Calc thickness"))
        self.listWidget_25.insertItem(4, self.tr("Clear"))

        self.groupbox25 = QGroupBox()
        self.groupbox25.setTitle(self.tr("Spectral SPR Measurement"))
        self.groupbox25.setFont(QFont("Helvetica", 8, QFont.Bold))
        self.groupbox25.setCheckable(True)
        self.groupbox25.setChecked(False)
        self.groupbox25.showMinimized()

        self.groupbox25.clicked.connect(self.selectType25)
        vlayout25 = QVBoxLayout(self.groupbox25)
        vlayout25.setContentsMargins(10, 10, 10, 10)
        vlayout25.setAlignment(Qt.AlignCenter)
        vlayout25.addWidget(self.listWidget_25)
        ##############

        #左侧第三栏
        self.listWidget_3=QListWidget()
        self.listWidget_3.insertItem(0,self.tr("Open AvaRaman"))
        self.listWidget_3.insertItem(1,self.tr("Load File"))
        self.listWidget_3.insertItem(2,self.tr("Process"))
        self.listWidget_3.insertItem(3,self.tr("Clear"))
        
        self.groupbox3=QGroupBox()  
        self.groupbox3.setTitle(self.tr("Raman Spectrometry"))
        self.groupbox3.setFont(QFont("Helvetica",8,QFont.Bold))
        self.groupbox3.setCheckable(True)
        self.groupbox3.setChecked(False)
        self.groupbox3.showMinimized()
        # self.connect(self.groupbox3,SIGNAL("clicked(bool)"),self.selectType3)
        self.groupbox3.clicked.connect(self.selectType3)
        vlayout3=QVBoxLayout(self.groupbox3)   
        vlayout3.setContentsMargins(10,10,10,10)   
        vlayout3.setAlignment(Qt.AlignCenter)
        vlayout3.addWidget(self.listWidget_3)
        
        #左侧第四栏
        self.listWidget_4=QListWidget()
        self.listWidget_4.insertItem(0,self.tr("Open GamryFramework"))
        self.listWidget_4.insertItem(1,self.tr("Open EchemAnalyst"))
        self.listWidget_4.insertItem(2,self.tr("Load File"))
        self.listWidget_4.insertItem(3,self.tr("Process"))
        self.listWidget_4.insertItem(4,self.tr("Clear"))
        
        self.groupbox4=QGroupBox()  
        self.groupbox4.setTitle(self.tr("ElectroChemistry"))
        self.groupbox4.setFont(QFont("Helvetica",8,QFont.Bold))
        self.groupbox4.setCheckable(True)
        self.groupbox4.setChecked(False)
        self.groupbox4.showMinimized()
        # self.connect(self.groupbox4,SIGNAL("clicked(bool)"),self.selectType4)
        self.groupbox4.clicked.connect(self.selectType4)
        vlayout4=QVBoxLayout(self.groupbox4)   
        vlayout4.setContentsMargins(10,10,10,10)   
        vlayout4.setAlignment(Qt.AlignCenter)
        vlayout4.addWidget(self.listWidget_4)
        
        #左侧第五栏
        self.listWidget_5=QListWidget()
        self.listWidget_5.insertItem(0,self.tr("Open Camera"))
        self.listWidget_5.insertItem(1,self.tr("Load File"))
        self.listWidget_5.insertItem(2,self.tr("Process"))
        self.listWidget_5.insertItem(3,self.tr("Clear"))
        
        self.groupbox5=QGroupBox()  
        self.groupbox5.setTitle(self.tr("Image Analysis"))
        self.groupbox5.setFont(QFont("Helvetica",8,QFont.Bold))
        self.groupbox5.setCheckable(True)
        self.groupbox5.setChecked(False)
        self.groupbox5.showMinimized()
        # self.connect(self.groupbox5,SIGNAL("clicked(bool)"),self.selectType5)
        self.groupbox5.clicked.connect(self.selectType5)
        vlayout5=QVBoxLayout(self.groupbox5)   
        vlayout5.setContentsMargins(10,10,10,10)   
        vlayout5.setAlignment(Qt.AlignCenter)
        vlayout5.addWidget(self.listWidget_5)
 
        widget=QWidget()  
        vlayout=QVBoxLayout(widget)   
        vlayout.setContentsMargins(10,10,10,10)   
        vlayout.setAlignment(Qt.AlignCenter)   
        vlayout.addWidget(self.groupbox1)
        vlayout.addWidget(self.groupbox2)
        vlayout.addWidget(self.groupbox25)
        vlayout.addWidget(self.groupbox3)
        vlayout.addWidget(self.groupbox4)
        vlayout.addWidget(self.groupbox5)        
        
        # self.connect(self.listWidget_1,SIGNAL("itemSelectionChanged()"),self.slot_test1)
        # self.connect(self.listWidget_2,SIGNAL("itemSelectionChanged()"),self.slot_test2)
        # self.connect(self.listWidget_3,SIGNAL("itemSelectionChanged()"),self.slot_test3)
        # self.connect(self.listWidget_4,SIGNAL("itemSelectionChanged()"),self.slot_test4)
        # self.connect(self.listWidget_5,SIGNAL("itemSelectionChanged()"),self.slot_test5)
        # self.listWidget_1.itemSelectionChanged.connect(self.slot_test1)
        # self.listWidget_2.itemSelectionChanged.connect(self.slot_test2)
        # self.listWidget_3.itemSelectionChanged.connect(self.slot_test3)
        # self.listWidget_4.itemSelectionChanged.connect(self.slot_test4)
        self.listWidget_1.clicked.connect(self.slot_test1)
        self.listWidget_2.clicked.connect(self.slot_test2)
        self.listWidget_25.clicked.connect(self.slot_test25)
        self.listWidget_3.clicked.connect(self.slot_test3)
        self.listWidget_4.clicked.connect(self.slot_test4)
        self.listWidget_5.clicked.connect(self.slot_test5)
        # self.listWidget_5.clicked.connect(self.slot_test51)
        
        #停靠窗口4
        dock4=QDockWidget(self.tr("Please Choose Test Type"),self)

        dock4.setFont(QFont("Helvetica",10,QFont.Normal))
        dock4.setFeatures(QDockWidget.AllDockWidgetFeatures)
        dock4.setWidget(widget)
        self.addDockWidget(Qt.LeftDockWidgetArea,dock4)
        
        QThread.sleep(1)
        
    def removeTab(self, index): # 移除tab的时候按title找到应用进程并kill
        # print("remove tab index:",index)
        if index != -1:
            print("You have closed the tab whose index is: ",index)
            print("It's title is: ",self.tabWidget.tabText(index))
            to_remove_title = self.tabWidget.tabText(index)
            self.tabWidget.removeTab(index)
            if to_remove_title=='Camera':
                # self.kill_process('CAM-MS.exe')
                self.kill_process('s-gauge.exe')
            elif to_remove_title=='Spectra Suite':
                #关闭SpectraSuite时，还需要关闭java.exe
                self.kill_process("SpectraSuite.exe")
                self.kill_process("java.exe")
            elif to_remove_title=='AvaRaman':
                self.kill_process("raman_76_USB2.exe")
            elif to_remove_title=='Gamry Framework':
                self.kill_process("framework.exe")
            elif to_remove_title=='Gamry Echem Analyst':
                self.kill_process("Echem Analyst.exe")

            else:
                pass

    def kill_process(self,exe_name):
        if exe_name:
            print(exe_name)
            command = 'taskkill /F /IM ' + exe_name
            try:
                p_names = [psutil.Process(i).name() for i in psutil.pids()]
                if exe_name in p_names:
                    print("Find the process,killing...!")
                    os.system(command)
                else:
                    print("didn't find it!")
            except:
                pass
        else:
            pass



            
    def add_tab(self, widget, title, index=None):
        try:
            if index:
                inserted_index = self.tabWidget.insertTab(index, widget, self.tr(title))

            else:  #(运行的这边)
                # print("--no--")
                inserted_index = self.tabWidget.addTab(widget, self.tr(title))
                # print(type(inserted_index))  #class int
            self.tabWidget.setCurrentIndex(inserted_index)
            widget.setFocus()
            return inserted_index
        except AttributeError as reason:
            print(reason)
            print("Widget couldn't be added, doesn't inherit from ITabWidget")
                
    def slot_test1(self):
        print("slot_test1 is actived")
        dataProcess = Mymath.dataProcess()
        if (self.listWidget_1.currentRow()==0):
            try:
                self.statusBar().showMessage("Open DAQ...")
                f = open('path.txt')
                path1 = f.readline()
                #去除末尾的‘\n’                
                path1=path1[0:-1]
                if path1.split('::')[0]=='path1':
                    path1=path1.split('::')[1]
                    directory,filename = os.path.split(path1)
                    print(path1)

                    # import win32process
                    from win32 import win32process
                    handle=win32process.CreateProcess(path1, '', None , None , 0 ,
                                               win32process. REALTIME_PRIORITY_CLASS ,
                                               None , directory, win32process.STARTUPINFO())
                    # win32process.TerminateProcess(handle,0)
                    widget=QWidget()
                    self.add_tab(widget,title=u'DAQ')
                    import win32gui 
                    hwnd=win32gui.FindWindow(None,u"Strip Chart - Last.scc configuration")
                    print("----daq-test1----")
                    while hwnd==0:
                        hwnd=win32gui.FindWindow(None,u"Strip Chart - Last.scc configuration")
                    hwnd_menu=win32gui.FindWindowEx(hwnd,None,None,u"menuStrip1")
                    win32gui.SetParent(hwnd_menu,int(self.daqTools.winId()))
                    #hwnd_graph=win32gui.FindWindowEx(hwnd,None,u"WindowsForms10.Window.8.app.0.378734a",None)
                    win32gui.SetParent(hwnd,int(widget.winId()))
                    win32gui.MoveWindow(hwnd,widget.rect().x(),widget.rect().y(),
                                        widget.rect().width(),widget.rect().height(),True)
                    
            except:
                QMessageBox.warning(self,self.tr("Error"),self.tr("Please Choose the Path"))
        elif(self.listWidget_1.currentRow()==1):            
            try: 
                temp = self.slotOpenFile()
                if temp != -1:
                    [self.data_x,self.data_y] = temp
                curveWidget = CurveDialog(edit=False, toolbar=True, 
                      options=dict(xlabel="xlabel", ylabel="ylabel"))
                plot = curveWidget.get_plot()
                self.add_tab(curveWidget, title =u'Orignal Data')
                curve = make.curve(self.data_x, self.data_y, color="b")
                plot.add_item(curve)
            except:
                pass  
        #QMessageBox.information(self,"Information",
        #                self.tr("填写任意想告诉于用户的信息!"))
        elif(self.listWidget_1.currentRow()==2):
            
            #获取方差，分离出待处理信号
            self.statusBar().showMessage("separate the wanted signal...")
            var_temp = dataProcess.get_var(self.data_y,self.var_len1,100000.0)
          
            curveWidget = CurveDialog(edit=False, toolbar=True, 
                      options=dict(xlabel="xlabel", ylabel="ylabel"))
            plot = curveWidget.get_plot()
            self.add_tab(curveWidget, title =u'Various')
            curve = make.curve(self.data_x,var_temp, color="b")
            plot.add_item(curve)
            
            var=[]
            for i in range(len(var_temp)):
                if var_temp[i]>self.var_thres1:
                    var.append(1)
                else:
                    var.append(0)
            self.data_y_simpled = list(numpy.array(var)*numpy.array(self.data_y))
            self.data_x_simpled = self.data_x
            #获取每次测量的开始测量和结束测量的节点
            self.index_start = []
            self.index_end = []
            for i in range(len(var)-1):
                if var[i+1]-var[i]==1:
                    self.index_start.append(i+1)
                elif var[i+1]-var[i]==-1:
                    self.index_end.append(i+1)
            
            self.statusBar().showMessage("successed in separating the wanted signal...")
            
            #根据分离的信号的个数在listWidget中创建len（index_start）个item
            for i in range(min(len(self.index_start),len(self.index_end))):
                self.listWidget_1.insertItem(4+i,"test%i"%i)
        
        elif(self.listWidget_1.currentRow()==3):
            self.clearResults()
            
        elif(self.listWidget_1.currentRow()>3):
            print('00000111s1')
            
            i=self.listWidget_1.currentRow()-4
            
            self.data_x_seq = self.data_x_simpled[self.index_start[i]:self.index_end[i]]
            self.data_y_seq = self.data_y_simpled[self.index_start[i]:self.index_end[i]]
            
            #进行平滑处理
            for i in range(self.smooth_num1):
                self.data_y_seq = dataProcess.smooth(self.data_y_seq,self.smooth_len1)

            self.statusBar().showMessage("caculate the phase...")
            
            self.phi,peak_valley_x,peak_valley_y=self.slotTest1DataProcess(self.data_x_seq,self.data_y_seq)
            
            self.statusBar().showMessage("success...")            
            #更新结果显示区的listWidget
            self.listWidget_result.addItem("phi=%.3f    period=%.3f"%(self.phi,self.phi/math.pi/2.0)) 
            
            curveWidget = CurveDialog(edit=False, toolbar=True, 
                      options=dict(xlabel="xlabel", ylabel="ylabel"))
            plot = curveWidget.get_plot()
            self.add_tab(curveWidget, title =u'Processed Data')
            curve = make.curve(self.data_x_seq,self.data_y_seq,color="b")
            point = make.curve(peak_valley_x,peak_valley_y,linestyle="NoPen",marker="Ellipse")
            plot.add_item(curve)
            plot.add_item(point)
            
            self.statusBar().showMessage("caculate the phase changed as the time pass...")
            #计算相位随时间的变化
            step = self.phi_step
            #step = 200
            phase=[]
            time=[]
            i=range(self.data_x_seq.index(peak_valley_x[1])+step,len(self.data_x_seq),step)
            for ii in i:
                x=self.data_x_seq[0:ii]
                y=self.data_y_seq[0:ii]
                phi_temp,temp_x,temp_y=self.slotTest1DataProcess(x,y)
                phase.append(phi_temp)
                time.append(self.data_x_seq[ii])
            #手动添加相位为0的开始点
            phi_x=list(numpy.array(time)-self.data_x_seq[0])
            phi_y=phase
            
            self.statusBar().showMessage("success! And now begin least square procedure...") 
            #最小二乘拟合            
            p=dataProcess.leastsqProcess(numpy.array(phi_y),numpy.array(phi_x))
            x = numpy.linspace(min(phi_x),max(phi_x),1000)
            print(p)
            y = p[0]*x**3+p[1]*x**2+p[2]*x+p[3]

            data_x=list(x)
            data_y=list(y)
            self.statusBar().showMessage("success! Now ploting...") 
            
            curveWidget = CurveDialog(edit=False, toolbar=True, 
                      options=dict(xlabel="xlabel", ylabel="ylabel"))
            plot = curveWidget.get_plot()
            self.add_tab(curveWidget, title = u'Phase Change With Time')
            curve = make.curve(data_x,data_y, color="b")
            point = make.curve(phi_x,phi_y,linestyle="NoPen",marker="Ellipse")
            plot.add_item(curve)
            plot.add_item(point)
        
            
    def slot_test2(self):
        print("slot_test2 is actived")
        if (self.listWidget_2.currentRow()==0):
            try:
                self.statusBar().showMessage(self.tr("Open Spectra Suite..."))
                with open('path.json','r') as file_obj:
                    path_list=json.load(file_obj)
                    path2=path_list[1]
                    print(path2)
                directory, filename = os.path.split(path2)
                import win32process

                win32process.CreateProcess(path2, '', None, None, 0, win32process.REALTIME_PRIORITY_CLASS,
                                           None, directory, win32process.STARTUPINFO())
                print('ss opening..')

                widget = QWidget()
                self.add_tab(widget, title=u'Spectra Suite')
                import win32gui
                # QThread.sleep(5)
                sleep(5)
                start1 = time()
                hwnd = win32gui.FindWindow(None, u"Ocean Optics SpectraSuite ")
                while hwnd == 0:
                    hwnd = win32gui.FindWindow(None, u"Ocean Optics SpectraSuite ")
                    sleep(0.5)
                    end1 = time()
                    if end1 - start1 > 10:
                        QMessageBox.warning(self, self.tr("Error"),
                                            self.tr("Didn't find the process"))
                        break
                # finding_time=end1-start1
                # print(finding_time)
                win32gui.SetParent(hwnd, int(widget.winId()))
                win32gui.MoveWindow(hwnd, widget.rect().x(), widget.rect().y(), widget.rect().width(),
                                    widget.rect().height(), True)
                # f = open('path.txt')
                # path2 = f.readline()
                # path2 = f.readline()
                # #去除换行符‘\n’
                # path2=path2[0:-1]
                # if path2.split('::')[0]=='path2':
                #     path2=path2.split('::')[1]
                #     print(path2)
                #     directory,filename = os.path.split(path2)
                #     import win32process
                #
                #     win32process.CreateProcess(path2, '', None , None , 0 , win32process. REALTIME_PRIORITY_CLASS ,
                #                                None , directory, win32process.STARTUPINFO())
                #     print('ss opening..')
                #
                #     widget=QWidget()
                #     self.add_tab(widget,title=u'Spectra Suite')
                #     import win32gui
                #     #QThread.sleep(5)
                #     sleep(5)
                #     start1=time()
                #     hwnd=win32gui.FindWindow(None,u"Ocean Optics SpectraSuite ")
                #     while hwnd==0:
                #         hwnd=win32gui.FindWindow(None,u"Ocean Optics SpectraSuite ")
                #         sleep(0.5)
                #         end1 = time()
                #         if end1 - start1 > 10:
                #             QMessageBox.warning(self, self.tr("Error"),
                #                                 self.tr("Didn't find the process"))
                #             break
                #     # finding_time=end1-start1
                #     # print(finding_time)
                #     win32gui.SetParent(hwnd,int(widget.winId()))
                #     win32gui.MoveWindow(hwnd,widget.rect().x(),widget.rect().y(),widget.rect().width(),widget.rect().height(),True)
                    
            except:
                QMessageBox.warning(self,self.tr("Error"),
                     self.tr("Please Choose the Path"))

        elif(self.listWidget_2.currentRow()==1):
            try: 
                temp = self.slotOpenFile()
                if temp != -1:
                    [self.data_x1,self.data_y1] = temp
                
                curveWidget = CurveDialog(edit=False, toolbar=True, 
                      options=dict(xlabel="xlabel", ylabel="ylabel"))
                plot = curveWidget.get_plot()
                self.add_tab(curveWidget, title =u'spectrum_dark')
                curve = make.curve(self.data_x1, self.data_y1, color="b")
                plot.add_item(curve)
            except:
                pass
        #QMessageBox.information(self,"Information",
        #                self.tr("填写任意想告诉于用户的信息!"))
        elif(self.listWidget_2.currentRow()==2):
            
            try:            
                temp = self.slotOpenFile()
                if temp != -1:
                    [self.data_x2,self.data_y2] = temp

                curveWidget = CurveDialog(edit=False, toolbar=True, 
                      options=dict(xlabel="xlabel", ylabel="ylabel"))
                plot = curveWidget.get_plot()
                self.add_tab(curveWidget, title =u'spectrum_reference')
                curve = make.curve(self.data_x2, self.data_y2, color="b")
                plot.add_item(curve)
                
            except:
                pass
        elif(self.listWidget_2.currentRow()==3):
            try:            
                temp = self.slotOpenFile()
                if temp != -1:
                    [self.data_x3,self.data_y3] = temp 
                
                curveWidget = CurveDialog(edit=False, toolbar=True, 
                      options=dict(xlabel="xlabel", ylabel="ylabel"))
                plot = curveWidget.get_plot()
                self.add_tab(curveWidget, title =u'spectrum_signal')
                curve = make.curve(self.data_x3, self.data_y3, color="b")
                plot.add_item(curve)
            except:
                pass


        elif(self.listWidget_2.currentRow()==4):
            [data_x,data_y,data_x,var,data_x_temp,data_y_temp,data_x_smooth,data_y_smooth,peak_x,peak_y]=slotTest2DataProcess(self.data_x1,self.data_y1,self.data_x2,self.data_y2,self.data_x3,self.data_y3)
            
            if peak_x!=[]:
                for i in range(len(peak_x)):
                    self.listWidget_result.addItem(u"λ%i=%.3f"%(i+1,peak_x[i]))
                    self.listWidget_result.addItem(u"A%i=%.3f"%(i+1,peak_y[i])) 
                    
            #画出方差随波长的变化情况
            curveWidget = CurveDialog(edit=False, toolbar=True, 
                      options=dict(xlabel="xlabel", ylabel="ylabel"))
            plot = curveWidget.get_plot()
            self.add_tab(curveWidget, title =u'Various')
            curve = make.curve(data_x, var, color="b")
            plot.add_item(curve)
            
            #显示吸光度曲线
            curveWidget = CurveDialog(edit=False, toolbar=True, 
                     options=dict(xlabel="xlabel", ylabel="ylabel"))
            plot = curveWidget.get_plot()
            self.add_tab(curveWidget, title =u'absorbers')
            curve = make.curve(data_x_temp, data_y_temp, color="g")
            plot.add_item(curve)
            
             #平滑后的曲线
            curve = make.curve(data_x_smooth, data_y_smooth, color="r")
            plot.add_item(curve)   
#            print peak_x
#            print valley_x
            
            #标记出峰和谷的位置
            for i in range(min(len(peak_x),len(peak_y))):
                point = make.marker(position=(peak_x[i], peak_y[i]),color='r',markerfacecolor='r',markeredgecolor='r')
                plot.add_item(point)
            
        elif(self.listWidget_2.currentRow()==5):
            #设置文件处理间隔,默认间隔4，而且默认导入TE偏振数据
            self.procFileGap=1
            self.fileSaveGap=1
            self.flag=True
            title=["please load TE polarized data","please load TM polarized data"]
            dialog_setNum=codeDialog_setNum(title[0])
            if dialog_setNum.exec_():
                if dialog_setNum.lineEdit_1.text()!="" and dialog_setNum.lineEdit_2.text()!="":
                    self.fileSaveGap=int(dialog_setNum.lineEdit_1.text())
                    self.procFileGap=int(dialog_setNum.lineEdit_2.text())
                dialog_setNum.destroy()
            else:
                dialog_setNum=codeDialog_setNum(title[1])
                if dialog_setNum.exec_():
                    if dialog_setNum.lineEdit_1.text()!="" and dialog_setNum.lineEdit_2.text()!="":
                        self.fileSaveGap=int(dialog_setNum.lineEdit_1.text())
                        self.procFileGap=int(dialog_setNum.lineEdit_2.text())
                    dialog_setNum.destroy() 
                self.flag=False
            try:
                f=open("directory.txt")
    #        if peak_x!=[]:
#            for i in range(len(peak_x)):
#                self.listWidget_result.addItem(u"λ%i=%.3f"%(i+1,peak_x[i]))
#                self.listWidget_result.addItem(u"A%i=%.3f"%(i+1,peak_y[i])) 
                directory,filename = os.path.split(f.readline())
                path=QFileDialog.getExistingDirectory(self,directory=directory)
            except:
                path=QFileDialog.getExistingDirectory(self)
            
            self.lock=QReadWriteLock()
            self.threadForProcessData = threadForProcessData.ThreadForProcessData(self.lock,self)
            # self.connect(self.threadForProcessData, SIGNAL("indexed(QString)"),self.indexed)
            # self.connect(self.threadForProcessData, SIGNAL("processed(QString)"),self.processed)
            # self.connect(self.threadForProcessData, SIGNAL("finished(QString)"),self.finished)
            
            self.threadForProcessData.initialize(unicode(path),self.procFileGap)
            self.threadForProcessData.start() 
            
        elif(self.listWidget_2.currentRow()==6):
            pass

    def slot_test25(self):
        print("slot_test2 is actived")
        if (self.listWidget_25.currentRow() == 0):
            try:
                self.statusBar().showMessage(self.tr("Open Spectra Suite..."))
                with open('path.json', 'r') as file_obj:
                    path_list = json.load(file_obj)
                    path2 = path_list[1]
                    print(path2)
                directory, filename = os.path.split(path2)
                import win32process

                win32process.CreateProcess(path2, '', None, None, 0, win32process.REALTIME_PRIORITY_CLASS,
                                           None, directory, win32process.STARTUPINFO())
                print('ss opening..')

                widget = QWidget()
                self.add_tab(widget, title=u'Spectra Suite')
                import win32gui
                # QThread.sleep(5)
                sleep(5)
                start1 = time()
                hwnd = win32gui.FindWindow(None, u"Ocean Optics SpectraSuite ")
                while hwnd == 0:
                    hwnd = win32gui.FindWindow(None, u"Ocean Optics SpectraSuite ")
                    sleep(0.5)
                    end1 = time()
                    if end1 - start1 > 10:
                        QMessageBox.warning(self, self.tr("Error"),
                                            self.tr("Didn't find the process"))
                        break
                # finding_time=end1-start1
                # print(finding_time)
                win32gui.SetParent(hwnd, int(widget.winId()))
                win32gui.MoveWindow(hwnd, widget.rect().x(), widget.rect().y(), widget.rect().width(),
                                    widget.rect().height(), True)
                # f = open('path.txt')
                # path2 = f.readline()
                # path2 = f.readline()
                # #去除换行符‘\n’
                # path2=path2[0:-1]
                # if path2.split('::')[0]=='path2':
                #     path2=path2.split('::')[1]
                #     print(path2)
                #     directory,filename = os.path.split(path2)
                #     import win32process
                #
                #     win32process.CreateProcess(path2, '', None , None , 0 , win32process. REALTIME_PRIORITY_CLASS ,
                #                                None , directory, win32process.STARTUPINFO())
                #     print('ss opening..')
                #
                #     widget=QWidget()
                #     self.add_tab(widget,title=u'Spectra Suite')
                #     import win32gui
                #     #QThread.sleep(5)
                #     sleep(5)
                #     start1=time()
                #     hwnd=win32gui.FindWindow(None,u"Ocean Optics SpectraSuite ")
                #     while hwnd==0:
                #         hwnd=win32gui.FindWindow(None,u"Ocean Optics SpectraSuite ")
                #         sleep(0.5)
                #         end1 = time()
                #         if end1 - start1 > 10:
                #             QMessageBox.warning(self, self.tr("Error"),
                #                                 self.tr("Didn't find the process"))
                #             break
                #     # finding_time=end1-start1
                #     # print(finding_time)
                #     win32gui.SetParent(hwnd,int(widget.winId()))
                #     win32gui.MoveWindow(hwnd,widget.rect().x(),widget.rect().y(),widget.rect().width(),widget.rect().height(),True)

            except:
                QMessageBox.warning(self, self.tr("Error"),
                                    self.tr("Please Choose the Path"))
        elif (self.listWidget_25.currentRow() == 1):  # draw & process
            widget24 = QWidget()
            self.add_tab(widget24, title=u"process spr spectrum")

            ###处理单个光谱文件####
            # 上侧布局
            open_bt24 = QPushButton("OPEN")
            path_edit24 = QLineEdit()
            path_edit24.setPlaceholderText("file path displayed here")
            draw_bt24 = QPushButton("Draw")
            seek_deep_bt24 = QPushButton("SeekDeep")

            label24 = QLabel("CAL PARM:(nm)")
            label24.setToolTip("Choose a section of wavelength to make fitting")
            parm_edit1 = QLineEdit()
            parm_edit1.setPlaceholderText("start")
            parm_edit1.setMaximumSize(50, 30)
            parm_edit2 = QLineEdit()
            parm_edit2.setPlaceholderText("end")
            parm_edit2.setMaximumSize(50, 30)

            # 下侧布局
            canvas24 = MyCanvas()
            ntb24 = NavigationToolbar(canvas24, parent=widget24)

            gridlayout = QGridLayout()
            gridlayout.addWidget(open_bt24, 0, 0)
            gridlayout.addWidget(path_edit24, 0, 1, 1, 2)
            gridlayout.addWidget(draw_bt24, 0, 3)
            gridlayout.addWidget(seek_deep_bt24, 0, 4)
            gridlayout.addWidget(label24, 1, 0)
            gridlayout.addWidget(parm_edit1, 1, 1)
            gridlayout.addWidget(parm_edit2, 1, 2)

            hlayout24 = QHBoxLayout()
            hlayout24.addStretch()
            hlayout24.addLayout(gridlayout)
            hlayout24.addStretch()

            vlayout24 = QVBoxLayout(widget24)
            vlayout24.addSpacing(20)
            vlayout24.addLayout(hlayout24)
            vlayout24.addWidget(canvas24)
            vlayout24.addWidget(ntb24)

            open_bt24.clicked.connect(lambda: self.open_spectrum(path_edit24, canvas24))
            draw_bt24.clicked.connect(lambda: self.draw_spectrum(path_edit24, parm_edit1, parm_edit2, canvas24, 0))
            seek_deep_bt24.clicked.connect(lambda: self.draw_spectrum(path_edit24, parm_edit1, parm_edit2, canvas24, 1))
        elif (self.listWidget_25.currentRow() == 2):
            widget25 = QWidget()
            self.add_tab(widget25, title=u"Ad/de-sorption spectrums")

            ###处理单个光谱文件####
            # 上侧布局
            open_bt25 = QPushButton("OPEN")
            path_edit25 = QLineEdit()
            path_edit25.setPlaceholderText("folder path displayed here")
            draw_bt25 = QPushButton("Draw")

            # 第二排局部
            label251 = QLabel("Sampling interval (s):")
            edit251 = QLineEdit()
            edit251.setText('0.1')
            edit251.setMaximumWidth(60)

            # label252=QLabel("Fit area")
            # edit252=QLineEdit()
            #
            # edit253=QLineEdit()

            # 下侧布局
            canvas25 = MyCanvas()
            ntb25 = NavigationToolbar(canvas25, parent=widget25)

            # 第一排
            hlayout25 = QHBoxLayout()
            hlayout25.addStretch()
            hlayout25.addWidget(open_bt25)
            hlayout25.addWidget(path_edit25)
            hlayout25.addWidget(draw_bt25)
            hlayout25.addStretch()

            # 第二排
            hlayout251 = QHBoxLayout()
            hlayout251.addStretch()
            hlayout251.addWidget(label251)
            hlayout251.addWidget(edit251)
            hlayout251.addStretch()

            # 第三排
            label252 = QLabel("Selection:")
            start_edit = QLineEdit()
            end_edit = QLineEdit()
            start_edit.setMaximumWidth(60)
            end_edit.setMaximumWidth(60)
            fit1_bt = QPushButton("Ad-Fit")
            fit2_bt = QPushButton("De-Fit")

            hlayout252 = QHBoxLayout()
            hlayout252.addStretch()
            hlayout252.addWidget(label252)
            hlayout252.addWidget(start_edit)
            hlayout252.addWidget(end_edit)
            hlayout252.addWidget(fit1_bt)
            hlayout252.addWidget(fit2_bt)
            hlayout252.addStretch()

            # 垂直布局
            vlayout24 = QVBoxLayout(widget25)
            vlayout24.addSpacing(20)
            vlayout24.addLayout(hlayout25)
            vlayout24.addLayout(hlayout251)
            vlayout24.addLayout(hlayout252)
            vlayout24.addWidget(canvas25)
            vlayout24.addWidget(ntb25)

            open_bt25.clicked.connect(lambda: self.open_spectrums(path_edit25, canvas25))
            draw_bt25.clicked.connect(lambda: self.draw_spectrums(path_edit25, canvas25, edit251))
            fit1_bt.clicked.connect(lambda: self.adsorption_fit(path_edit25, start_edit, end_edit, canvas25))
            fit2_bt.clicked.connect(lambda: self.desorption_fit(path_edit25, start_edit, end_edit, canvas25))
        elif (self.listWidget_25.currentRow() == 3):
            widget253 = QWidget()
            self.add_tab(widget253, title=u"Calculate thickness")
            self.calc_thickness()


    def open_spectrums(self, edit, canvas): #打开文件夹，计算文件夹内所有光谱共振峰
        foldername=QFileDialog.getExistingDirectory(self,"choose folder",'./')
        print(foldername)
        if not foldername:
            return
        edit.setText(foldername)

        canvas.ax.clear()
        canvas.draw()


    def draw_spectrums(self, edit, canvas,edit251):
        if not edit.text():
            return
        foldername=edit.text()
        # print(foldername.split('/')[-1])
        file_list=[]
        for parent,dirs,files in os.walk(foldername):
            for file in sorted(files):
                if file.endswith(".txt"):
                    file_list.append(file)
        # print(file_list)
        n = len(file_list)
        if edit251.text():
            try:
                a=float(edit251.text())
                n_list = [round(i*a,1) for i in range(n)]  #每一个数据采集的间隔时间是？
            except:
                pass
        #print(n_list)
        resonance_wavelength = []

        progressdialog=QProgressDialog(self)
        progressdialog.setWindowTitle('Please wait')
        progressdialog.setWindowModality(Qt.WindowModal)
        progressdialog.setLabelText('processing...')
        progressdialog.setRange(0,n)
        progressdialog.show()
        i=0
        for file in file_list:
            i=i+1
            print(i)
            progressdialog.setValue(i)
            resonance_wavelength.append(visual_data(read_data(foldername,'\t',file))[2])
        # x -- n_list
        # y -- resonance_wavelength
        ################################相同的y值只要第一个
        # y_values=[]
        # x_values=[]
        # for i in range(0,len(n_list)):
        #     if resonance_wavelength[i] in y_values:
        #         pass
        #     else:
        #         y_values.append(resonance_wavelength[i])
        #         x_values.append(n_list[i])
        # n_list=x_values
        # resonance_wavelength=y_values

        ###################################
        my_prefix=foldername.split('/')[-1]
        with open('temp_x_'+my_prefix+'.json', 'w') as file_obj:
            json.dump(n_list,file_obj)
        with open('temp_y_'+my_prefix+'.json', 'w') as file_obj:
            json.dump(resonance_wavelength,file_obj)
        canvas.ax.clear()
        canvas.ax.scatter(n_list,resonance_wavelength,s=3)
        canvas.draw()


    def adsorption_fit(self,path_edit,start_edit,end_edit,canvas): #
        x_data=[]
        y_data=[]
        my_prefix = path_edit.text().split('/')[-1]
        with open('temp_x_'+my_prefix+'.json','r') as file_obj:
            x_data=json.load(file_obj)
        with open('temp_y_'+my_prefix+'.json','r') as file_obj:
            y_data=json.load(file_obj)
        try:
            # print(x_data)
            # print(y_data)
            start_value=float(start_edit.text())
            end_value=float(end_edit.text())
            temp=cut_list(x_data,start_value,end_value)
            x1_data=x_data[temp[0]:temp[1]]
            x_data=[i-x1_data[0] for i in x1_data] #x是时间，因此需要从0开始
            y_data=y_data[temp[0]:temp[1]]  #根据需求截取，从而进行后面的拟合

            # 吸附
            def func(x,N0,tao):
                return N0*(1-np.exp(-x/tao))

            n0=1
            y1=[y_data[i] for i in range(0,len(y_data),n0) ] #每隔三个取一个点
            x=[x_data[i] for i in range(0,len(x_data),n0)]
            y=[i-y1[0] for i in y1]
            popt, pcov = curve_fit(func, x, y)
            fitted_y = [func(i, popt[0], popt[1])  for i in x]
            canvas.ax.clear()
            canvas.myplot(x, fitted_y)
            canvas.ax.scatter(x, y, s=2)
            # canvas.fig.text(0.3, 0.2, str(round(popt[0], 2)) + "*(1-e^(-t/" + str(round(popt[1], 2)) + "))")
            canvas.ax.text(x[10],y[1],str(round(popt[0], 2)) + "*(1-e^(-t/" + str(round(popt[1], 2)) + "))",size=15)
            canvas.draw()

        except:
            pass

    def desorption_fit(self,path_edit,start_edit,end_edit,canvas): #
        x_data = []
        y_data = []
        my_prefix=path_edit.text().split('/')[-1]
        with open('temp_x_'+my_prefix+'.json', 'r') as file_obj:
            x_data = json.load(file_obj)
        with open('temp_y_'+my_prefix+'.json', 'r') as file_obj:
            y_data = json.load(file_obj)
        try:
            # print(x_data)
            # print(y_data)
            start_value = float(start_edit.text())
            end_value = float(end_edit.text())
            temp = cut_list(x_data, start_value, end_value)

            if temp[1]==-1:
                x1_data=x_data[temp[0]:]
                y_data = y_data[temp[0]:]  # 根据需求截取，从而进行后面的拟合

            else:
                x1_data = x_data[temp[0]:temp[1]+1]
                y_data = y_data[temp[0]:temp[1]+1]  # 根据需求截取，从而进行后面的拟合

            x_data = [i - x1_data[0] for i in x1_data]  # x是时间，因此需要从0开始

            # 脱附
            def fund(x,b,k):
                return b-k*x
            n0=1
            y1 = [y_data[i] for i in range(0, len(y_data), n0)]  # 每隔三个取一个点
            x = [x_data[i] for i in range(0, len(x_data) , n0)]
            y2 = [i - y1[-1] for i in y1]


            y_2=[]
            x_2=[]
            for i in range(0,len(y2)):
                if y2[i]>0:
                    y_2.append(y2[i])
                    x_2.append(x[i])
            x=x_2
            y=[]
            for i in y_2:
                y.append(math.log(i,math.e))
            popt, pcov = curve_fit(fund, x, y)
            fitted_y = [fund(i, popt[0], popt[1])  for i in x]
            canvas.ax.clear()
            canvas.myplot(x,fitted_y)
            canvas.ax.scatter(x,y,s=2)
            #canvas.fig.text(0.3,0.2, str(round(popt[0],2))+"-x*"+str(round(popt[1],2)) )
            canvas.ax.text(x[0],y[-1],str(round(popt[0],2))+"-x*"+str(round(popt[1],2)),size=15 )
            canvas.draw()

        except:
            pass


    def open_spectrum(self,edit,canvas): #包含打开拉曼(trt)和spr光谱(jdx,txt)
        filename=QFileDialog.getOpenFileName(self,"Open file",'',"*.txt *.trt",None,QFileDialog.DontUseNativeDialog)
        if not filename[0]:
            return
        edit.setText(filename[0])
        canvas.ax.clear()
        canvas.draw()

    def draw_spectrum(self,edit,parm_edit1,parm_edit2,canvas,flag): #画spr光谱,flag=0只画，flag=1还标注deep
        if edit.text():
            path=edit.text()
            if path.split('.')[-1]!='txt':
                return
            if parm_edit1.text() and parm_edit2.text():
                try:
                    a1=int(parm_edit1.text())
                    a2=int(parm_edit2.text())
                    data=visual_data(read_data(path,'\t'),(a1,a2))

                except:
                    return
            else:
                data=visual_data(read_data(path,'\t'))
            if data[2]==0 or flag==0:
                canvas.ax.clear()
                canvas.myplot(data[0], data[1])
                canvas.ax.set_xlabel("Wavelength($nm$)")
                canvas.draw()
                if flag==1:
                    QMessageBox.warning(self, self.tr("Error"),self.tr("No deep found"))
            else:
                # if flag==0:
                #     canvas.ax.clear()
                #     canvas.myplot(data[0],data[1])
                if flag==1:
                    canvas.ax.axvline(data[2],c='red',alpha=0.5)
                    canvas.ax.text(500 , 0.2, "resonance wavelength="+str(data[2])+"nm")
                    # canvas.fig.text(0.2,0.25,"resonance wavelength="+str(data[2])+"nm")
            canvas.ax.set_xlabel("Wavelength($nm$)")
            canvas.draw()

        else:
            pass




    def slot_test3(self):
        print("slot_test3 is actived")
        #dataProcess = Mymath.dataProcess()
        if (self.listWidget_3.currentRow()==0):
            try:
                self.statusBar().showMessage("Open AvaRaman...")
                with open('path.json','r') as file_obj:
                    path_list=json.load(file_obj)
                    path3=path_list[2]
                    print(path3)
                directory, filename = os.path.split(path3)
                import win32process
                win32process.CreateProcess(path3, '', None, None, 0,
                                           win32process.REALTIME_PRIORITY_CLASS,
                                           None, directory, win32process.STARTUPINFO())

                widget = QWidget()
                self.add_tab(widget, title=u'AvaRaman')
                import win32gui
                QThread.sleep(3)
                start1 = time()
                hwnd1 = win32gui.FindWindow(None, u"AvaSoft?7.6.1 Raman - 2011 Avantes - S/N: 1202042U1")  #usb
                hwnd2 = win32gui.FindWindow(None, u"AvaSoft?7.6.1 Raman - 2011 Avantes - S/N: SimChan_0")   #仿真模式
                while hwnd1 or hwnd2 == 0:
                    hwnd1 = win32gui.FindWindow(None, u"AvaSoft?7.6.1 Raman - 2011 Avantes - S/N: 1202042U1")
                    hwnd2 = win32gui.FindWindow(None, u"AvaSoft?7.6.1 Raman - 2011 Avantes - S/N: SimChan_0")
                    sleep(0.5)
                    end1 = time()
                    if end1 - start1 > 10:
                        QMessageBox.warning(self, self.tr("Error"),
                                            self.tr("Didn't find the process"))
                        break
                if hwnd1:
                    win32gui.SetParent(hwnd1, int(widget.winId()))
                    win32gui.MoveWindow(hwnd1, widget.rect().x(), widget.rect().y(), widget.rect().width(),
                                    widget.rect().height(), True)
                elif hwnd2:
                    win32gui.SetParent(hwnd2, int(widget.winId()))
                    win32gui.MoveWindow(hwnd2, widget.rect().x(), widget.rect().y(), widget.rect().width(),
                                        widget.rect().height(), True)
            #
            #     f = open('path.txt')
            #     path3 = f.readline()
            #     path3 = f.readline()
            #     path3 = f.readline()
            #     #去除末尾的‘\n’
            #     path3=path3[0:-1]
            #     if path3.split('::')[0]=='path3':
            #         path3=path3.split('::')[1]
            #         print(path3)
            #         directory,filename = os.path.split(path3)
            #         import win32process
            #         win32process.CreateProcess(path3, '', None , None , 0 ,
            #                                    win32process. REALTIME_PRIORITY_CLASS ,
            #                                    None , directory, win32process.STARTUPINFO())
            #
            #         widget=QWidget()
            #         self.add_tab(widget,title=u'AvaRaman')
            #         import win32gui
            #         QThread.sleep(1)
            #         start1 = time()
            #         hwnd=win32gui.FindWindow(None,u"AvaSoft?7.6.1 Raman - 2011 Avantes - S/N: 1202042U1")
            #         while hwnd==0:
            #             hwnd=win32gui.FindWindow(None,u"AvaSoft?7.6.1 Raman - 2011 Avantes - S/N: 1202042U1")
            #             sleep(0.5)
            #             end1 = time()
            #             if end1 - start1 > 10:
            #                 QMessageBox.warning(self, self.tr("Error"),
            #                                     self.tr("Didn't find the process"))
            #                 break
            #         win32gui.SetParent(hwnd,int(widget.winId()))
            #         win32gui.MoveWindow(hwnd,widget.rect().x(),widget.rect().y(),widget.rect().width(),widget.rect().height(),True)
            except:
                QMessageBox.warning(self,self.tr("Error"),
                     self.tr("Please Choose the Path"))
        elif (self.listWidget_3.currentRow()==1):
            pass
        elif (self.listWidget_3.currentRow()==2): #process 处理拉曼光谱，基线校正，平滑滤波，人工寻峰标记
            widget32=QWidget()
            self.add_tab(widget32,title=u"process raman")
            open_bt32 = QPushButton("Open")
            path_edit32 = QLineEdit()
            draw_bt32 = QPushButton("Draw")
            path_edit32.setPlaceholderText("file path displayed here")


            label32=QLabel("fc:")
            label32.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            # label32.setStyleSheet("border:1px solid red")
            label32.setToolTip("the normalized cut-off frequency when using low-pass filter")
            slider32=QSlider(Qt.Horizontal)
            slider32.setMinimum(0)
            slider32.setMaximum(100) # 具体操作时要除以100
            slider32.setValue(35)
            slider32.setSingleStep(5)
            slider32.setTickInterval(10)
            slider32.setTickPosition(QSlider.TicksAbove)

            #selection布局
            label321=QLabel("Selection:")
            label321.setToolTip("Select a section of data to process")
            start_edit=QLineEdit()
            start_edit.setMaximumSize(50,30)
            end_edit=QLineEdit()
            end_edit.setMaximumSize(50,30)
            process_btn=QPushButton("Detrend/Smooth")


            canvas32=MyCanvas()
            ntb32=NavigationToolbar(canvas32,parent=widget32)

            gridlayout32=QGridLayout()
            gridlayout32.addWidget(open_bt32,0,0)
            gridlayout32.addWidget(path_edit32,0,1,1,2)
            gridlayout32.addWidget(draw_bt32,0,3)
            gridlayout32.addWidget(label32,0,4)
            gridlayout32.addWidget(slider32,0,5,1,2)
            gridlayout32.addWidget(label321,1,0)
            gridlayout32.addWidget(start_edit,1,1)
            gridlayout32.addWidget(end_edit,1,2)
            gridlayout32.addWidget(process_btn,1,3)

            hlayout32=QHBoxLayout()
            hlayout32.addStretch()
            hlayout32.addLayout(gridlayout32)
            hlayout32.addStretch()

            vlayout32=QVBoxLayout(widget32)
            vlayout32.addSpacing(20)
            vlayout32.addLayout(hlayout32)
            # vlayout32.addLayout(hlayout32)
            # vlayout32.addLayout(hlayout321)
            vlayout32.addWidget(canvas32)
            vlayout32.addWidget(ntb32)


            open_bt32.clicked.connect(lambda: self.open_spectrum(path_edit32,canvas32))
            draw_bt32.clicked.connect(lambda: self.draw_raman(path_edit32,canvas32,slider32,start_edit,end_edit))
            process_btn.clicked.connect(lambda :self.draw_raman(path_edit32,canvas32,slider32,start_edit,end_edit))



        elif (self.listWidget_3.currentRow()==3):
            pass
    def draw_raman(self,edit,canvas,slider,start_edit,end_edit):
        if edit.text():
            path=edit.text()
            if path.split('.')[-1]!='trt':
                return
            if start_edit.text() and end_edit.text():
                try:
                    a1=int(start_edit.text())
                    a2=int(end_edit.text())
                    if a1>=a2:
                        print("invalid input")
                        return
                    data=raman_read(path,slider.value()/100,(a1,a2))
                    canvas.ax.clear()
                    canvas.ax.set_xlabel("Raman shift($cm^{-1}$)")
                    canvas.myplot(data[0],data[1])
                    canvas.draw()
                except:
                    return
            else:
                data = raman_read(path)
                canvas.ax.clear()
                canvas.ax.set_xlabel("Raman shift($cm^{-1}$)")
                canvas.myplot(data[0], data[1])
                canvas.draw()
        else:
            pass


    def slot_test4(self):
        print("slot_test4 is actived")
        #dataProcess = Mymath.dataProcess()
        if (self.listWidget_4.currentRow()==0):
            try:
                self.statusBar().showMessage("Open GamryFramework...")
                with open('path.json','r') as file_obj:
                    path_list=json.load(file_obj)
                    path4=path_list[3]
                    print(path4)
                directory, filename = os.path.split(path4)
                import win32process
                win32process.CreateProcess(path4, '', None, None, 0,
                                           win32process.REALTIME_PRIORITY_CLASS,
                                           None, directory, win32process.STARTUPINFO())

                widget = QWidget()
                self.add_tab(widget, title=u'Gamry Framework')
                import win32gui
                QThread.sleep(1)
                start1 = time()
                hwnd = win32gui.FindWindow(None, u"Gamry Instruments Framework")
                while hwnd == 0:
                    hwnd = win32gui.FindWindow(None, u"Gamry Instruments Framework")
                    sleep(0.5)
                    end1 = time()
                    if end1 - start1 > 10:
                        QMessageBox.warning(self, self.tr("Error"),
                                            self.tr("Didn't find the process"))
                        break
                win32gui.SetParent(hwnd, int(widget.winId()))
                win32gui.MoveWindow(hwnd, widget.rect().x(), widget.rect().y(), widget.rect().width(),
                                    widget.rect().height(), True)
                # f = open('path.txt')
                # path4 = f.readline()
                # path4 = f.readline()
                # path4 = f.readline()
                # path4 = f.readline()
                # #去除末尾的‘\n’
                # path4=path4[0:-1]
                # if path4.split('::')[0]=='path4':
                #     path4=path4.split('::')[1]
                #     directory,filename = os.path.split(path4)
                #     import win32process
                #     win32process.CreateProcess(path4, '', None , None , 0 ,
                #                                win32process. REALTIME_PRIORITY_CLASS ,
                #                                None , directory, win32process.STARTUPINFO())
                #
                #     widget=QWidget()
                #     self.add_tab(widget,title=u'Gamry Framework')
                #     import win32gui
                #     QThread.sleep(1)
                #     hwnd=win32gui.FindWindow(None,u"Gamry Instruments Framework")
                #     while hwnd==0:
                #         hwnd=win32gui.FindWindow(None,u"Gamry Instruments Framework")
                #     win32gui.SetParent(hwnd,int(widget.winId()))
                #     win32gui.MoveWindow(hwnd,widget.rect().x(),widget.rect().y(),widget.rect().width(),widget.rect().height(),True)
            except:
                QMessageBox.warning(self,self.tr("Error"),
                     self.tr("Please Choose the Path"))
        elif (self.listWidget_4.currentRow()==1):
            try:
                self.statusBar().showMessage("Open EchemAnalyst...")
                with open('path.json','r') as file_obj:
                    path_list=json.load(file_obj)
                    path5=path_list[4]
                    print(path5)
                directory, filename = os.path.split(path5)
                import win32process
                win32process.CreateProcess(path5, '', None, None, 0,
                                           win32process.REALTIME_PRIORITY_CLASS,
                                           None, directory, win32process.STARTUPINFO())

                widget = QWidget()
                self.add_tab(widget, title=u'Echem Analyst')
                import win32gui
                QThread.sleep(1)
                start1 = time()
                hwnd = win32gui.FindWindow(None, u"Gamry Echem Analyst")
                while hwnd == 0:
                    hwnd = win32gui.FindWindow(None, u"Gamry Echem Analyst")
                    sleep(0.5)
                    end1 = time()
                    if end1 - start1 > 10:
                        QMessageBox.warning(self, self.tr("Error"),
                                            self.tr("Didn't find the process"))
                        break
                win32gui.SetParent(hwnd, int(widget.winId()))
                win32gui.MoveWindow(hwnd, widget.rect().x(), widget.rect().y(), widget.rect().width(),
                                    widget.rect().height(), True)

                # f = open('path.txt')
                # path5 = f.readline()
                # path5 = f.readline()
                # path5 = f.readline()
                # path5 = f.readline()
                # path5 = f.readline()
                # #去除末尾的‘\n’
                # path5=path5[0:-1]
                # if path5.split('::')[0]=='path5':
                #     path5=path5.split('::')[1]
                #     directory,filename = os.path.split(path5)
                #     import win32process
                #     win32process.CreateProcess(path5, '', None , None , 0 ,
                #                                win32process. REALTIME_PRIORITY_CLASS ,
                #                                None , directory, win32process.STARTUPINFO())
                #
                #     widget=QWidget()
                #     self.add_tab(widget,title=u'Echem Analyst')
                #     import win32gui
                #     QThread.sleep(1)
                #     hwnd=win32gui.FindWindow(None,u"Gamry Echem Analyst")
                #     while hwnd==0:
                #         hwnd=win32gui.FindWindow(None,u"Gamry Echem Analyst")
                #     win32gui.SetParent(hwnd,int(widget.winId()))
                #     win32gui.MoveWindow(hwnd,widget.rect().x(),widget.rect().y(),widget.rect().width(),widget.rect().height(),True)
            except:
                QMessageBox.warning(self,self.tr("Error"),
                     self.tr("Please Choose the Path"))
        elif (self.listWidget_4.currentRow()==2):
            pass
        elif (self.listWidget_4.currentRow()==3):
            pass
        elif (self.listWidget_4.currentRow()==4):
            pass
    def slot_test5(self):
        print("slot_test5 is actived")
        #dataProcess = Mymath.dataProcess()
        if (self.listWidget_5.currentRow()==0):
            try:
                self.statusBar().showMessage("Open Camera...")
                with open('path.json','r') as file_obj:
                    path_list=json.load(file_obj)
                    path6=path_list[5]
                    print(path6)
                import win32process
                win32process.CreateProcess(path6, '', None, None, 0,
                                           win32process.REALTIME_PRIORITY_CLASS,
                                           None, None, win32process.STARTUPINFO())
                widget = QWidget()
                self.add_tab(widget, title=u'Camera')  # 此函数返回的是当前添加的标签页的index

                # close..connect(win32process.TerminateProcess(subprocess,0))
                import win32gui
                QThread.sleep(3)
                start1 = time()
                hwnd = win32gui.FindWindow(None, u"S-gauge")
                # 通过任务管理器查看程序的句柄名称
                while hwnd == 0:
                    hwnd = win32gui.FindWindow(None, u"S-gauge")
                    sleep(0.5)
                    end1 = time()
                    if end1 - start1 > 10:
                        QMessageBox.warning(self, self.tr("Error"),
                                            self.tr("Didn't find the process"))
                        break
                win32gui.SetParent(hwnd, int(widget.winId()))
                win32gui.MoveWindow(hwnd, widget.rect().x(), widget.rect().y(), widget.rect().width(),
                                    widget.rect().height(), True)

                # with open('path.txt','r') as file_obj:
                #     lines = file_obj.readlines()
                #     exe_path = lines[6].split("::")[1].strip()
                # #去除末尾的‘\n’
                # print(exe_path)
                # # import win32process
                # import win32process
                # win32process.CreateProcess(exe_path, '', None , None , 0 ,
                #                            win32process. REALTIME_PRIORITY_CLASS ,
                #                            None , None, win32process.STARTUPINFO())
                # widget=QWidget()
                # self.add_tab(widget,title=u'Camera')  #此函数返回的是当前添加的标签页的index
                #
                #
                # # close..connect(win32process.TerminateProcess(subprocess,0))
                # import win32gui
                # QThread.sleep(1)
                # hwnd=win32gui.FindWindow(None,u"CAM-MS测量软件")
                # # 通过任务管理器查看程序的句柄名称
                # while hwnd==0:
                #     hwnd=win32gui.FindWindow(None,u"CAM-MS测量软件")
                # win32gui.SetParent(hwnd,int(widget.winId()))
                # win32gui.MoveWindow(hwnd,widget.rect().x(),widget.rect().y(),widget.rect().width(),widget.rect().height(),True)
            except:
                QMessageBox.warning(self,self.tr("Error"),
                     self.tr("Please Choose the Path"))
        elif (self.listWidget_5.currentRow()==1):
            pass
        elif (self.listWidget_5.currentRow()==2): #process
            widget52 = QWidget()
            self.add_tab(widget52, title=u'process img')
            #此处的self是MainWindow
            #add_tab是MainWindow的自定义函数，其中调用了self.TabWidget的addTab函数

            pushbutton0 = QPushButton("Open Img")
            pushbutton1=QPushButton("Zoom In")
            pct_lineedit = QLineEdit()
            pushbutton2=QPushButton("Zoom Out")
            hue_button = QPushButton("Calc HUE")
            hue_lineedit = QLineEdit()
            enhance_button = QPushButton("Enhance")

            pushbutton0.setMaximumSize(80,50)
            pushbutton1.setMaximumSize(80, 50)
            pct_lineedit.setMaximumSize(80,50)
            pushbutton2.setMaximumSize(80,50)
            hue_button.setMaximumSize(80,50)
            hue_lineedit.setMaximumSize(80,50)
            enhance_button.setMaximumSize(80, 50)
            ## 左侧栏布局
            vlayout_52_left = QVBoxLayout()
            vlayout_52_left.addSpacing(10)
            vlayout_52_left.addWidget(pushbutton0)
            vlayout_52_left.addStretch(1)
            vlayout_52_left.addWidget(pushbutton1)
            vlayout_52_left.addWidget(pct_lineedit)
            vlayout_52_left.addWidget(pushbutton2)
            vlayout_52_left.addStretch(1)
            vlayout_52_left.addWidget(hue_button)
            vlayout_52_left.addWidget(hue_lineedit)
            vlayout_52_left.addStretch(1)
            vlayout_52_left.addWidget(enhance_button)
            vlayout_52_left.addSpacing(10)

            #右侧布局
            edit1 = QLineEdit('0')
            edit2 = QLineEdit('0')
            edit3 = QLineEdit('0')
            edit4 = QLineEdit('0')
            edit1.setAlignment(Qt.AlignCenter)
            edit2.setAlignment(Qt.AlignCenter)
            edit3.setAlignment(Qt.AlignCenter)
            edit4.setAlignment(Qt.AlignCenter)
            select_bt = QPushButton('Select')
            cancel_bt = QPushButton('Cancel')
            cut_bt = QPushButton('Cut/Save')

            # 右上角布局
            hlayout_52_rt = QHBoxLayout()
            hlayout_52_rt.addStretch(3)
            hlayout_52_rt.addWidget(edit1,stretch=1)
            hlayout_52_rt.addWidget(edit2,stretch=1)
            hlayout_52_rt.addWidget(edit3,stretch=1)
            hlayout_52_rt.addWidget(edit4,stretch=1)
            hlayout_52_rt.addWidget(select_bt,stretch=1)
            hlayout_52_rt.addWidget(cancel_bt,stretch=1)
            hlayout_52_rt.addWidget(cut_bt,stretch=1)
            hlayout_52_rt.addStretch(3)

            label0 = MyLabel()
            # label0.setStyleSheet("border:2px solid grey;")
            # pixmap = QPixmap()
            image_scroll_area = myWidgetScrollArea()
            image_scroll_area.setMinimumSize(600,480)
            # image_scroll_area.setFixedSize(800,600)
            image_scroll_area.setWidget(label0)
            image_scroll_area.setAlignment(Qt.AlignCenter)
            # print(image_scroll_area.width()," -- ",image_scroll_area.height())


            #右侧布局
            vlayout_52_right = QVBoxLayout()
            vlayout_52_right.addLayout(hlayout_52_rt)
            vlayout_52_right.addWidget(image_scroll_area)
            #整体布局(参数为窗口)
            hlayout52_total=QHBoxLayout(widget52)
            hlayout52_total.addLayout(vlayout_52_left)
            hlayout52_total.addLayout(vlayout_52_right)

            #按钮信号连接
            pushbutton0.clicked.connect(lambda: self.open_img(label0, cancel_bt,image_scroll_area, pct_lineedit, hue_lineedit))
            pushbutton1.clicked.connect(lambda: self.zoom_in(label0, select_bt,image_scroll_area, pct_lineedit))
            pushbutton2.clicked.connect(lambda: self.zoom_out(label0, select_bt,image_scroll_area, pct_lineedit))
            hue_button.clicked.connect(lambda: self.calculate_hue(label0, hue_lineedit,edit1,edit2,edit3,edit4))  # 计算色相实际上是从源图片计算
            enhance_button.clicked.connect(lambda: self.process_image(label0, edit1, edit2, edit3, edit4))
            select_bt.clicked.connect(lambda :self.selection_functon(label0,edit1,edit2,edit3,edit4,1))
            cancel_bt.clicked.connect(lambda :self.selection_functon(label0,edit1,edit2,edit3,edit4,0))
            cut_bt.clicked.connect(lambda :self.cut_image(label0,edit1,edit2,edit3,edit4))

            label0.mySignal1.connect(lambda :self.set_size(label0,edit1,edit2,edit3,edit4))

            # label0.set_position.connect(lambda :edit1.setText('11'))
            # label0.set_position.connect(lambda :edit2.setText('22'))
            #


        elif (self.listWidget_5.currentRow()==3):
            pass

    # def slot_test51(self):
    #     print("slot_test51 is actived")
    #     clicked_row = self.listWidget_5.currentRow()
    #     print("clicked_row_number: ",clicked_row)
    #     if(clicked_row == 0):
    #         self.statusBar().showMessage("Open Image...")
    #         with open("path.txt",'r') as file_obj:
    #             lines = file_obj.readlines()
    #             exe_path = lines[7].split("::")[1].strip()
    #         print("exe_path: ",exe_path)
    #         import win32process
    #         path6 = exe_path
    #         # path6 = "G:/SOFTWARE/SmallSoft/FastStone Image Viewer/FSViewer.exe"
    #         handle=win32process.CreateProcess(path6, '', None, None, 0,
    #                                    win32process.REALTIME_PRIORITY_CLASS,
    #                                    None, None, win32process.STARTUPINFO())
    #
    #         widget51 = QWidget()
    #         self.add_tab(widget51, title=u'Image')
    #         print("index:",self.tabWidget.currentIndex())
    #         temp_index = self.tabWidget.currentIndex()
    #         self.tabWidget.tabCloseRequested.connect(lambda :self.test_func(temp_index,handle))
    #         #如何在关闭此标签页的时候调用函数关闭exe进程
    #         import win32gui
    #         QThread.sleep(1)
    #         hwnd = win32gui.FindWindow(None, u"FastStone Image Viewer 5.8")
    #         while hwnd == 0:
    #             print('-1-')
    #             hwnd = win32gui.FindWindow(None, u"FastStone Image Viewer 5.8")
    #         # print("-2-")
    #         win32gui.SetParent(hwnd, int(widget51.winId()))
    #         win32gui.MoveWindow(hwnd, widget51.rect().x(), widget51.rect().y(), widget51.rect().width(),
    #                             widget51.rect().height(), True)
    #
    #     else:
    #         pass

    # def mousePressEvent(self, event):
    #  print(event.pos())

    # def test_func(self,index,handle):
    #     print("--:",index)
    #     if index==1:
    #         # import win32process
    #         # win32process.TerminateProcess(handle[0],0)
    #         print("~~~~~~~~~~~~~~~~~~~~~~~~~test~~~~~")

    def set_size(self,label,edit1,edit2,edit3,edit4):  #将鼠标选择的区域显示在框里
        # print('yeaaaaaaaaaaahhhhh')
        new_x = label.x0 #根据鼠标滑动的四种方向，重新矫正选框左上角的坐标
        new_y = label.y0
        if label.w<0:
            new_x = label.x0+label.w
        if label.h<0:
            new_y = label.y0+label.h
        edit1.setText(str(int(new_x/label.ratio)))
        edit2.setText(str(int(new_y/label.ratio)))
        edit3.setText(str(abs(int(label.w/label.ratio)))) # 绝对值,比例
        edit4.setText(str(abs(int(label.h/label.ratio))))

    def cut_image(self,label,edit1,edit2,edit3,edit4):
        x1 = int(edit1.text())
        x2 = int(edit2.text())
        x3 = int(edit3.text())
        x4 = int(edit4.text())

        if x1 + x2 + x3 + x4 == 0:
            return
        original_image=Image.open(label.toolTip())
        box=(x1,x2,x1+x3,x2+x4)
        new_image=original_image.crop(box)
        # crop的四个参数分别上左上角的(x,y)和左下角的(x,y)，所以注意换算
        original_image=None
        filepath=QFileDialog.getSaveFileName(self,"save file","C:/Users/yintao/Desktop","*.png")
        # print(filepath)
        if not filepath[0]: #这一步必须有，防止取消保存导致的死机
            return
        new_image.save(filepath[0])

    def process_image(self, label, edit1, edit2, edit3, edit4):
        # path=str(label.toolTip())
        # enhance_image(path)
        # 如果没有建立选框，则计算的是整体图片的色相
        # 如果当下建立了选框，则计算的是选框部分的色相值

        if not label.pixmap():
            print('no image')
            return
        path = label.toolTip()  # 图片源地址
        # print(type(path),path)
        #path = str(path)  # 一定要把QSTRING转换成python的str后续才能读取
        # print(type(path),path)
        x1 = int(edit1.text())
        x2 = int(edit2.text())
        x3 = int(edit3.text())
        x4 = int(edit4.text())
        print(" -- ", x1, x2, x3, x4)
        if x1 + x2 + x3 + x4 == 0:  # 没有建立选框，框里的数值关系bug先不管,只要不乱数数字- -
            print('--yes--1')
            enhance_image(path)


        else:
            print('--1')
            enhance_image(path, x1, x2, x3, x4)
            print('--2')

    def selection_functon(self,label,edit1,edit2,edit3,edit4,flag):
        # painEvent不能传递参数，因此通过改变label属性来传递参数
        # 四个参数分别为：选区左上角的(x,y)以及选区的宽和高度
        #
        # 【注意】：我们看到的尺寸是标签大小label.width()，而实际尺寸是
        #                   图像大小label.pixmap().width()，这二者存在缩放比的关系
        #                   作画时，是在标签上作画，因此显示的矩形框应与实际的尺寸存在缩放比计算
        #                   这样才能保证缩放过程中选框选的是同一位置
        #                   在参数传递过程中，应完成此缩放比计算
        #                   但是在实际操作中，如裁剪、计算选区色相，由于是从源图片上操作的，所以对输入参数不需要变换
        w1=label.width()
        w2=label.pixmap().width()
        ratio=w1/w2
        x=[int(edit1.text()),int(edit2.text()),int(edit3.text()),int(edit4.text())]
        x=[a*ratio for a in x]
        if flag:
            label.x0=x[0]
            label.y0=x[1]
            label.w=x[2]
            label.h=x[3]
        else:
            label.x0 = 0
            label.y0 = 0
            label.w = 0
            label.h = 0
            edit1.setText('0')
            edit2.setText('0')
            edit3.setText('0')
            edit4.setText('0')
        label.repaint()
        #更新窗口，以使得新的paintevent触发

    def open_img(self,label,button,scroll_area,lineedit,lineedit2):
        filename = QFileDialog.getOpenFileName(self,"Open file",'',
                                               "Images(*.png *.jpg *.bmp)",None,QFileDialog.DontUseNativeDialog)
        if not filename[0]:
            return
        print(filename[0])
        #settings=QSettings('./Setting.ini',QSettings.IniFormat)
        #settings.setValue('saa',filename[0])

        pixmap = QPixmap(filename[0])
        w1=pixmap.width()
        h1=pixmap.height()
        w2=scroll_area.width()
        h2=scroll_area.height()
        print(w1," -- ",h1)
        print(w2," -- ",h2)
        # label.resize(pixmap.width(),pixmap.height())
        fit_size = self.fit_image(w1,h1,w2,h2)
        label.resize(fit_size[0],fit_size[1]) # 这里把label的尺寸设置为和
        # 图片一样的宽高比并且自适应于滚动区域的大小
        label.setPixmap(pixmap)
        # label.setStyleSheet("background-image:url(filename[0])")
        label.ratio=fit_size[0]/w1
        print("加载图片相对于原始尺寸时的缩放比例:",label.ratio)
        lineedit.setText(str( math.floor(100 * label.ratio)) + "%")
        lineedit2.setText(" ")
        label.setToolTip(filename[0])  # 将图片路径作为标签的tooltip内容，以便后续操作
        label.setScaledContents(True)

        button.click() #新打开一张图片时调用cancel_bt将label上的矩形框清除
        #  如何把前面的pixmap传递到后面的操作中？->直接访问label.pixmap()

    def zoom_in(self,label,button,scroll_area,lineedit): #放大
        print("zoom in + clicked")
        if not label.pixmap():
            print('no image')
            return
        zoomin_factor = 1.1
        new_width = label.width()*zoomin_factor
        new_height = label.height() * zoomin_factor
        if new_width<5*label.pixmap().width() and new_width< 5000 and new_height<5000:
            label.resize(new_width,new_height)
            # print(new_width,new_height)
            label.ratio = new_width / label.pixmap().width()
            lineedit.setText(str( math.floor(100 * label.ratio)) + "%")

        # print(label.toolTip())
        # 需限定放大倍数，不能无穷得放大下去，会死机的
        # 小图片用倍数限制，大图片用绝对像素值限制

        scroll_area.setAlignment(Qt.AlignCenter)
        scroll_area.setWidgetResizable(False)# 不加这一句的话，可能放大的时候不会出现滚动条
        label.setScaledContents(True)
        button.click()  # 缩放过程中保持矩形选框的一致性


    def zoom_out(self,label,button,scroll_area,lineedit): # 缩小
        print("zoom out - clicked")
        if not label.pixmap():
            print('no image')
            return
        zoomout_factor = 0.90
        new_width = label.width() * zoomout_factor
        new_height = label.height() * zoomout_factor
        label.resize(new_width, new_height)
        label.ratio = new_width / label.pixmap().width()
        lineedit.setText(str(math.floor(100 * label.ratio)) + "%")

        scroll_area.setAlignment(Qt.AlignCenter)
        scroll_area.setWidgetResizable(False)
        label.setScaledContents(True)
        button.click()

    def calculate_hue(self,label,lineedit,edit1,edit2,edit3,edit4):
        # 如果没有建立选框，则计算的是整体图片的色相
        # 如果当下建立了选框，则计算的是选框部分的色相值

        if not label.pixmap():
            print('no image')
            return
        path = label.toolTip() # 图片源地址
        print(path)
        x1=int(edit1.text())
        x2=int(edit2.text())
        x3=int(edit3.text())
        x4=int(edit4.text())
        print(" -- ",x1,x2,x3,x4)
        if x1+x2+x3+x4==0: # 没有建立选框，框里的数值关系bug先不管,只要不乱数数字- -
            average_hue=hue_of_image(path)
            print("HUE of the whole image is :", average_hue[0])
        else:
            print('--1')
            average_hue = hue_of_image(path,x1,x2,x3,x4)
            print('--2')
            print("HUE of the selected part is :", average_hue[0])
        lineedit.setText(str(average_hue[0]))
        draw_image(average_hue[1])



    def fit_image(self,w1,h1,w2,h2): # 加载图片的时候自适应滚动区域的大小
        if w1<w2 and h1<h2:
            return (w1,h1)
        else:  # 剩余三种情况，可以划分为两类
            if w1*h2>h1*w2: # 宽的比例更大，则以此比例作为缩放标准
                ratio=(w1/w2)
            else:    # 否则高的比例更大，则以高的比例为标准
                ratio=(h1/h2)
            print("加载时为缩小到滚动区域的比例为：", ratio)
            ratio=ratio*1.03 #这个因子是让图片与边框之间留点缝隙
            return(math.floor(w1/ratio),math.floor(h1/ratio))



    def indexed(self, fname):
        self.statusBar().showMessage(fname+" is indexed")
        try:
            self.lock.lockForRead()
        finally:
            self.lock.unlock()
        
    def processed(self, info):
        self.statusBar().showMessage("the "+info+"data is processed")     
        
    def finished(self, filenameToSave):
        self.statusBar().showMessage("Indexing complete")
        
        #self.threadForProcessData.wait()
        peak_x_all=[]
        peak_y_all=[]
        peak_x_temp=[]
        peak_y_temp=[]
        curveWidget = CurveDialog(edit=False, toolbar=True, 
                      options=dict(xlabel="Wavelength (nm)", ylabel="Absorbance (a.u.)"))
        self.add_tab(curveWidget, title =u'Absorption Spectra')
            
        plot=curveWidget.get_plot()
        
##########################################################################################################
###################吸附随时间变化的数据处理#################################################################
##########################################################################################################
        count=0
        for member in self.threadForProcessData.result_ad:
            [data_x,data_y,data_x,var,data_x_temp,data_y_temp,data_x_smooth,data_y_smooth,peak_x,peak_y]=member  
            self.statusBar().showMessage("plot----%i"%self.threadForProcessData.result_ad.index(member))
            
            if count==0: 
                #画出平滑后的吸光度曲线            
                curve=make.curve(data_x_smooth,data_y_smooth)
                plot.add_item(curve)
                plot.replot()  
            count=(count+1)%5
            
            peak_x_temp=peak_x_temp+peak_x
            peak_y_temp=peak_y_temp+peak_y
            
            peak_x_all.append(peak_x)
            peak_y_all.append(peak_y)
        
        peak_x_temp_int=[]
        for member in peak_x_temp:
            peak_x_temp_int.append(int(member))
        
        print("peak_x_temp_int................")
        print(peak_x_temp_int)
        #获取出现频率最高的数据
        dataProcess = Mymath.dataProcess()
        data_range=dataProcess.getMaxExistData(peak_x_temp_int,5)
        
        print("data_range................")
        print(data_range)
        
        #定义一个list用来存放有效的峰的横坐标值：
        peak_x_mean=[]
        peak_y_mean=[]
        for data_range_member in data_range:
            #去除出现频率低的误判的数据
            peak_x_wanted=[]
            peak_y_wanted=[]
            
            for i in range(len(peak_x_all)):
                if peak_x_all[i]!=[]:
                    temp_x=[]
                    temp_y=[]
                    for j in range(len(peak_x_all[i])):
                        if peak_x_all[i][j]>=min(data_range_member) and peak_x_all[i][j]<=max(data_range_member):
                            temp_x.append(peak_x_all[i][j])
                            temp_y.append(peak_y_all[i][j])
                else:
                    temp_x=[]
                    temp_y=[]
                    
                peak_x_wanted.append(temp_x)
                peak_y_wanted.append(temp_y)
                
            print("peak_x_wanted...................." )
            print(peak_x_wanted)
            print("peak_y_wanted....................")
            print(peak_y_wanted)
    
            time=[]
            for i in range(len(peak_x_wanted)):
                if peak_x_wanted[i]!=[]:
                    time.append(i)
            
            peak_y=[]
            peak_x=[]
            for i in range(len(peak_y_wanted)):
                peak_y+=peak_y_wanted[i]
                peak_x+=peak_x_wanted[i]
            peak_x_mean.append(numpy.mean(peak_x))
            peak_y_mean.append(numpy.mean(peak_y))
            print("time............")
            print(numpy.shape(time))
            print(time)
            print("peak_y...........")
            print(numpy.shape(peak_y))
            print(peak_y)
        
        index_remove=[]
        for i in range(len(peak_x_mean)):
            if max(peak_y_mean)/peak_y_mean[i]>5:
                index_remove.append(i)
                peak_x_mean[i]=[]
                peak_y_mean[i]=[]
                
        for i in range(len(index_remove)):
            peak_x_mean.remove([])
            peak_y_mean.remove([])
        #到此为止，peak_x_mean已经得到
        #确定是否要对peak_x_mean进行手动更改
        #弹出对话框是否要进行更改，要进行何种更改
        confirmData=str(peak_x_mean)[1:-1]
        dialog_confirm=codeDialog_confirm(confirmData)
        if dialog_confirm.exec_():
            temp=dialog_confirm.lineEdit.text().split(',')
            peak_x_mean=[]
            for memb in temp:
                peak_x_mean.append(float(memb))
            dialog_confirm.destroy()   
        #peak_x_mean更改结束 
        
        time_All=[]
        peak_y_All=[]
        for peak_x_mean_member in peak_x_mean:
            peak_x_des=peak_x_mean_member
            peak_y_des=[]    
            for member in self.threadForProcessData.result_ad: 
                [data_x,data_y,data_x,var,data_x_temp,data_y_temp,data_x_smooth,data_y_smooth,peak_x,peak_y]=member
                dataProcess = Mymath.dataProcess()
                peak_y_des.append(data_y_smooth[dataProcess.getIndex(data_x_smooth,peak_x_des)])
           
            time=range(0,self.procFileGap*self.fileSaveGap*len(peak_y_des),self.procFileGap*self.fileSaveGap)
            time_All.append(time)
            peak_y_All.append(peak_y_des)
            
        #画出不同的峰随时间变化散点图
        curveWidget = CurveDialog(edit=False, toolbar=True, 
                      options=dict(xlabel="Time (s)", ylabel="Absorbance (a.u.)"))
        self.add_tab(curveWidget, title =u'Absorbance-A Vs Time')
        plot=curveWidget.get_plot()
        
        for i in range(min(len(time_All),len(peak_y_All))):
            index1=time_from1/self.procFileGap/self.fileSaveGap
            index2=time_to1/self.procFileGap/self.fileSaveGap
            point = make.curve(time_All[i][index1:index2],peak_y_All[i][index1:index2],linestyle="NoPen",marker="Ellipse")
            plot.add_item(point)
            
            if self.flag:
                self.ATE=str(max(peak_y_All[i]))
            else:
                self.ATM=str(max(peak_y_All[i]))
            
            p=dataProcess.expProcess(numpy.array(peak_y_All[i][index1:index2]),numpy.array(time_All[i][index1:index2]))
            print(p)
            x = numpy.linspace(min(time_All[i][index1:index2]),max(time_All[i][index1:index2]),1000)
            y = p[0]-p[1]*math.e**(-x*p[2])
            x=list(x)
            y=list(y)
            curve=make.curve(x,y,color='r',linewidth=2)
            #curve=make.curve(time_All[i][index1:index2],peak_y_All[i][index1:index2],color='r',linewidth=2)
            plot.add_item(curve)

        #将time_All和peak_y_All保存到adsorption.xls中：
        import xlwt   
        file_ad = xlwt.Workbook() 
        table_ad = file_ad.add_sheet('Sheet1',cell_overwrite_ok=True)
        
        for i in range(min(len(time_All),len(peak_y_All))):
            for j in range(len(time_All[i])+1):
                if j==0:
                    table_ad.write(0,i*2,peak_x_mean[i])
                else:
                    table_ad.write(j,i*2,time_All[i][j-1])
                    table_ad.write(j,i*2+1,peak_y_All[i][j-1])
        file_ad.save(filenameToSave.split(";")[0])
        file_ad.save("adsorption.xls")
##########################################################################################################
###################脱附随时间变化的数据处理#################################################################
##########################################################################################################
        #脱附的峰和谷的值不是通过吸光度判别的，是通过吸附的峰的位置推算得到的
        curveWidget = CurveDialog(edit=False, toolbar=True, 
                      options=dict(xlabel="Wavelength (nm)", ylabel="Absorbance (a.u.)"))
        self.add_tab(curveWidget, title =u'Desorption Spectra')
        plot=curveWidget.get_plot()
        count=0
        for member in self.threadForProcessData.result_de:
            [data_x,data_y,data_x,var,data_x_temp,data_y_temp,data_x_smooth,data_y_smooth,peak_x,peak_y]=member  
            
            if count==0:
                #画出平滑后的吸光度曲线            
                curve=make.curve(data_x_smooth,data_y_smooth)
                plot.add_item(curve)
                plot.replot()
            count=(count+1)%10
            
        #画出不同的峰随时间变化散点图    
        curveWidget = CurveDialog(edit=False, toolbar=True, 
                      options=dict(xlabel="Time (s)", ylabel="Absorbance (a.u.)"))
        self.add_tab(curveWidget, title =u'Absorbance-D Vs Time')
        plot=curveWidget.get_plot()
       
        time_All=[]
        peak_y_All=[]
        for peak_x_mean_member in peak_x_mean:
            peak_x_des=peak_x_mean_member
            peak_y_des=[]    
            for member in self.threadForProcessData.result_de: 
                [data_x,data_y,data_x,var,data_x_temp,data_y_temp,data_x_smooth,data_y_smooth,peak_x,peak_y]=member
                dataProcess = Mymath.dataProcess()
                peak_y_des.append(data_y_smooth[dataProcess.getIndex(data_x_smooth,peak_x_des)])
           
            time=range(0,self.procFileGap*self.fileSaveGap*len(peak_y_des),self.procFileGap*self.fileSaveGap)
            time_All.append(time)
            peak_y_All.append(peak_y_des)

            ln_peak_y_des=[]
            for i in range(len(peak_y_des)):
                temp=math.log(numpy.array(peak_y_des)[i])
                ln_peak_y_des.append(temp)
            
            index1=time_from2/self.procFileGap/self.fileSaveGap
            index2=time_to2/self.procFileGap/self.fileSaveGap
            
            point=make.curve(time[index1:index2],peak_y_des[index1:index2],linestyle="NoPen",marker="Ellipse")
            plot.add_item(point)
            
            
            p=dataProcess.lineProcess(numpy.array(ln_peak_y_des)[index1:index2],numpy.array(time)[index1:index2])
            print(p)
            x = numpy.linspace(min(time[index1:index2]),max(time[index1:index2]),1000)
            y = math.e**(p[0]*x+p[1])
            x=list(x)
            y=list(y)
            curve=make.curve(x,y,color='r',linewidth=2)
            plot.add_item(curve)
            
        
        #将time_All和peak_y_All保存到desorption.xls中：    
        file_de = xlwt.Workbook() 
        table_de = file_de.add_sheet('Sheet1',cell_overwrite_ok=True)
        
        for i in range(min(len(time_All),len(peak_y_All))):
            for j in range(len(time_All[i])+1):
                if j==0:
                    table_de.write(0,i*2,peak_x_mean[i])
                else:
                    table_de.write(j,i*2,time_All[i][j-1])
                    table_de.write(j,i*2+1,peak_y_All[i][j-1])
        file_de.save(filenameToSave.split(";")[1])
        file_de.save("desorption.xls")
        #在结果显示区显示吸收峰的位置
        peak_x_mean.sort()
        for member in peak_x_mean:
            self.listWidget_result.addItem(u"λ%i=%.3f"%(peak_x_mean.index(member)+1,member))
        
#class MyTool(QMainWindow):
    def createActions(self):
        self.fileOpenAction=QAction(QIcon("icon/fileOpen.ico"),self.tr("Open"),self)   
        self.fileOpenAction.setShortcut("Ctrl+O")   
        self.fileOpenAction.setStatusTip(self.tr("Open a file"))
        # self.connect(self.fileOpenAction,SIGNAL("triggered()"),self.slotOpenFile)
        self.fileOpenAction.triggered.connect(self.slotOpenFile)


        self.fileSaveAction=QAction(QIcon("icon/fileSave.ico"),self.tr("Save"),self)   
        self.fileSaveAction.setShortcut("Ctrl+S")   
        self.fileSaveAction.setStatusTip(self.tr("Save the file"))   
        # self.connect(self.fileSaveAction,SIGNAL("triggered()"),self.slotSaveFile)
        self.fileSaveAction.triggered.connect(self.slotSaveFile)

        self.exitAction=QAction(QIcon("icon/exit.ico"),self.tr("Quit"),self)   
        self.exitAction.setShortcut("Ctrl+Q")   
        self.setStatusTip(self.tr("Quit"))   
        # self.connect(self.exitAction,SIGNAL("triggered()"),self.close)
        self.exitAction.triggered.connect(self.close)
 
        self.aboutAction=QAction(QIcon("icon/about.ico"),self.tr("About"),self)   
        # self.connect(self.aboutAction,SIGNAL("triggered()"),self.slotAbout)
        self.aboutAction.triggered.connect(self.slotAbout)

        self.setPathAction1=QAction(QIcon("icon/setPath1.ico"),self.tr("Set DAQ Path"),self)
        # self.connect(self.setPathAction1,SIGNAL("triggered()"),self.setPath1)
        self.setPathAction1.triggered.connect(self.setPath1)

        self.setPathAction2=QAction(QIcon("icon/setPath2.ico"),self.tr("Set SpectraSuite Path"),self)
        # self.connect(self.setPathAction2,SIGNAL("triggered()"),self.setPath2)
        self.setPathAction2.triggered.connect(self.setPath2)
        
        self.setPathAction3=QAction(QIcon("icon/setPath3.png"),self.tr("Set AvaRaman Path"),self)
        # self.connect(self.setPathAction3,SIGNAL("triggered()"),self.setPath3)
        self.setPathAction3.triggered.connect(self.setPath3)
        
        self.setPathAction4=QAction(QIcon("icon/setPath4.png"),self.tr("Set GamryFramework Path"),self)
        # self.connect(self.setPathAction4,SIGNAL("triggered()"),self.setPath4)
        self.setPathAction4.triggered.connect(self.setPath4)
        
        self.setPathAction5=QAction(QIcon("icon/setPath5.png"),self.tr("Set Echem Analyst Path"),self)
        # self.connect(self.setPathAction5,SIGNAL("triggered()"),self.setPath5)
        self.setPathAction5.triggered.connect(self.setPath5)

        self.setPathAction6=QAction(QIcon("icon/setPath6.png"),self.tr("Set CCD Path"),self)
        # self.connect(self.setPathAction6,SIGNAL("triggered()"),self.setPath6)
        self.setPathAction6.triggered.connect(self.setPath6)
        
        self.setParaAction=QAction(QIcon("icon/setPara.ico"),self.tr("Parameters Setting"),self)
        # self.connect(self.setParaAction,SIGNAL("triggered()"),self.setPara)
        self.setParaAction.triggered.connect(self.setPara)
        
        #########################################################################
        ###工具栏
        self.calibrateAction=QAction(QIcon("icon/calibrate.ico"),self.tr("Calibrate"),self)
        # self.connect(self.calibrateAction,SIGNAL("triggered()"),self.calibrate)
        self.calibrateAction.triggered.connect(self.calibrate)

        self.concentrationAction=QAction(QIcon("icon/concentration.ico"),self.tr("Measure Concentration"),self)
        # self.connect(self.concentrationAction,SIGNAL("triggered()"),self.concentration)
        self.concentrationAction.triggered.connect(self.concentration)

        self.surfaceCoverAction=QAction(QIcon("icon/surfaceCover.ico"),self.tr("Measure Surface Coverage"),self)
        # self.connect(self.surfaceCoverAction,SIGNAL("triggered()"),self.surfaceCover)
        self.surfaceCoverAction.triggered.connect(self.surfaceCover)

        self.orienAngleAction=QAction(QIcon("icon/orienAngle.ico"),self.tr("Measure Average Orientation Angle"),self)
        # self.connect(self.orienAngleAction,SIGNAL("triggered()"),self.orienAngle)
        self.orienAngleAction.triggered.connect(self.orienAngle)

        self.adsorptionAction=QAction(QIcon("icon/adsorption.png"),self.tr("Measure Adsorption Rate Constant"),self)
        # self.connect(self.adsorptionAction,SIGNAL("triggered()"),self.adsorption)
        self.adsorptionAction.triggered.connect(self.adsorption)

        self.desorptionAction=QAction(QIcon("icon/desorption.png"),self.tr("Measure Desportion Rate Constant"),self)
        # self.connect(self.desorptionAction,SIGNAL("triggered()"),self.desorption)
        self.desorptionAction.triggered.connect(self.desorption)

        self.freeEnergyAction=QAction(QIcon("icon/freeEnergy.png"),self.tr("Measure Adsorption Free Energy"),self)
        # self.connect(self.freeEnergyAction,SIGNAL("triggered()"),self.freeEnergy)
        self.freeEnergyAction.triggered.connect(self.freeEnergy)

        self.startPumpAction=QAction(QIcon("icon/start.png"),self.tr("power on pump"),self)
        # self.connect(self.startPumpAction,SIGNAL("triggered()"),self.startPump)
        self.startPumpAction.triggered.connect(self.startPump)
        
        self.stopPumpAction=QAction(QIcon("icon/stop.png"),self.tr("power off pump"),self)
        # self.connect(self.stopPumpAction,SIGNAL("triggered()"),self.stopPump)
        self.stopPumpAction.triggered.connect(self.stopPump)
        
        self.reversePumpAction=QAction(QIcon("icon/reverse1.png"),self.tr("reverse pump"),self)
        # self.connect(self.reversePumpAction,SIGNAL("triggered()"),self.reversePump)
        self.reversePumpAction.triggered.connect(self.reversePump)
        
    def slotOpenFile(self):
        try:
            f=open("directory.txt")
            print(type(f))
            directory,filename = os.path.split(f.readline())
            fileName=QFileDialog.getOpenFileName(self,directory=directory)
            print(fileName[0])
            fileName=fileName[0]
        except:

            fileName=QFileDialog.getOpenFileName(self)[0]

        if fileName:
            # print("----test22--")
            f=open("directory.txt",'w')
            f.write(fileName)
            f.close()
            # print("---test23--")
            self.statusBar().showMessage("open "+fileName+"...")
            return readFile(fileName)
        else:
            return -1
            
    def slotSaveFile(self):   
        pass

    def slotAbout(self): 
        
        QMessageBox.about(self,"About the Program",self.tr("""<b>多光谱融合表界面原位分析测试系统程序</b> 
                          <p>Copyright &copy; 2018 IECAS.
                          All rights reserved.
                          <p>多光谱融合表界面原位分析测试系统程序是一款采用光波导偏振吸收
                          光谱与偏振干涉光谱测量技术相融合的创新方法，原位实时检测亚
                          单分子吸附层的高灵敏度表面分析仪器测试界面。用于测定生化分
                          子及纳米粒子在固/液界面的覆盖度、吸附姿态、聚集状态、吸附
                          子及纳米粒子在固/液界面的覆盖度、吸附姿态、聚集状态、吸附
                          动力学参数（吸附速率常数、脱附速率常数、吸附自由能）、界面
                          诱导分子光谱变化等信息。
                          <p>"""))   

    def createToolBars(self):
        fileToolBar=self.addToolBar("File")   
        fileToolBar.addAction(self.fileOpenAction)   
        fileToolBar.addAction(self.fileSaveAction) 
        fileToolBar.addAction(self.exitAction)

        settingToolBar=self.addToolBar("setting")
        settingToolBar.addAction(self.setPathAction1)
        settingToolBar.addAction(self.setPathAction2)
        settingToolBar.addAction(self.setPathAction3)
        settingToolBar.addAction(self.setPathAction4)
        settingToolBar.addAction(self.setPathAction5)
        settingToolBar.addAction(self.setPathAction6)
        settingToolBar.addAction(self.setParaAction)
        
        interferToolBar=self.addToolBar("interferometry")
        interferToolBar.addAction(self.calibrateAction)
        interferToolBar.addAction(self.concentrationAction)
        interferToolBar.addAction(self.surfaceCoverAction)
        
        absorbToolBar=self.addToolBar("absorbance spectrometry")      
        absorbToolBar.addAction(self.orienAngleAction)
        absorbToolBar.addAction(self.adsorptionAction)
        absorbToolBar.addAction(self.desorptionAction)
        absorbToolBar.addAction(self.freeEnergyAction)
        
        pumpToolBar=self.addToolBar("pump control")
        self.label_pump = QLabel("注液泵控制  ")
        self.checkBox = QCheckBox()
        self.checkBox.setText('Timer fixed')
        self.checkBox.setFont(QFont("Helvetica",9,QFont.Normal))
        # self.connect(self.checkBox,SIGNAL('toggled(bool)'),self.setFixedTimer)
        self.checkBox.toggled.connect(self.setFixedTimer)
        self.label0 = QLabel()
        self.label0.setText("    Timer:")
        self.label0.setFont(QFont("Helvetica",9,QFont.Normal))
        self.lineEdit0 = QLineEdit()
        self.lineEdit0.setText('0.00')
        self.lineEdit0.setMaximumSize(50,20)
        self.label1 = QLabel()   
        self.label1.setText(" s")
        self.label1.setFont(QFont("Helvetica",9,QFont.Normal))
        self.label2 = QLabel()   
        self.label2.setText("    Flow Rate:")
        self.label2.setFont(QFont("Helvetica",9,QFont.Normal))
        self.lineEdit1 = QLineEdit()
        self.lineEdit1.setText('50.0')
        self.lineEdit1.setMaximumSize(50,20)
        self.label3 = QLabel()
        self.label3.setText(" rpm   ")
        self.label3.setFont(QFont("Helvetica",9,QFont.Normal))
        pumpToolBar.addWidget(self.label_pump)
        pumpToolBar.addWidget(self.checkBox)
        pumpToolBar.addWidget(self.label0)
        pumpToolBar.addWidget(self.lineEdit0)
        pumpToolBar.addWidget(self.label1)
        pumpToolBar.addWidget(self.label2)
        pumpToolBar.addWidget(self.lineEdit1)
        pumpToolBar.addWidget(self.label3)
        pumpToolBar.addAction(self.startPumpAction)
        pumpToolBar.addAction(self.stopPumpAction)
        pumpToolBar.addAction(self.reversePumpAction)
        
        self.s=self.addToolBar("DAQ")
#        helpToolBar=self.addToolBar("help")      
#        helpToolBar.addAction(self.abnoutAction)
 
    def createMenus(self):   
        fileMenu=self.menuBar().addMenu(self.tr("File"))   
        fileMenu.addAction(self.fileOpenAction)   
        fileMenu.addAction(self.fileSaveAction)   
        fileMenu.addAction(self.exitAction) 
        
        editMenu=self.menuBar().addMenu(self.tr("Setting"))  
        editMenu.addAction(self.setPathAction1)
        editMenu.addAction(self.setPathAction2) 
        editMenu.addAction(self.setPathAction3)
        editMenu.addAction(self.setPathAction4)
        editMenu.addAction(self.setPathAction5)
        editMenu.addAction(self.setPathAction6)
        editMenu.addAction(self.setParaAction)
        
        aboutMenu=self.menuBar().addMenu(self.tr("Help"))   
        aboutMenu.addAction(self.aboutAction)
        
    def setPath1(self):
        try:
            self.set_exe_path(1)
        except:
            QMessageBox.warning(self,"Information",
                     self.tr("setting error!"))
        # try:
        #     self.path1=unicode(QFileDialog.getOpenFileName(self),'utf-8','ignore')
        #     if self.path1 != '':
        #         f=open("path.txt",'w')
        #         f.write('path1::'+self.path1+'\n')
        #         try:
        #             f.write('path2::'+self.path2+'\n')
        #         except:
        #             pass
        #         try:
        #             f.write('path3::'+self.path3+'\n')
        #         except:
        #             pass
        #         try:
        #             f.write('path4::'+self.path4+'\n')
        #         except:
        #             pass
        #         try:
        #             f.write('path5::'+self.path5+'\n')
        #         except:
        #             pass
        #         try:
        #             f.write('path6::'+self.path6+'\n')
        #         except:
        #             pass
        # except:
        #     QMessageBox.warning(self, "Information",
        #                         self.tr("setting error!"))


    
    def setPath2(self):
        try:
            self.set_exe_path(2)
        except:
            QMessageBox.warning(self,"Information",
                     self.tr("setting error!"))
        # try:
        #     self.path2=unicode(QFileDialog.getOpenFileName(self),'utf-8','ignore')
        #     if self.path2 != '':
        #         f=open("path.txt",'w')
        #
        #         try:
        #             f.write('path1::'+self.path1+'\n')
        #         except:
        #             f.write('\n')
        #
        #         f.write('path2::'+self.path2+'\n')
        #
        #         try:
        #             f.write('path3::'+self.path3+'\n')
        #         except:
        #             pass
        #         try:
        #             f.write('path4::'+self.path4+'\n')
        #         except:
        #             pass
        #         try:
        #             f.write('path5::'+self.path5+'\n')
        #         except:
        #             pass
        #         try:
        #             f.write('path6::'+self.path6+'\n')
        #         except:
        #             pass
        # except:
        #     QMessageBox.warning(self,"Information",
        #              self.tr("setting error!"))
                     
    def setPath3(self):
        try:
            self.set_exe_path(3)
        except:
            QMessageBox.warning(self,"Information",
                     self.tr("setting error!"))
        # try:
        #     self.path3=unicode(QFileDialog.getOpenFileName(self),'utf-8','ignore')
        #     print(self.path3)
        #     if self.path3 != '':
        #         f=open("path.txt",'w')
        #
        #         try:
        #             f.write('path1::'+self.path1+'\n')
        #         except:
        #             f.write('\n')
        #         try:
        #             f.write('path2::'+self.path2+'\n')
        #         except:
        #             f.write('\n')
        #
        #         f.write('path3::'+self.path3+'\n')
        #
        #         try:
        #             f.write('path4::'+self.path4+'\n')
        #         except:
        #             pass
        #
        #         try:
        #             f.write('path5::'+self.path5+'\n')
        #         except:
        #             pass
        #         try:
        #             f.write('path6::'+self.path6+'\n')
        #         except:
        #             pass
        # except:
        #     QMessageBox.warning(self,"Information",
        #              self.tr("setting error!"))
                     
    def setPath4(self):
        try:
            self.set_exe_path(4)
        except:
            QMessageBox.warning(self,"Information",
                     self.tr("setting error!"))
        # try:
        #     self.path4=unicode(QFileDialog.getOpenFileName(self),'utf-8','ignore')
        #     print(self.path4)
        #     if self.path4 != '':
        #         f=open("path.txt",'w')
        #
        #         try:
        #             f.write('path1::'+self.path1+'\n')
        #         except:
        #             f.write('\n')
        #         try:
        #             f.write('path2::'+self.path2+'\n')
        #         except:
        #             f.write('\n')
        #         try:
        #             f.write('path3::'+self.path3+'\n')
        #         except:
        #             f.write('\n')
        #
        #         f.write('path4::'+self.path4+'\n')
        #
        #         try:
        #             f.write('path5::'+self.path5+'\n')
        #         except:
        #             pass
        #         try:
        #             f.write('path6::'+self.path6+'\n')
        #         except:
        #             pass
        # except:
        #     QMessageBox.warning(self,"Information",
        #              self.tr("setting error!"))
                     
    def setPath5(self):
        try:
            self.set_exe_path(5)
            # self.path5=unicode(QFileDialog.getOpenFileName(self),'utf-8','ignore')
            # print(self.path5)
            # if self.path5 != '':
            #     f=open("path.txt",'w')
            #
            #     try:
            #         f.write('path1::'+self.path1+'\n')
            #     except:
            #         f.write('\n')
            #     try:
            #         f.write('path2::'+self.path2+'\n')
            #     except:
            #         f.write('\n')
            #     try:
            #         f.write('path3::'+self.path3+'\n')
            #     except:
            #         f.write('\n')
            #     try:
            #         f.write('path4::'+self.path4+'\n')
            #     except:
            #         f.write('\n')
            #     f.write('path5::'+self.path5+'\n')
            #     try:
            #         f.write('path6::'+self.path6+'\n')
            #     except:
            #         pass
        except:
            QMessageBox.warning(self,"Information",
                     self.tr("setting error!"))

    def setPath6(self):
        try:
            self.set_exe_path(6)
        except:
            QMessageBox.warning(self,"Information",
                     self.tr("setting error!"))

        # try:
        #     self.path6=unicode(QFileDialog.getOpenFileName(self),'utf-8','ignore')
        #     print(self.path6)
        #     if self.path6 != '':
        #         f=open("path.txt",'w')
        #
        #         try:
        #             f.write('path1::'+self.path1+'\n')
        #         except:
        #             f.write('\n')
        #         try:
        #             f.write('path2::'+self.path2+'\n')
        #         except:
        #             f.write('\n')
        #         try:
        #             f.write('path3::'+self.path3+'\n')
        #         except:
        #             f.write('\n')
        #         try:
        #             f.write('path4::'+self.path4+'\n')
        #         except:
        #             f.write('\n')
        #         try:
        #             f.write('path5::'+self.path5+'\n')
        #         except:
        #             f.write('\n')
        #         f.write('path6::'+self.path6+'\n')
        # except:
        #     QMessageBox.warning(self,"Information",
        #              self.tr("setting error!"))

    def set_exe_path(self, index): #index从1开始，分别为各软件exe的路径
        try:
            with open('path.json', 'r') as file_object:
                path_list = json.load(file_object)
            print(path_list)

            filename = QFileDialog.getOpenFileName(self, "Open file", '', "*.exe", None,
                                                   QFileDialog.DontUseNativeDialog)
            if not filename[0]:
                return
            path_list[index-1] = filename[0]
            with open('path.json', 'w') as file_object:
                json.dump(path_list, file_object)
            QMessageBox.information(self, self.tr("info"),
                                self.tr("Completed"))
        except:
            pass

    def setPara(self):
        try:
            para_program1 = [self.var_len1,self.var_thres1,self.smooth_len1,self.smooth_num1,self.peak_step1,self.phi_step,self.fit_type]
            para_program2 = [self.var_len2,self.var_thres2,self.smooth_len2,self.smooth_num2,self.peak_step2,self.peak_thres]
            dialog_setPara = codeDialog_setPara(para_program1,para_program2)
            if dialog_setPara.exec_():
                self.var_len1 = int(dialog_setPara.lineEdit1.text())
                self.var_thres1 = float(dialog_setPara.lineEdit2.text())
                self.smooth_len1 = int(dialog_setPara.lineEdit3.text())
                self.smooth_num1 = int(dialog_setPara.lineEdit4.text())
                self.peak_step1 = int(dialog_setPara.lineEdit5.text())
                self.phi_step = int(dialog_setPara.lineEdit6.text())
                self.fit_type = int(dialog_setPara.spinBox1.value())

                self.var_len2 = int(dialog_setPara.lineEdit7.text())
                self.var_thres2 = float(dialog_setPara.lineEdit8.text())
                self.smooth_len2 = int(dialog_setPara.lineEdit9.text())
                self.smooth_num2 = int(dialog_setPara.lineEdit10.text())
                self.peak_step2 = int(dialog_setPara.lineEdit11.text())
                self.peak_thres = float(dialog_setPara.lineEdit12.text())

                dialog_setPara.destroy()
        except:
            pass

    def calc_thickness(self):
        # mywidget=Porosity_Thickness_main.MyMainWindow()
        # mywidget.exec_()
        mydialog=P_d_dialog.MyPdDialog(self)
        # mydialog.exec_()
        mydialog.setAttribute(Qt.WA_DeleteOnClose)
        mydialog.show()
    def calibrate(self):
        concentration=[]
        phase=[]
        dialogTable=dialog_table.dialogTable(['Concentration','phase'])
        if dialogTable.exec_():
            for i in range(dialogTable.model.rowCount()):
                index_x=dialogTable.model.index(i,0)
                index_y=dialogTable.model.index(i,1)
                temp_x=float(dialogTable.model.data(index_x,0))
                temp_y=float(dialogTable.model.data(index_y,0))
                concentration.append(temp_x[0])
                phase.append(temp_y[0])
            dataProcess=Mymath.dataProcess()
            self.P_calibrate=dataProcess.lineProcess(numpy.array(concentration),numpy.array(phase))
            print(self.P_calibrate)
            self.listWidget_result.addItem("Calibrated Coefficient=[%.3f  %.3f]"%(self.P_calibrate[0],self.P_calibrate[1]))
            QMessageBox.information(self,self.tr("Calibration"),
                     self.tr("Calibrated Coefficient=[%.3f  %.3f]"%(self.P_calibrate[0],self.P_calibrate[1])))

    def concentration(self):
        print('entering concentration function....')
        try:
            concentration=self.P_calibrate[0]*self.phi/2/math.pi+self.P_calibrate[1]
            self.listWidget_result.addItem("Concentration = %.3f wt%%"%concentration)
            QMessageBox.information(self,self.tr("Concentration"),
                                    self.tr("Concentration=%.3f wt%%"%concentration))
        except:
            QMessageBox.warning(self,'warning','something wrong')
            pass
    
    def surfaceCover(self):
        try:
            dialog_surfaceCover=codeDialog_surfaceCover()
            if dialog_surfaceCover.exec_():
                Stad=float(dialog_surfaceCover.lineEdit.text())
                surfaceCoverage=0.622*self.phi/Stad
                self.listWidget_result.addItem("sufaceCoverage=%.3f"%surfaceCoverage)

                dialog_surfaceCover.destroy()
            #return surfaceCoverage
        except:
            pass
    
    def orienAngle(self):
        try:
            try:
                dialog_orienAngle=codeDialog_orienAngle(self.ATE,self.ATM)
            except:
                dialog_orienAngle=codeDialog_orienAngle("1.0","1.0")

            if dialog_orienAngle.exec_():
                try:
                    ATE=float(dialog_orienAngle.lineEdit_2.text())
                    ATM=float(dialog_orienAngle.lineEdit_3.text())
                    ro=ATE/ATM
                    N=float(dialog_orienAngle.lineEdit_4.text())
                    n21=1.33/1.52
                    nglass=1.52
                    sina=N/nglass
                    alpha=math.asin(N/nglass)
                    cosa=math.cos(alpha)
                    temp=(sina**2-n21**2)*cosa**2/((1-n21**2)*((1+n21**2)*sina**2-n21**2))
                    Ex=math.sqrt(temp)
                    Ey=2*cosa/math.sqrt(1-n21**2)
                    Ez=2*sina*cosa/math.sqrt((1-n21**2)*((1+n21**2)*sina**2-n21**2))
                    cot2=(Ey**2/ro-Ex**2)/(2*Ez**2)
                    cot=math.sqrt(cot2)
                    theta=math.atan(1/cot)
                    theta=theta*180/math.pi
                    self.listWidget_result.addItem("orienAngle=%.3f deg"%theta)
                    QMessageBox.information(self,self.tr("Average Orientation Angle"),
                         self.tr("Average Orientation Angle=%.3f deg"%theta))
                except:
                    QMessageBox.warning(self,self.tr("Error"),
                         self.tr("Input error!!!"))
                dialog_orienAngle.destroy()
        except:
            pass
    
    def adsorption(self):
        try:
            concentration=1.0
            dialog_adsorption=codeDialog_adsorption()
            if dialog_adsorption.exec_():
                concentration=float(dialog_adsorption.lineEdit.text())
                dialog_adsorption.destroy()

            time_All=[]
            A_All=[]
            self.wavelength=[]
            import xlrd
            bk = xlrd.open_workbook('adsorption.xls')
            sh = bk.sheet_by_name("Sheet1")
            for j in range(0,sh.ncols,2):
                time=[]
                A=[]
                for i in range(sh.nrows):
                    if i==0:
                        self.wavelength.append(float(sh.cell_value(0,j)))
                    else:
                        time.append(float(sh.cell_value(i,j)))
                        A.append(float(sh.cell_value(i,j+1)))
                time_All.append(time)
                A_All.append(A)

            self.ka=[]
            dataProcess=Mymath.dataProcess()
            for i in range(min(len(time_All),len(A_All))):
                index1=time_from1/self.procFileGap/self.fileSaveGap
                index2=time_to1/self.procFileGap/self.fileSaveGap
                p=dataProcess.expProcess(numpy.array(A_All[i][index1:index2]),numpy.array(time_All[i][index1:index2]))
                self.listWidget_result.addItem(u"y=%.4f-%.4f*exp(-x*%.4f)"%(p[0],p[1],p[2]))
                print(p)
                tao=p[2]
                ka=(tao-self.kd[i])*55.5/concentration
                self.ka.append(ka)
                self.listWidget_result.addItem(u"λ:%.2f nm"%self.wavelength[i])
                self.listWidget_result.addItem(u"Ka=%.2E s-1"%ka)

            temp=""
            for i in range(min(len(self.wavelength),len(self.ka))):
                temp=temp+u"λ:%.2f nm  Ka:%.2E s-1  \n"%(self.wavelength[i],self.ka[i])
            QMessageBox.information(self,self.tr("Adsorption Rate Constant"),self.tr(temp))
        except:
            pass
                
    def desorption(self):
        try:
            time_All=[]
            lnA_All=[]
            self.wavelength=[]
            import xlrd
            bk = xlrd.open_workbook('desorption.xls')
            sh = bk.sheet_by_name("Sheet1")
            for j in range(0,sh.ncols,2):
                time=[]
                lnA=[]
                for i in range(sh.nrows):
                    if i==0:
                        self.wavelength.append(float(sh.cell_value(0,j)))
                    else:
                        time.append(float(sh.cell_value(i,j)))
                        lnA.append(math.log(float(sh.cell_value(i,j+1))))
                time_All.append(time)
                lnA_All.append(lnA)

            self.kd=[]
            dataProcess=Mymath.dataProcess()
            for i in range(min(len(time_All),len(lnA_All))):
                index1=time_from2/self.procFileGap/self.fileSaveGap
                index2=time_to2/self.procFileGap/self.fileSaveGap
                p=dataProcess.lineProcess(numpy.array(lnA_All[i])[index1:index2],numpy.array(time_All[i])[index1:index2])
                self.listWidget_result.addItem(u"lny=%.4f*x%.4f"%(p[0],p[1]))
                print(p)
                kd=math.fabs(p[0])
                self.kd.append(kd)
                self.listWidget_result.addItem(u"λ:%.2f nm"%self.wavelength[i])
                self.listWidget_result.addItem(u"Kd=%.5f s-1"%kd)

            temp=""
            for i in range(min(len(self.wavelength),len(self.kd))):
                temp=temp+u"λ:%.2f nm  Kd:%.5f s-1  \n"%(self.wavelength[i],self.kd[i])
            QMessageBox.information(self,self.tr("Desorption Rate Constant"),self.tr(temp))
        except:
            pass
    def freeEnergy(self):
        try:

            R=8.31
            T=25.0+273.0
            temp=""
            for i in range(min(len(self.kd),len(self.ka))):
                Energy=R*T*math.log(self.kd[i]/self.ka[i])
                self.listWidget_result.addItem(u"λ:%.2f nm"%self.wavelength[i])
                self.listWidget_result.addItem("Adsorption Free Energy=%.2E J/mol"%Energy)
                temp=temp+u"λ:%.2f nm  E:%.2E J/mol  \n"%(self.wavelength[i],Energy)
            QMessageBox.information(self,self.tr("Desorption Rate Constant"), self.tr(temp))
        except:
            pass

    def clearResults(self):
        for i in range(self.listWidget_1.count()-4):
            self.listWidget_1.takeItem(4)
            
    def selectType1(self):
        # self.groupbox1.setChecked(False)
        if self.groupbox1.isChecked():
            self.groupbox2.setChecked(False)
            self.groupbox25.setChecked(False)
            self.groupbox3.setChecked(False)
            self.groupbox4.setChecked(False)
            self.groupbox5.setChecked(False)
        else:
            self.groupbox2.setChecked(True)
    def selectType2(self):
        if self.groupbox2.isChecked():
            self.groupbox1.setChecked(False)
            self.groupbox25.setChecked(False)
            self.groupbox3.setChecked(False)
            self.groupbox4.setChecked(False)
            self.groupbox5.setChecked(False)
        else:
            self.groupbox25.setChecked(True)

    def selectType25(self):
        if self.groupbox25.isChecked():
            self.groupbox1.setChecked(False)
            self.groupbox2.setChecked(False)
            self.groupbox3.setChecked(False)
            self.groupbox4.setChecked(False)
            self.groupbox5.setChecked(False)
        else:
            self.groupbox3.setChecked(True)
    def selectType3(self):
        if self.groupbox3.isChecked():
            self.groupbox1.setChecked(False)
            self.groupbox2.setChecked(False)
            self.groupbox25.setChecked(False)
            self.groupbox4.setChecked(False)
            self.groupbox5.setChecked(False)
        else:
            self.groupbox4.setChecked(True)
    def selectType4(self):
        if self.groupbox4.isChecked():
            self.groupbox1.setChecked(False)
            self.groupbox2.setChecked(False)
            self.groupbox25.setChecked(False)
            self.groupbox3.setChecked(False)
            self.groupbox5.setChecked(False)
        else:
            self.groupbox5.setChecked(True)
    def selectType5(self):
        if self.groupbox5.isChecked():
            self.groupbox1.setChecked(False)
            self.groupbox2.setChecked(False)
            self.groupbox25.setChecked(False)
            self.groupbox3.setChecked(False)
            self.groupbox4.setChecked(False)
        else:
            self.groupbox1.setChecked(True)     
   
    def setFixedTimer(self):
        if self.checkBox.isChecked()==True:
            if self.flag_reverse:
                self.lineEdit0.setText('15.00')
                self.lineEdit0.setDisabled(True)
            else:
                self.lineEdit0.setText('7.00')
                self.lineEdit0.setDisabled(True)
            self.lineEdit1.setText('100.0')
            self.lineEdit1.setDisabled(True)
        else:
            self.lineEdit0.setDisabled(False)
            self.lineEdit0.setText('0.00')
            self.lineEdit1.setDisabled(False)
            self.lineEdit1.setText('50.0')
            
    def startPump(self):
        print("start pump action triggered")
        flag = True
        while flag:
            print("serialport:",self.SerialPort)
            try:
                Speed=float(self.lineEdit1.text())
        
                if(Speed==100.0):
                    OnOff=3
                    Speed=0.0
                else:
                    OnOff=1
                if self.flag_reverse:
                    Reverse=0
                else:
                    Reverse=1
                print('---1')
                self.pumpControl(self.SerialPort,Speed,OnOff,Reverse) # 初始设置serialport=1
                print('---2')
                sleep(0.01)
                self.pumpControl(self.SerialPort,Speed,OnOff,Reverse)
                sleep(0.01)
                self.pumpControl(self.SerialPort,Speed,OnOff,Reverse)
                flag = False
            except:
                # break
                self.SerialPort = self.SerialPort+1
                if self.SerialPort==256:
                    flag=False

                    
        if float(self.lineEdit0.text())!=0.0:
            self.timeValue=float(self.lineEdit0.text())
            self.timer=QBasicTimer()  
            self.timer.start(10, self)             
            
    def timerEvent(self, event):
        self.lineEdit0.setText("%.2f"%(float(self.lineEdit0.text())-0.01))        
        if float(self.lineEdit0.text())<0.0:
            self.lineEdit0.setText("%.2f"%self.timeValue)
            self.timer.stop()
            self.stopPump()
            sleep(0.01)
            self.stopPump()
            sleep(0.01)
            self.stopPump()

    def stopPump(self):
        flag = True
        while flag:
            try:
                if float(self.lineEdit1.text())!=100.0:
                    Speed=float(self.lineEdit1.text())
                    OnOff=0
                else:
                    Speed=0.0
                    OnOff=2
                if self.flag_reverse:
                    Reverse=0
                else:
                    Reverse=1
                self.pumpControl(self.SerialPort,Speed,OnOff,Reverse)
                flag = False
            except:
                self.SerialPort = self.SerialPort+1
                if self.SerialPort==256:
                    flag=False


    def reversePump(self):

        flag = True
        while flag:
            try:
                Speed=float(self.lineEdit1.text())
                if(Speed==100.0):
                    OnOff=2
                    Speed=0.0
                else:
                    OnOff=0
                    
                if self.flag_reverse:
                    self.flag_reverse=False
                else:
                    self.flag_reverse=True

                if self.flag_reverse:
                    Reverse=0
                    self.reversePumpAction.setText("CCW")
                    self.reversePumpAction.setIcon(QIcon("icon/reverse2.png"))
                else:
                    Reverse=1
                    self.reversePumpAction.setText("CW")
                    self.reversePumpAction.setIcon(QIcon("icon/reverse1.png"))
                self.pumpControl(self.SerialPort,Speed,OnOff,Reverse)
                flag = False
            except:
                self.SerialPort = self.SerialPort+1
                if self.SerialPort==256:
                    flag=False

                    
        if self.checkBox.isChecked():
            if self.flag_reverse:
                self.lineEdit0.setDisabled(False)
                self.lineEdit0.setText('15.00')
                self.lineEdit0.setDisabled(True)
            else:
                self.lineEdit0.setDisabled(False)
                self.lineEdit0.setText('7.00')
                self.lineEdit0.setDisabled(True)
                
    def pumpControl(self,SerialPort,Speed,OnOff,Reverse):
        import serial      #导入串口包
        ser=serial.Serial()
        ser.close()         #先关闭串口
        ser.port='COM'+str(SerialPort-1)
        # ser.port='COM4'
        
        ser.baudrate=1200   #设定串口
        ser.bytesize=8
        ser.parity='E'
        ser.stopbits=1
        ser.timeout=None
        ser.xonxoff=0
        ser.rtscts=0
        
        data = [0xE9,0x01,0x06,0x57,0x4A]
        flowRate = int(float(Speed)*10)
        data.append(int(flowRate/256))
        data.append(int(flowRate%256))
        data.append(OnOff)
        data.append(Reverse)
        temp = data[1]
        for i in range(7):
            temp=temp^data[i+2]
        print(temp)
        data.append(temp)
        print(data)
        # controlSignal=''  ##python2写法
        # for i in data:
        #     controlSignal=controlSignal+chr(i)  #16进制转字符
        # print(controlSignal)
        controlSignal = bytearray()    #python3写法
        for i in data:
            controlSignal.append(i)
        print(controlSignal)
        
        ser.open()          #打开串口
        print('Open serial now')
        ser.write(controlSignal)
        print('Close serial now')
        ser.close()          
        
    def slotTest1DataProcess(self,data_x,data_y):
        print("slotTest1DataProcess start...")
        import Mymath
        dataProcess = Mymath.dataProcess()
        self.statusBar().showMessage("get the peak and valley...")
        #获取峰值和谷值的位置
        m,n = dataProcess.get_peak(data_y,self.peak_step1)
        peak_x=[]
        peak_y=[]
        valley_x=[]
        valley_y=[]
        for i in m:
            peak_x.append(data_x[i])
            peak_y.append(data_y[i])
        for i in n:
            valley_x.append(data_x[i])
            valley_y.append(data_y[i])
        #过滤掉峰值谷值明显误判的点
        #去除两端误判的点
        #创建字典
        
        dict_peak = {}
        for i in range(len(peak_x)):
            dict_peak[peak_x[i]] = peak_y[i]
        dict_valley = {}
        for i in range(len(valley_x)):
            dict_valley[valley_x[i]] = valley_y[i]
        dict_peak.update(dict_valley)
        dict_peak=sorted(dict_peak.iteritems(),key=lambda asd:asd[0],reverse = False)          
        
        flag = 0
        index_remove = []
        #阈值ep,通过dict_peak的第二列的最大最小值差的一半来确定
        #获取dict_peak的第二列
        temp=[]
        for i in range(len(dict_peak)):
            temp.append(dict_peak[i][1])
        ep = float(max(temp)-min(temp))/2.0
        #ep = 0.1
        for i in range(len(dict_peak)-1):
            if math.fabs(dict_peak[i+1][1]-dict_peak[i][1])>=ep:
                flag = 1
            elif math.fabs(dict_peak[i+1][1]-dict_peak[i][1])<ep:
                if flag == 0:
                    index_remove.append(i)
                elif flag == 1:
                    index_remove.append(i+1)
        print(index_remove)
        
        if index_remove!=[]:
            #移除对应index的元素，并且消除误判
            #0 1 2 3 6 7 8 10 11 12:4,10 
            #0 1 2 3 6 7 8:4,13
            #6 7 8 10 11 12:0,10
            #4 5 8 9:0,13
            #0 1 2 3 10 11 12:4,10
            #0 1 2 3:4,13
            #10 11 12:0,10
            #6 7 8:0,13
            flag = 0
            temp=[]
            for i in range(len(index_remove)-1):
                if index_remove[i+1]-index_remove[i] >2 :
                    flag = 1
                    temp.append(index_remove[i])
                    temp.append(index_remove[i+1])
            if flag ==1:
                if min(index_remove)==0 and max(index_remove)==len(dict_peak)-1:
                    index_start=min(temp)+1
                    index_end=max(temp)
                elif min(index_remove)==0 and max(index_remove)!=len(dict_peak)-1:
                    index_start=min(temp)+1
                    index_end=len(dict_peak)
                elif min(index_remove)!=0 and max(index_remove)==len(dict_peak)-1:
                    index_start=0
                    index_end=max(temp)
                elif min(index_remove)!=0 and max(index_remove)!=len(dict_peak)-1:
                    index_start=0
                    index_end=len(dict_peak)
            elif flag == 0:
                if min(index_remove)==0:
                    index_start=max(index_remove)+1
                    index_end=len(dict_peak)
                elif min(index_remove)!=0 and max(index_remove)==len(dict_peak)-1:
                    index_start=0
                    index_end=min(index_remove)
                elif min(index_remove)!=0 and max(index_remove)!=len(dict_peak)-1:
                    index_start=0
                    index_end=len(dict_peak)
            dict_peak = dict_peak[index_start:index_end]
        print(dict_peak)
        
        #将一个二维list转换成两个一维list
        peak_valley_x = []
        peak_valley_y = []
        for member in dict_peak:
            peak_valley_x.append(member[0])
            peak_valley_y.append(member[1])
        peak_x=[]
        peak_y=[]
        valley_x=[]
        valley_y=[]
        temp1_y=peak_valley_y[0:len(peak_valley_y):2]
        temp2_y=peak_valley_y[1:len(peak_valley_y):2]
        if sum(temp1_y)>=sum(temp2_y):
            peak_y=temp1_y
            valley_y=temp2_y
            peak_x=peak_valley_x[0:len(peak_valley_x):2]
            valley_x=peak_valley_x[1:len(peak_valley_x):2]
        elif sum(temp1_y)<sum(temp2_y):
            peak_y=temp2_y
            valley_y=temp1_y
            peak_x=peak_valley_x[1:len(peak_valley_x):2]
            valley_x=peak_valley_x[0:len(peak_valley_x):2]
#        print peak_x
#        print peak_y
#        print valley_x
#        print valley_y
#        print data_y[0]
#        print data_y[-1]
        phi = dataProcess.getPhi(peak_x,peak_y,valley_x,valley_y,data_y[0],data_y[-1])
        return phi,peak_valley_x,peak_valley_y      
        
def slotTest2DataProcess(data_x1,data_y1,data_x2,data_y2,data_x3,data_y3):
    print("slotTest2DataProcess start...")
    import Mymath
    dataProcess = Mymath.dataProcess()
        
    #self.statusBar().showMessage("caculate the absorbers...")
    length=min(len(data_y1),len(data_y2),len(data_y3))
    data_x=data_x3
    data_y=list(numpy.zeros(length))
    for i in range(len(data_y)):
        try: 
            #计算吸光度                       
            data_y[i] = -math.log10(math.fabs(data_y3[i]-data_y1[i])
                                /math.fabs(data_y2[i]-data_y1[i]))
        except:
            data_y[i] = 0.0
            
    data_smooth_y = dataProcess.smooth(data_y,smooth_len2) 
    data_smooth_x = data_x       
    for i in range(smooth_num2):
        data_smooth_y = dataProcess.smooth(data_smooth_y,smooth_len2)
            
    var = dataProcess.get_var(data_y,var_len2,100000)
            
    #self.statusBar().showMessage("select the wanted piece...")
    #获取截取片段的下表范围,并且截取数据,下表没有严格截取少一个数据无伤大雅
    index_wanted = []
    for i in range(len(var)):
        if var[i] < var_thres2:
            index_wanted.append(i)
    data_x_temp = data_x[min(index_wanted):max(index_wanted)]
    data_y_temp = data_y[min(index_wanted):max(index_wanted)]
    #self.statusBar().showMessage("draw the wanted pieces curves...")
                
    #self.statusBar().showMessage("smoothing the curves...")
    #直接平滑,进行3次平滑处理
    data_y_smooth = dataProcess.smooth(data_y_temp,smooth_len2)
    for i in range(smooth_num2-1):
        data_y_smooth = dataProcess.smooth(data_y_smooth,smooth_len2)
    data_x_smooth = data_x_temp
            
    #self.statusBar().showMessage("mark the peak and valley point...")
    m,n= dataProcess.get_peak(data_y_smooth,peak_step2)
    peak_x=[]
    peak_y=[]
    valley_x=[]
    valley_y=[]
    for i in m:
        if data_y_smooth[i]<peak_thres:
            pass
        else:
            peak_x.append(data_x_smooth[i])
            peak_y.append(data_y_smooth[i])
    for i in n:
        if data_y_smooth[i]<peak_thres:
            pass
        else:
            valley_x.append(data_x_smooth[i])
            valley_y.append(data_y_smooth[i])
    print("slotTest2DataProcess end...")
    return [data_smooth_x,data_smooth_y,data_x,var,data_x_temp,data_y_temp,data_x_smooth,data_y_smooth,peak_x,peak_y]

class codeDialog_setPara(dialog_setPara.Ui_Dialog):#修改为从Ui_Dialog继承
    def __init__(self,para_program1,para_program2, parent = None):
        super(codeDialog_setPara, self).__init__(parent)
        self.setupUi(self,para_program1,para_program2)
        
class codeDialog_orienAngle(dialog_orienAngle.Ui_Dialog):#修改为从Ui_Dialog继承
    def __init__(self,ATE,ATM,parent = None):
        super(codeDialog_orienAngle, self).__init__(parent)
        self.setupUi(self,ATE,ATM)

class codeDialog_adsorption(dialog_adsorption.Ui_Dialog):#修改为从Ui_Dialog继承
    def __init__(self, parent = None):
        super(codeDialog_adsorption, self).__init__(parent)
        self.setupUi(self)
        
class codeDialog_surfaceCover(dialog_surfaceCover.Ui_Dialog):#修改为从Ui_Dialog继承
    def __init__(self, parent = None):
        super(codeDialog_surfaceCover, self).__init__(parent)
        self.setupUi(self)

class codeDialog_setNum(dialog_setNum.Ui_Dialog):#修改为从Ui_Dialog继承
    def __init__(self, title, parent = None):
        super(codeDialog_setNum, self).__init__(parent)
        self.setupUi(self,title)
        
class codeDialog_confirm(dialog_confirm.Ui_Dialog):#修改为从Ui_Dialog继承
    def __init__(self, confirmData, parent = None):
        super(codeDialog_confirm, self).__init__(parent)
        self.setupUi(self,confirmData)

class MyCanvas(FigureCanvas):
    def __init__(self):
        # self.x_data=[]
        # self.y_data=[]
        self.fig=Figure()
        self.ax=self.fig.add_subplot(111)
        # self.ax.set_xlabel("Raman shift($cm^{-1}$)")
        FigureCanvas.__init__(self, self.fig)
        self.fig.canvas.mpl_connect("button_press_event", self.call_back)   # 信号与槽
    def call_back(self,event):
        if event.button==2: # 鼠标中键
            self.ax.text(event.xdata, event.ydata*1.05, str(int(event.xdata)),color='red')
            self.ax.scatter(event.xdata, event.ydata,color='red',s=10)
            self.fig.canvas.draw_idle()
            # x=[1,2,3]
            # y=[2,3,4]
            # plt.plot(x,y)
            # plt.show()

    def myplot(self,x_data,y_data):
        self.ax.plot(x_data,y_data)

class MyLabel(QLabel):
    mySignal1 = pyqtSignal()
    def __init__(self):
        super(MyLabel, self).__init__()
        self.x0 = 0 # 要划矩形框的参数
        self.y0 = 0
        self.w = 0
        self.h = 0

        self.press_flag=False #判断在label上的鼠标按下后是否抬起，按下置为True，抬起置为False

        self.ratio=1 #label相对于图像原始尺寸的缩放比例
        # 自定义Label，额外添加四个属性，分别为要设置选区的左上角(x0,y0)和选区宽、高

        self.mouse_position=(0,0) # 用来指示当前鼠标（右键）点击的地方相对label的位置
    def paintEvent(self, event):
        super(MyLabel,self).paintEvent(event)
        painter=QPainter(self)
        # painter.begin(self)
        painter.setPen(QPen(Qt.yellow,2,Qt.DashLine))
        print('--paintevent function triggered--')
        print(QRect(self.x0,self.y0,self.w,self.h))
        painter.drawRect(QRect(self.x0,self.y0,self.w,self.h))
        # paintEvent似乎不允许传递自定义参数？因此通过调用MyLabel属性来实现参数传递
    def mousePressEvent(self, event):
        # print(self.pos()) # label左上角的位置
        self.press_flag=True
        x=event.x()
        y=event.y()
        # if event.button()==Qt.RightButton: #右键点击显示当前鼠标相对于label的位置
        self.x0=x
        self.y0=y
        self.mouse_position=(round(x/self.ratio),round(y/self.ratio))
        print("鼠标在图像中的实际位置：",self.mouse_position)
    def mouseReleaseEvent(self, event):
        self.press_flag=False #抬起则置为false
    def mouseMoveEvent(self, event): #限制鼠标在label内，超出无效
        if self.press_flag:
            x = event.x()
            y = event.y()
            if x>=0 and x<=self.width():
                self.w = x - self.x0
            if y>=0 and y<=self.height():
                self.h=y-self.y0
            self.mySignal1.emit()
            self.update()


class myWidgetScrollArea(QScrollArea):
    def __init__(self):
        print("---my widgetscrollarea checked---")
        super().__init__()

        self.last_time_move_x = 0
        self.last_time_move_y = 0

        self.scrollBarX = self.horizontalScrollBar()
        self.scrollBarY = self.verticalScrollBar()

    def eventFilter(self, QObject, QEvent):

        if QEvent.type() == QEvent.MouseMove and QEvent.button()==Qt.RightButton:
            #后半句有些问题，去掉后半句，则可用鼠标拖动滚动区域
            if self.last_time_move_x == 0:
                self.last_time_move_x = QEvent.pos().x()

            if self.last_time_move_y == 0:
                self.last_time_move_y = QEvent.pos().y()

            distance_x = self.last_time_move_x - QEvent.pos().x()
            distance_y = self.last_time_move_y - QEvent.pos().y()

            # print(self.last_time_move_y, QEvent.pos().y(), distance_y, self.scrollBarY.value())
            self.scrollBarX.setValue(self.scrollBarX.value() + distance_x)
            self.scrollBarY.setValue(self.scrollBarY.value() + distance_y)

        elif QEvent.type() == QEvent.MouseButtonRelease:
            self.last_time_move_x = self.last_time_move_y = 0

        return QWidget.eventFilter(self, QObject, QEvent)

    def mousePressEvent(self, event):
        # print(self.pos()) # l滚动区域左上角的位置
        print("鼠标相对于滚动区域的位置:",event.pos()) # 鼠标相对于滚动区域的位置
        # if event.button()==Qt.LeftButton:
        #     print('11')


def readFile(fileName):
    #输入参数为文件路径，如C:/Users/yintao/PycharmProjects/SPR_System/directory.txt
    data_x = []
    data_y = []

    print ("open "+fileName+"...")
    portion = fileName.split('.') # 获取文件后缀

    if portion[1] == "jdx":
        f = open(fileName, 'r')
        for line in f:
            if(line.startswith('##')):
                pass
            else:                
                datax,datay= line.split(',')
                data_x.append(float(datax))
                data_y.append(float(datay))
    elif portion[1] == "csv":
        import csv
        reader = csv.reader(file(fileName,'rb'))
        for line in reader:
            if len(line) == 3:
                data_x.append(float(line[0]))
                data_y.append(float(line[2]))
            else:
                pass
    elif portion[1] == "xls":
        import xlrd
        bk = xlrd.open_workbook(fileName)
        sh = bk.sheet_by_name("Sheet1")
        for i in range(sh.nrows):
            data_x.append(float(sh.cell_value(i,0)))
            data_y.append(float(sh.cell_value(i,1)))
    return [data_x,data_y]

#def plotData((plot,data)):
#    [data_x,data_y]=data
#    curve=make.curve(data_x,data_y)
#    plot.add_item(curve)   
    
def main():       
    app=QApplication(sys.argv)
    splash=QSplashScreen(QPixmap("icon/logo1.png"))
    splash.show()
    app.processEvents()
    app.setOrganizationName("IECAS")
    app.setOrganizationDomain("IECAS")
    app.setApplicationName("分子吸附特性原位测试系统界面")
    app.setWindowIcon(QIcon("icon/system.ico"))
    main=MainWindow()
    main.showMaximized()
    splash.finish(main)
    # app.connect(app, SIGNAL("lastWindowClosed()"), main.stopPump)
    # app.connect(app, SIGNAL("lastWindowClosed()"), app, SLOT("quit()"))
    app.lastWindowClosed.connect(main.stopPump)
    app.lastWindowClosed.connect(app.quit)
    app.exec_()

if __name__ == '__main__':
    main() 

