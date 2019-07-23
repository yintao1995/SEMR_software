# -*- coding: utf-8 -*-
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import QApplication
# from pyExcelerator import Workbook
     
class dialogTable(QtWidgets.QDialog):
    def __init__(self,label,parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        
        # 创建table和model
        self.table = QtWidgets.QTableView(parent=self)
        self.model = QtGui.QStandardItemModel(parent=self)
        self.model.setHorizontalHeaderLabels(label)
        self.table.setModel(self.model)
     
        # 创建添加按钮
        button1 = QtWidgets.QPushButton(u'Add', parent=self)
        button2 = QtWidgets.QPushButton(u'Remove',parent=self)
        button3 = QtWidgets.QPushButton(u'Load',parent=self)
        button4 = QtWidgets.QPushButton(u'Save',parent=self)
        # 添加信号槽
        button1.clicked.connect(self.add)
        button2.clicked.connect(self.remove)
        button3.clicked.connect(self.load)
        button4.clicked.connect(self.save)
        
        # 创建ButtonBox，用户确定和取消
        buttonBox = QtWidgets.QDialogButtonBox(parent=self)
        buttonBox.setOrientation(QtCore.Qt.Horizontal) # 设置为水平方向
        buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok) # 确定和取消两个按钮
        # 连接信号和槽
        buttonBox.accepted.connect(self.accept) # 确定
        buttonBox.rejected.connect(self.reject) # 取消
     
        # 创建一个垂直布局，用于防止表格和按钮
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.table)
        layout_ = QtWidgets.QHBoxLayout()
        layout_.addWidget(button1)
        layout_.addWidget(button2)
        layout_.addWidget(button3)
        layout_.addWidget(button4)
        layout.addLayout(layout_)
        layout.addWidget(buttonBox)
        self.setLayout(layout)
        
     
    def add(self): # 添加一行 (checked~~)
        row = self.model.rowCount()
        self.model.appendRow((
            QtGui.QStandardItem(""),
            QtGui.QStandardItem(""),
            ))
        index = self.model.index(row, 0)
        self.table.setFocus()
        self.table.setCurrentIndex(index)
        self.table.edit(index)


    def remove(self): # 移除一行 (checked)
        index = self.table.currentIndex()
        self.model.removeRow(index.row())
        
    
    def load(self): # 将excel表格(前两列)加载到界面里(fixed)
        import xlrd
        bk = xlrd.open_workbook('calibrate.xls')
        sh = bk.sheet_by_name("Sheet1")
        for i in range(sh.nrows):
            print(sh.cell_value(i,0))
            print(sh.cell_value(i,1))
            self.model.appendRow((QtGui.QStandardItem("%.3f"%sh.cell_value(i,0)),
            QtGui.QStandardItem("%.3f"%sh.cell_value(i,1))))
        QtWidgets.QMessageBox.information(self,self.tr("Load Done"),
                     self.tr("Load the calibrate.xls file successfully!!!"))
    
    def save(self): # 将界面里的表格数据存储到excel
        import xlwt
        w = xlwt.Workbook()
        ws=w.add_sheet('Sheet1')
        # print(self.model.rowCount())
        for i in range(self.model.rowCount()):
            index_x=self.model.index(i,0)
            index_y=self.model.index(i,1)
            temp_x=float(self.model.data(index_x,0))
            temp_y=float(self.model.data(index_y,0))
            # print(temp_x, temp_y)
            ws.write(i,0,temp_x)
            ws.write(i,1,temp_y)
        w.save('calibrate.xls')
        # w.save('test.xls')
        QtWidgets.QMessageBox.information(self,self.tr("Save Done"),
                     self.tr("Saved in calibrate.xls successfully!!!"))

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    mainWindow = dialogTable(['Time','A'])
    mainWindow.show()
    sys.exit(app.exec_())
     
     
