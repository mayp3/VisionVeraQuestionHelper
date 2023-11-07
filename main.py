#!/usr/bin/env python
import os
import sys
import json
import hashlib
import datetime
import shutil
import re

#------------------------------------------------------------------------------
gl_dictQuesAns = {}    #题目dict，用于题干去重，数据形式："题干":"选项+答案"
gl_quesDupNum = 0
gl_quesAndAnsAllLineNum = 0
#------------------------------------------------------------------------------


gl_fileInputPath            = os.getcwd() + "\\FileInput\\"
gl_fileInputBakPath         = os.getcwd() + "\\FileInputBak\\"
gl_fileFilterPath           = os.getcwd() + "\\FileFilter\\"    # XXXXX-Filter.txt
gl_fileOutputPath           = os.getcwd() + "\\FileOutput\\"
gl_fileOutputBakPath        = os.getcwd() + "\\FileOutputBak\\"
gl_fileDistinctOutputPath   = os.getcwd() + "\\FileDistinctOutput\\"


def Log(msg):
    print('File: ' + __file__[__file__.rfind("\\")+1:] + ', [' + sys._getframe(1).f_code.co_name + '] Line '+ str(sys._getframe(1).f_lineno) + ': ' + msg)

def test():
    list1 = ['a','b','c','d','a']
    list2 = [1,2,3,4,5]
    dictTest = dict(zip(list1, list2))
    dictOut = {}
    dictOut[dictTest] = 'OK'
    for key,value in dictTest.items():
            # 输出去重后的题干与答案
            Log("key:{}".format(key))
            Log("value:{}".format(value))

    for key,value in dictOut.items():
        # 输出去重后的题干与答案
        Log("key:{}".format(key))
        Log("value:{}".format(value))

def test1():
    global gl_dictSingleChoice
    i = 0
    listtmp = [1,2]

    
    if i == 0:
        gl_dictSingleChoice["a"] = listtmp
    listtmp = []
    listtmp.clear()

    print(gl_dictSingleChoice.keys(), gl_dictSingleChoice.values())

    print(gl_fileInputPath)

def test2():
    # 打开源文件和目标文件
    with open('input.txt', 'r') as input_file, open('output.txt', 'w') as output_file:
        # 创建一个集合用于存储已经处理过的字符串
        processed_lines = set()

        # 逐行读取源文件内容
        for line in input_file:
            # 截取每行<|>之前的字符串
            data = line.split('<|>')[0]  # 使用 strip() 方法去除首尾的空白符
            # 去重
            if data not in processed_lines:
                processed_lines.add(data)
                # 将截取并去重后的字符串写入目标文件中
                output_file.write(data + '\n')


def getFilterQuestionAnswerMatch():
    """
    获取单选题、多选题、判断题文件或者获取混合题
    文件中只获取code=200，msg="成功"那一行的数据, 剔除报文头
    剔除多余数据（只有题干没有答案），保证题干和答案的json数据一一映射
    @prarm questionFilterFile 过滤掉协议头后的文件路径
    """

    inputFileList = []
    lineFilterList = []
    questionNumInput = 0    # 题干输入数
    questionNumOutput = 0   # 题干输出数


    # 获取文件输入路径下的文件
    for inputFileName in os.listdir(gl_fileInputPath):
        if inputFileName.find("视联") != -1 and inputFileName.find(".txt") != -1:
            inputFileList.append(inputFileName)

    for inputFile in inputFileList:
        lineFilterList = []

        outputFilterFileName = inputFile[0:inputFile.rfind(".")] + "-Filter.txt"

        with open(gl_fileInputPath + inputFile, "r", encoding='UTF-8') as fr:
            lines = fr.readlines()
            for line in lines:
                if line.find('"code":200,"msg":"成功"') != -1:  # 筛选出code=200，msg="成功"那一行的数据
                    lineFilterList.append(line)

                    if line.find('"isTrue":1') != -1:   # 对答案行计数
                        questionNumInput += 1

            question1 = ""
            answer = ""
            outputFilterlist = []
            resultFlag = False
    
            for lineFilter in lineFilterList:
                if lineFilter.find("question") != -1:
                    question1 = lineFilter
                    break

            startLineNum = lineFilterList.index(question1)

            for i in range(startLineNum + 1, len(lineFilterList)):
                if lineFilterList[i].find("question") != -1 and lineFilterList[i].find('"isTrue":null') != -1:    # 提取题干
                    question1 = lineFilterList[i]
                elif lineFilterList[i].find('"isTrue":1,"value"') != -1: # 提取答案
                    #question1 = re.sub(re.compile("\n"), "\\n", question1)
                    outputFilterlist.append(question1)
                    question1 = ""
                    answer = lineFilterList[i]
                    outputFilterlist.append(answer)

            for outputFilter in outputFilterlist:
                if outputFilter.find("question") != -1:
                    pass
                else:
                    questionNumOutput += 1
 
            # 考虑到原始文件开头是答案的情况下，即第一条有效数据不是question
            if questionNumInput == questionNumOutput + 1:
                questionNumInput = questionNumOutput

            if questionNumInput != questionNumOutput:
                resultFlag = False
                Log("Error:ResultLineNum Error!!! questionNumInput: {}, questionNumOutput: {}".format(questionNumInput, questionNumOutput))
            else:
                resultFlag = True

            if resultFlag == True:
                with open(gl_fileFilterPath + outputFilterFileName, "w", encoding='UTF-8', newline='') as fw:
                    for outputFilter in outputFilterlist:
                        if outputFilter.find('"code":200,"msg":"成功"') != -1:
                            fw.write(outputFilter)

        # shutil.move(gl_fileInputPath + inputFileName, gl_fileInputBakPath + inputFileName)  # 将输入文件移动到输入备份路径

        getGenerateQuesAndAnsToText(outputFilterFileName, outputFilterlist)

