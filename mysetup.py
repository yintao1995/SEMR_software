# -*- coding: utf-8 -*-
"""
Created on Sun Oct 26 16:55:50 2014

@author: cesc
"""
from distutils.core import setup
import py2exe
import sys
import glob

sys.argv.append('py2exe')

script=[{"script":"main.py",
         'icon_resource':[(1,r'icon\system.ico'),]
    }]

py2exe_option={"includes":["sip","decimal","scipy.sparse.csgraph._validation",
                           "scipy.special._ufuncs_cxx","pylab","numpy",'guidata','guiqwt','PyQt4.QtSvg'],
               "dll_excludes":["MSVCP90.dll"],
    }
data_files=[(r'guiqwt\images',glob.glob(r'C:\Python27\Lib\site-packages\guiqwt\images\*.*')),
            (r'guidata\images',glob.glob(r'C:\Python27\Lib\site-packages\guidata\images\*.*')),
            (r'imageformats',glob.glob(r'C:\Python27\Lib\site-packages\PyQt4\plugins\imageformats\*.*')),
            (r'icon',glob.glob(r'icon\*.*')),
            (r'origData',glob.glob(r'origData\*.*'))
            ]

setup(windows=script,options={'py2exe':py2exe_option},data_files=data_files)
