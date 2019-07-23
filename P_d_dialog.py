import sys
from P_d import *
from Thickness_P import calc_main,assess_data
import numpy as np
from PyQt5.QtWidgets import QApplication, QDialog, QMessageBox


class MyPdDialog(QDialog, Ui_Dialog):
    def __init__(self,parent=None):
        super(MyPdDialog, self).__init__(parent)
        self.setupUi(self)
        self.pushButton.clicked.connect(self.calc_result)
        self.pushButton_2.clicked.connect(self.assess_result)

    def calc_result(self):
        try:
            theta_list = self.lineEdit.text()
            theta_list = [float(theta) for theta in theta_list.split(',')]

            wavelength_list = self.lineEdit_2.text()
            wavelength_list = [float(wavelength) for wavelength in wavelength_list.split(',')]

            d_start = float(self.lineEdit_3.text())
            calc_min = float(self.lineEdit_4.text())
            calc_max = float(self.lineEdit_5.text())
            P_list = np.arange(calc_min, calc_max + 0.01, 0.01)
            accuracy = float(self.lineEdit_6.text())
            result = calc_main(theta_list, wavelength_list, d_start, P_list, accuracy)
            self.textEdit.setText(str(result[0]))
            self.textEdit_2.setText(str(result[1]))

        except:
            QMessageBox.warning(self, 'Warning', 'Input Format Wrong')
            pass

    def assess_result(self):
        try:
            d_list=self.textEdit.toPlainText()
            d_list=[float(p) for p in d_list[1:-1].split(',')]
            assess_d=assess_data(d_list)
            self.lineEdit_7.setText(str(round(assess_d[0],3)))
            self.lineEdit_8.setText(str(round(assess_d[2],3))+'%')

            P_list=self.textEdit_2.toPlainText()
            P_list = [float(t) for t in P_list[1:-1].split(',')]
            assess_P=assess_data(P_list)
            self.lineEdit_9.setText(str(round(assess_P[0],3)))
            self.lineEdit_10.setText(str(round(assess_P[2],3))+'%')

        except:
            pass