def getGenerateQuesAndAnsToText(questionFilterFile, questionStrList):
    """
    从json提取题干、选项和答案，并以（题目 选项）\n答案的形式写入文件“XXX_题目与答案”中（有重复的题干），同时以“题目:选项+答案”的形式放入dict
    @param questionFilterFile 题目Filter文件名
    @param questionStrList 题目
    """
    global gl_dictQuesAns
    global gl_quesDupNum
    global gl_quesAndAnsAllLineNum

    jsonData = ""
    questionTitle = ""
    listAns = []

    outputFile = questionFilterFile[0:questionFilterFile.rfind("-")] + "-题目与答案.txt"

    with open(gl_fileOutputPath + outputFile, "w", encoding='UTF-8', newline='') as fw:
        for questionStr in questionStrList:
            if questionStr.find("question") != -1:
                question = json.loads(questionStr)
                questionTitle = question.get("data").get("question").get("name")
                jsonData = re.sub(re.compile("\n"), "\\n", questionTitle) + "<|>"
                jsonData = repr(jsonData).strip("'")    # 去除两边的引号"'"
            else:
                answerStr = ""
                answers = json.loads(questionStr)
                for answer in answers.get("data"):
                    if(answer.get("isTrue") == 1):
                         answerStr += answer.get("value") + "||"
                answerStr = answerStr[:answerStr.rindex("||")]

                # 填入全局字典dictQuestionAndAnswer，格式{str:list}，list中存放选项和答案，分别为list[0]和list[1]
                if len(listAns) == 0:
                    listAns.append(answerStr)
                else:
                    Log("listAns isn't empty!!!")

                if questionTitle in gl_dictQuesAns:
                    gl_quesDupNum += 1
                else:
                    gl_dictQuesAns[questionTitle] = listAns
                listAns = []    # 不能用list.clear()，只能用[]，详情请百度list.clear()和list = []的区别

                answerStr = re.sub(re.compile("\n"), "\\n", answerStr)
                answerStr = repr(answerStr)
                jsonData = answerStr.strip("'") + '\n'  # 去除两边的引号"'"

            gl_quesAndAnsAllLineNum += 1
            #jsonData = jsonData.strip("'")
            fw.write(jsonData)
 
    #try:
    #    os.remove(questionFilterFile)
    #except:
    #    Log("Remove FilterFile Fail!!!")

    Log(outputFile)


def getQuestionAnswerDistinct():
    """
    题目文件中的题干去重
    """
    global gl_dictQuesAns
    global gl_quesDupNum
    global gl_quesAndAnsAllLineNum

    curr_time = datetime.datetime.now()
    timestamp = datetime.datetime.strftime(curr_time, '%Y%m%d%H%M%S')
    keyTmp = ''
    listValueTmp = ''

    Log("----------------题目文件生成开始----------------")

    for file in os.listdir(gl_fileOutputPath):
        if file.find("题目与答案") != -1:
            shutil.move(gl_fileOutputPath + file, gl_fileOutputBakPath + file)

    with open(gl_fileDistinctOutputPath + "tm_" + timestamp + ".txt", "w", encoding='UTF-8', newline='') as fw:
        for key, listValue in gl_dictQuesAns.items():
            keyTmp = re.sub(re.compile("\n"), "\\n", key) + "<|>"
            keyTmp = repr(keyTmp)
            fw.write(keyTmp.strip("'"))

            if len(listValue) == 1:
                listValueTmp = re.sub(re.compile("\n"), "\\n", listValue[0])
                listValueTmp = repr(listValueTmp)
                fw.write(listValueTmp.strip("'") + "\n")
            else:
                Log("gl_dictQuesAns's value is incomplete")

    Log("fileAllLineNum = {}".format(gl_quesAndAnsAllLineNum))
    Log("questionAndAnswerDupNum = {}".format(gl_quesDupNum * 2))
    Log("distinctQuesNum = {}".format(len(gl_dictQuesAns.keys())))
    Log("distinctAnsNum = {}".format(len(gl_dictQuesAns.values())))

    if gl_quesAndAnsAllLineNum == gl_quesDupNum * 2 + len(gl_dictQuesAns.keys()) + len(gl_dictQuesAns.values()):
        Log("----------------答案题目文件生成成功----------------")
        Log("----------------答案题目文件生成完成----------------")
    else:
        Log("----------------答案题目文件生成失败----------------")


def main():

    global gl_dictQuesAns
    global gl_quesDupNum
    global gl_quesAndAnsAllLineNum

    #test()
    #test1()
    #test2()

    # 数据筛选
    getFilterQuestionAnswerMatch()

    # 题目去重
    getQuestionAnswerDistinct()
    Log("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")



if __name__ == "__main__":
    main()