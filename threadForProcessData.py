# -*- coding: utf-8 -*-
"""
Created on Fri Nov 21 09:19:25 2014

@author: cesc
"""

import os
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import main

class ThreadForProcessData(QThread):
    
    def __init__(self, lock, parent=None):
        super(ThreadForProcessData, self).__init__(parent)
        self.lock = lock
        self.stopped = False
        self.mutex = QMutex()
        self.path = None
        self.completed = False
        print("init success")

    def initialize(self, path, gap):
        self.stopped = False
        self.path = path
        self.gap = gap
        self.completed = False
        self.data_ad=[]
        self.data_de=[]
        self.result_ad=[]
        self.result_de=[]
        print("initialize success")

    def stop(self):
        try:
            self.mutex.lock()
            self.stopped = True
        finally:
            self.mutex.unlock()


    def isStopped(self):
        try:
            self.mutex.lock()
            return self.stopped
        finally:
            self.mutex.unlock()


    def run(self):
        self.processFiles(self.path,self.gap)
        self.stop()
        self.emit(SIGNAL("finished(QString)"), self.path+"\\"+"adsorption"+self.flag_ad+".xls"
                                ";"+self.path+"\\"+"desorption"+self.flag_de+".xls")


    def processFiles(self, path, gap):
        if self.isStopped():
            return
        filenames=[]
        self.flag_ad="0"
        self.flag_de="0"
        for filename in os.listdir(path):
            #用来判断文件夹中是否有之前处理过的数据，记录下之前处理数据的下标
            if str(filename).startswith("adsorption_spectrum") and str(filename).endswith(".xls"):
                self.flag_ad=str(int(str(filename)[-5])+1)
            if str(filename).startswith("desorption_spectrum") and str(filename).endswith(".xls"):
                self.flag_de=str(int(str(filename)[-5])+1)    
                
            if str(filename).endswith(".jdx"):
                filenames.append(filename)
                
        flag=0
        for filename in filenames:
            if flag==0:
                f=open("directory.txt",'w')
                f.write(path+"\\"+filename)
                f.close()
                flag=1
            
            if self.isStopped():
                return
            data=main.readFile(unicode(path+"\\"+filename))
            if str(filename).endswith("ef.jdx"):
                self.data_ad[1:1]=[data]
                self.data_de[1:1]=[data]
#            [self.data_x1,self.data_y1]=data
            elif str(filename).endswith("ark.jdx"):
                self.data_ad[0:0]=[data]
                self.data_de[0:0]=[data]
#            [self.data_x2,self.data_y2]=data
            else:
                if str(filename).startswith("a") and str(filename).endswith(".jdx"):
                    self.data_ad.append(data)
                elif str(filename).startswith("d") and str(filename).endswith(".jdx"):
                    self.data_de.append(data)
            self.emit(SIGNAL("indexed(QString)"), filename)
            
        import xlwt   
        file_ad = xlwt.Workbook() 
        table_ad = file_ad.add_sheet('Sheet1',cell_overwrite_ok=True)
        file_ad.save(path+"\\"+'adsorption_spectrum'+self.flag_ad+'.xls') 
        count=0
        flag=0
        for i in range(2,len(self.data_ad),gap):
            print(i)
            temp = main.slotTest2DataProcess(self.data_ad[0][0],self.data_ad[0][1],self.data_ad[1][0],self.data_ad[1][1],self.data_ad[i][0],self.data_ad[i][1])
            self.result_ad.append(temp)
            
            if flag==0:
                data_x_smooth = temp[0]
                data_y_smooth = temp[1]
                
                if count==0:
                    for j in range(len(data_x_smooth)):
                        table_ad.write(j,count,data_x_smooth[j])
                        table_ad.write(j,count+1,data_y_smooth[j])
                else:
                    for j in range(len(data_y_smooth)):
                        table_ad.write(j,count+1,data_y_smooth[j])
                
                count=count+1 
                if count%10==0:
                    print("................")
                    file_ad.save(path+"\\"+'adsorption_spectrum'+self.flag_ad+'.xls')
            flag=(flag+1)%5
            self.emit(SIGNAL("processed(QString)"), "adsorption --- %i "%i)
        file_ad.save(path+"\\"+'adsorption_spectrum'+self.flag_ad+'.xls')   
            
        
        file_de = xlwt.Workbook() 
        table_de = file_de.add_sheet('Sheet1',cell_overwrite_ok=True)
        file_de.save(path+"\\"+'desorption_spectrum'+self.flag_de+'.xls')
        count=0
        flag=0
        for i in range(2,len(self.data_de),gap):
            print(i)
            temp = main.slotTest2DataProcess(self.data_de[0][0],self.data_de[0][1],self.data_de[1][0],self.data_de[1][1],self.data_de[i][0],self.data_de[i][1])
            self.result_de.append(temp)
            
            if flag==0:
                data_x_smooth = temp[0]
                data_y_smooth = temp[1]
        
                if count==0:
                    for j in range(len(data_x_smooth)):
                        table_de.write(j,count,data_x_smooth[j])
                        table_de.write(j,count+1,data_y_smooth[j])
                else:
                    for j in range(len(data_y_smooth)):
                        table_de.write(j,count+1,data_y_smooth[j])
                    
                count=count+1  
                if count%10==0:
                    print("......................")
                    file_de.save(path+"\\"+'desorption_spectrum'+self.flag_de+'.xls')
            flag=(flag+1)%10
            self.emit(SIGNAL("processed(QString)"), "desorption --- %i "%i)
        file_de.save(path+"\\"+'desorption_spectrum'+self.flag_de+'.xls')
        self.completed = True
