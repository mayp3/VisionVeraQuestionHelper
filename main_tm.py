#!/usr/bin/env python
import os
import sys
import json
import hashlib
import datetime
import shutil
import re

gl_fileInputPath            = os.getcwd() + "\\FileInput\\"
gl_fileInputBakPath         = os.getcwd() + "\\FileInputBak\\"
gl_fileFilterPath           = os.getcwd() + "\\FileFilter\\"
gl_fileOutputPath           = os.getcwd() + "\\FileOutput\\"
gl_fileOutputBakPath        = os.getcwd() + "\\FileOutputBak\\"
gl_fileDistinctOutputPath   = os.getcwd() + "\\FileDistinctOutput\\"


def Log(msg):
    print('File: ' + __file__[__file__.rfind("\\")+1:] + ', [' + sys._getframe(1).f_code.co_name + '] Line '+ str(sys._getframe(1).f_lineno) + ': ' + msg)


def quesDistinctFinal():
    dictQuesTM = {}
    txtLineNumTotal = 0
    txtLineNumDis = 0
    txtLineNumDup = 0
    lines = []

    for tmFileName in os.listdir(gl_fileInputPath):
        if tmFileName.find("tm") != -1 and tmFileName.find(".txt") != -1:
            with open(gl_fileInputPath + tmFileName, "r", encoding='UTF-8') as fr:
                lines += fr.readlines()

    for line in lines:
        txtLineNumTotal += 1
        index = line.find("<|>")

        if index != -1:
            strQues = line[:index]
            if dictQuesTM.get(strQues) == None:
                dictQuesTM[strQues] = line
            else:
                txtLineNumDup += 1

    txtLineNumDis = len(dictQuesTM.keys())

    Log("txtLineNumTotal: {}, txtLineNumDis: {}, txtLineNumDup:{}".format(txtLineNumTotal, txtLineNumDis, txtLineNumDup))
    if txtLineNumTotal == txtLineNumDis + txtLineNumDup:
        with open(gl_fileDistinctOutputPath + "tm.txt", "w", encoding='UTF-8', newline='') as fw:
            for key, value in dictQuesTM.items():
                fw.write(value)

        Log("----------------tm.txt文件生成成功----------------")
        Log("----------------tm.txt文件生成完成----------------")
    else:
        Log("----------------tm.txt文件生成完成----------------")



if __name__ == "__main__":
    quesDistinctFinal()