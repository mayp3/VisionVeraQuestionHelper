#!/usr/bin/env python
import os
import sys
import json
import hashlib
import datetime
import shutil
import re

gl_dictSingleChoice = {}    #单选题dict，用于题干去重，数据形式："题干":"选项+答案"
gl_dictMultiChoice = {}     #多选题dict，用于题干去重，数据形式："题干":"选项+答案"
gl_dictJudge = {}           #判断题dict，用于题干去重，数据形式："题干":"选项+答案"
gl_singleQuesDupNum = 0
gl_multiQuesDupNum = 0
gl_judgeQuesDupNum = 0
gl_singleQuesAndAnsAllLineNum = 0
gl_multiQuesAndAnsAllLineNum = 0
gl_judgeQuesAndAnsAllLineNum = 0


#------------------------------------------------------------------------------
gl_dictQuesAns = {}    #题目dict，用于题干去重，数据形式："题干":"选项+答案"
gl_quesDupNum = 0
gl_quesAndAnsAllLineNum = 0
#------------------------------------------------------------------------------


gl_fileInputPath            = os.getcwd() + "\\FileInput\\"
gl_fileInputBakPath         = os.getcwd() + "\\FileInputBak\\"
gl_fileFilterPath           = os.getcwd() + "\\FileFilter\\"
gl_fileOutputPath           = os.getcwd() + "\\FileOutput\\"
gl_fileOutputBakPath        = os.getcwd() + "\\FileOutputBak\\"
gl_fileDistinctOutputPath   = os.getcwd() + "\\FileDistinctOutput\\"


def Log(msg):
    print('File: ' + __file__[__file__.rfind("\\")+1:] + ', [' + sys._getframe(1).f_code.co_name + '] Line '+ str(sys._getframe(1).f_lineno) + ': ' + msg)


def getFilterTextList():
    """
    获取单选题、多选题、判断题文件
    或者获取混合题
    """

    outputFileList = []
    outputFlag = False

    for inputFileName in os.listdir(gl_fileInputPath):
        outputFlag = False

        if inputFileName.find("选题_") != -1 or inputFileName.find("判断题_") != -1 or inputFileName.find("题目_") != -1 :
            outputFileName = inputFileName[0:inputFileName.rfind("_")] + "_Filter" + inputFileName[inputFileName.rfind("_"):]
            with open(gl_fileInputPath + inputFileName, "r", encoding='UTF-8') as fr:
                lines = fr.readlines()
            
            with open(gl_fileFilterPath + outputFileName, "w", encoding='UTF-8', newline='') as fw:
                for line in lines:
                    if line.find('"code":200,"msg":"成功"') != -1:
                        outputFlag = True
                        fw.write(line)
            
            if outputFlag == True:
                outputFileList.append(gl_fileFilterPath + outputFileName)
                Log(outputFileName)
            
            shutil.move(gl_fileInputPath + inputFileName, gl_fileInputBakPath + inputFileName)

    if len(outputFileList) > 0:
        return outputFileList


def getFilterQuestionAnswerMatch(questionFilterFile):
    """
    剔除多余数据（只有题干没有答案），保证题干和答案的json数据一一映射
    @prarm questionFilterFile 过滤掉协议头后的文件路径
    """
    questionNumInput = 0
    questionNumOutput = 0

    # questionFilterFile
    with open(questionFilterFile, "r", encoding='UTF-8') as fr:
        lines = fr.readlines()
        for line in lines:
            if line.find('"isTrue":1') != -1:
                questionNumInput += 1

    question1 = ""
    answer = ""
    listOut = []
    resultFlag = False
    
    for line in lines:
        if line.find("question") != -1:
            question1 = line
            break

    startLineNum = lines.index(question1)

    for i in range(startLineNum + 1, len(lines)):
        if lines[i].find("question") != -1 and lines[i].find('"isTrue":null') != -1:    # 提取题干
            question1 = lines[i]
        elif lines[i].find('"isTrue":1,"value"') != -1: # 提取答案
            listOut.append(question1.replace('\\n', '') + "\n")
            question1 = ""
            answer = lines[i]
            listOut.append(answer.replace('\\n', '') + "\n")

    for out in listOut:
        if out.find("question") != -1:
            pass
        else:
            questionNumOutput += 1
 
    # 考虑到原始文件开头是答案的情况下，即第一条有效数据不是question
    if questionNumInput == questionNumOutput + 1:
        questionNumInput = questionNumOutput

    if questionNumInput != questionNumOutput:
        resultFlag = False
        Log("ResultLineNum Error!!! questionNumInput: {}, questionNumOutput: {}".format(questionNumInput, questionNumOutput))
    else:
        resultFlag = True

    if resultFlag == True:
        getGenerateQuesAndAnsToText(questionFilterFile, listOut)


def getGenerateQuesAndAnsToText(questionFilterFile, questionStrList):
    """
    从json提取题干、选项和答案，并以（题目 选项）\n答案的形式写入文件“XXX_题目与答案”中（有重复的题干），同时以“题目:选项+答案”的形式放入dict
    @param questionFilterFile 选择题Filter文件路径
    @param questionStrList 题
    """
    global gl_dictSingleChoice
    global gl_dictMultiChoice
    global gl_dictJudge
    global gl_singleQuesDupNum
    global gl_multiQuesDupNum
    global gl_judgeQuesDupNum
    global gl_singleQuesAndAnsAllLineNum
    global gl_multiQuesAndAnsAllLineNum
    global gl_judgeQuesAndAnsAllLineNum

    questionType = 0    # 0:单选题，1:多选题，2:判断题
    jsonData = ""
    questionTitle = ""
    choiceOption = ""
    listChoiceOptAndAns = []

    choiceFilterFileName = questionFilterFile[questionFilterFile.rfind("\\")+1:]    #获取文件名，不要"\"
    outputChoiceFile = choiceFilterFileName[0:choiceFilterFileName.find("_")] + "_题目与答案" + choiceFilterFileName[choiceFilterFileName.rfind("_"):]
    
    if outputChoiceFile.find("单选题") != -1:
        questionType = 0
    elif outputChoiceFile.find("多选题") != -1:
        questionType = 1
    elif outputChoiceFile.find("判断题") != -1:
        questionType = 2
    else:
        Log("questionType Error!!! questionType = {}".format(questionType))
        sys.exit(0)

    #currentPath = os.getcwd()
    with open(gl_fileOutputPath + outputChoiceFile, "w", encoding='UTF-8', newline='') as fw:
        for choiceStr in questionStrList:
            if choiceStr.find("question") != -1:
                question = json.loads(choiceStr)
                questionTitle = question.get("data").get("question").get("name") + "\n"
                answerList = question.get("data").get("question").get("answerList")
                
                option=['A','B','C','D','E','F','G','H']
                #i = 0
                #choiceOption = ""
                #for answer in answerList:
                #    choiceOption += option[i]
                #    choiceOption += "."
                #    choiceOption += answer.get("value")
                #    choiceOption += "\n"
                #    i += 1
                #jsonData = questionTitle + choiceOption
                jsonData = questionTitle
            else:
                answerStr = ""
                answers = json.loads(choiceStr)
                for answer in answers.get("data"):
                    if(answer.get("isTrue") == 1):
                         answerStr += answer.get("value") + "||"
                answerStr = answerStr[:answerStr.rindex("||")]

                # 填入全局字典dictQuestionAndAnswer，格式{str:list}，list中存放选项和答案，分别为list[0]和list[1]
                if len(listChoiceOptAndAns) == 0:
                    #listChoiceOptAndAns.append(choiceOption)
                    listChoiceOptAndAns.append(answerStr)
                else:
                    Log("listChoiceOptAndAns isn't empty!!!")

                if questionType == 0:   # 单选题
                    if questionTitle in gl_dictSingleChoice:
                        gl_singleQuesDupNum += 1
                        #Log("重复单选题目: " + questionTitle)
                    else:
                        gl_dictSingleChoice[questionTitle] = listChoiceOptAndAns
                elif questionType == 1: #多选题
                    if questionTitle in gl_dictMultiChoice:
                        gl_multiQuesDupNum += 1
                        #Log("重复多选题目: " + questionTitle)
                    else:
                        gl_dictMultiChoice[questionTitle] = listChoiceOptAndAns
                elif questionType == 2: #判断题
                    if questionTitle in gl_dictJudge:
                        gl_judgeQuesDupNum += 1
                        #Log("重复多选题目: " + questionTitle)
                    else:
                        gl_dictJudge[questionTitle] = listChoiceOptAndAns
                listChoiceOptAndAns = []    # 不能用list.clear()，只能用[]，详情请百度list.clear()和list = []的区别

                jsonData = answerStr + "\n"

            if questionType == 0:   #单选题
                gl_singleQuesAndAnsAllLineNum += 1
            elif questionType == 1: #多选题
                gl_multiQuesAndAnsAllLineNum += 1
            elif questionType == 2: #判断题
                gl_judgeQuesAndAnsAllLineNum += 1
            fw.write(jsonData)

 
    try:
        os.remove(questionFilterFile)
    except:
        Log("Remove FilterFile Fail!!!")

    Log(outputChoiceFile)


def getSingleChoiceFileDistinct():
    """
    单选题文件中的题干去重
    """
    global gl_dictSingleChoice
    global gl_singleQuesDupNum
    global gl_singleQuesAndAnsAllLineNum

    curr_time = datetime.datetime.now()
    timestamp = datetime.datetime.strftime(curr_time, '%m%d')

    Log("----------------单选题文件生成开始----------------")

    for file in os.listdir(gl_fileOutputPath):
        if file.find("选题_") != -1:
            shutil.move(gl_fileOutputPath + file, gl_fileOutputBakPath + file)

    with open(gl_fileDistinctOutputPath + "单选题_题目与答案_Distinct_" + timestamp + ".txt", "w", encoding='UTF-8', newline='') as fw:
        for key, listValue in gl_dictSingleChoice.items():
            #if key.find("题目:") != -1:
            fw.write(key + "<|>")
            #else:
            #    Log("gl_dictSingleChoice's key no have 题目")

            if len(listValue) == 1:
                fw.write(listValue[0] + "\n")
                #fw.write(listValue[1] + "\n")
                fw.write("\n")
            else:
                Log("gl_dictSingleChoice's value is incomplete")

    Log("SingleChoiceFileAllLineNum = {}".format(gl_singleQuesAndAnsAllLineNum))
    Log("SingleChoiceQuestionAndAnswerDupNum = {}".format(gl_singleQuesDupNum * 2))
    Log("SingleChoiceDistinctQuesNum = {}".format(len(gl_dictSingleChoice.keys())))
    Log("SingleChoiceDistinctAnsNum = {}".format(len(gl_dictSingleChoice.values())))

    if gl_singleQuesAndAnsAllLineNum == gl_singleQuesDupNum * 2 + len(gl_dictSingleChoice.keys()) + len(gl_dictSingleChoice.values()):
        Log("----------------单选题文件生成成功----------------")
        Log("----------------单选题文件生成完成----------------")
    else:
        Log("----------------单选题文件生成失败----------------")


def getMultiChoiceFileDistinct():
    """
    多选题文件中题干去重
    """
    global gl_dictMultiChoice
    global gl_multiQuesDupNum
    global gl_multiQuesAndAnsAllLineNum

    curr_time = datetime.datetime.now()
    timestamp = datetime.datetime.strftime(curr_time,'%m%d')

    Log("----------------多选题文件生成开始----------------")

    for file in os.listdir(gl_fileOutputPath):
        if file.find("选题_") != -1:
            shutil.move(gl_fileOutputPath + file, gl_fileOutputBakPath + file)

    with open(gl_fileDistinctOutputPath + "多选题_题目与答案_Distinct_" + timestamp + ".txt", "w", encoding='UTF-8', newline='') as fw:
        for key, listValue in gl_dictMultiChoice.items():
            #if key.find("题目:") != -1:
            fw.write(key + "<|>")
            #else:
            #    Log("gl_dictMultiChoice's key no have 题目")

            if len(listValue) == 1:
                fw.write(listValue[0] + "\n")
                #fw.write(listValue[1] + "\n")
                fw.write("\n")
            else:
                Log("gl_dictMultiChoice's value is incomplete")

    Log("MultiChoiceFileAllLineNum = {}".format(gl_multiQuesAndAnsAllLineNum))
    Log("MultiChoiceQuestionAndAnswerDupNum = {}".format(gl_multiQuesDupNum * 2))
    Log("MultiChoiceDistinctQuesNum = {}".format(len(gl_dictMultiChoice.keys())))
    Log("MultiChoiceDistinctAnsNum = {}".format(len(gl_dictMultiChoice.values())))

    if gl_multiQuesAndAnsAllLineNum == gl_multiQuesDupNum * 2 + len(gl_dictMultiChoice.keys()) + len(gl_dictMultiChoice.values()):
        Log("----------------多选题文件生成成功----------------")
        Log("----------------多选题文件生成完成----------------")
    else:
        Log("----------------多选题文件生成失败----------------")

def getJudgeFileDistinct():
    """
    判断题文件中的题干去重
    """
    global gl_dictJudge
    global gl_judgeQuesDupNum
    global gl_judgeQuesAndAnsAllLineNum

    curr_time = datetime.datetime.now()
    timestamp = datetime.datetime.strftime(curr_time, '%m%d')

    Log("----------------判断题文件生成开始----------------")

    for file in os.listdir(gl_fileOutputPath):
        if file.find("判断题_") != -1:
            shutil.move(gl_fileOutputPath + file, gl_fileOutputBakPath + file)

    with open(gl_fileDistinctOutputPath + "判断题_题目与答案_Distinct_" + timestamp + ".txt", "w", encoding='UTF-8', newline='') as fw:
        for key, listValue in gl_dictJudge.items():
            #if key.find("题目:") != -1:
            fw.write(key + "<|>")
            #else:
            #    Log("gl_dictJudge's key no have 题目")

            if len(listValue) == 1:
                fw.write(listValue[0] + "\n")
                #fw.write(listValue[1] + "\n")
                fw.write("\n")
            else:
                Log("gl_dictJudge's value is incomplete")

    Log("JudgeQuesAndAnsAllLineNum = {}".format(gl_judgeQuesAndAnsAllLineNum))
    Log("JudgeQuestionAndAnswerDupNum = {}".format(gl_judgeQuesDupNum * 2))
    Log("JudgeDistinctQuesNum = {}".format(len(gl_dictJudge.keys())))
    Log("JudgeDistinctAnsNum = {}".format(len(gl_dictJudge.values())))

    if gl_judgeQuesAndAnsAllLineNum == gl_judgeQuesDupNum * 2 + len(gl_dictJudge.keys()) + len(gl_dictJudge.values()):
        Log("----------------判断题文件生成成功----------------")
        Log("----------------判断题文件生成完成----------------")
    else:
        Log("----------------判断题文件生成失败----------------")

"""
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
"""


def getFilterQuestionAnswerMatchGeneral(questionFilterFile):
    """
    剔除多余数据（只有题干没有答案），保证题干和答案的json数据一一映射
    @prarm questionFilterFile 过滤掉协议头后的文件路径
    """
    questionNumInput = 0
    questionNumOutput = 0

    # questionFilterFile
    with open(questionFilterFile, "r", encoding='UTF-8') as fr:
        lines = fr.readlines()
        for line in lines:
            if line.find('"isTrue":1') != -1:
                questionNumInput += 1

    question1 = ""
    answer = ""
    listOut = []
    resultFlag = False
    
    for line in lines:
        if line.find("question") != -1:
            question1 = line
            break

    startLineNum = lines.index(question1)

    for i in range(startLineNum + 1, len(lines)):
        if lines[i].find("question") != -1 and lines[i].find('"isTrue":null') != -1:    # 提取题干
            question1 = lines[i]
        elif lines[i].find('"isTrue":1,"value"') != -1: # 提取答案
            #question1 = re.sub(re.compile("\n"), "\\n", question1)
            listOut.append(question1)
            question1 = ""
            answer = lines[i]
            listOut.append(answer)

    for out in listOut:
        if out.find("question") != -1:
            pass
        else:
            questionNumOutput += 1
 
    # 考虑到原始文件开头是答案的情况下，即第一条有效数据不是question
    if questionNumInput == questionNumOutput + 1:
        questionNumInput = questionNumOutput

    if questionNumInput != questionNumOutput:
        resultFlag = False
        Log("ResultLineNum Error!!! questionNumInput: {}, questionNumOutput: {}".format(questionNumInput, questionNumOutput))
    else:
        resultFlag = True

    if resultFlag == True:
        getGenerateQuesAndAnsToTextGeneral(questionFilterFile, listOut)



def getGenerateQuesAndAnsToTextGeneral(questionFilterFile, questionStrList):
    """
    从json提取题干、选项和答案，并以（题目 选项）\n答案的形式写入文件“XXX_题目与答案”中（有重复的题干），同时以“题目:选项+答案”的形式放入dict
    @param questionFilterFile 题目Filter文件路径
    @param questionStrList 题目
    """
    global gl_dictQuesAns
    global gl_quesDupNum
    global gl_quesAndAnsAllLineNum

    jsonData = ""
    questionTitle = ""
    listAns = []

    filterFileName = questionFilterFile[questionFilterFile.rfind("\\")+1:]    #获取文件名，不要"\"
    outputFile = filterFileName[0:filterFileName.find("_")] + "与答案" + filterFileName[filterFileName.find("_"):filterFileName.find("_", -21)] + filterFileName[filterFileName.rfind("_"):]

    with open(gl_fileOutputPath + outputFile, "w", encoding='UTF-8', newline='') as fw:
        for questionStr in questionStrList:
            if questionStr.find("question") != -1:
                question = json.loads(questionStr)
                questionTitle = question.get("data").get("question").get("name")
                jsonData = re.sub(re.compile("\n"), "\\n", questionTitle) + "<|>"
                jsonData = repr(jsonData)
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
                jsonData = answerStr + '\n'

            gl_quesAndAnsAllLineNum += 1

            fw.write(jsonData.strip("'"))
 
    try:
        os.remove(questionFilterFile)
    except:
        Log("Remove FilterFile Fail!!!")

    Log(outputFile)


def getFileDistinctGeneral():
    """
    题目文件中的题干去重
    """
    global gl_dictQuesAns
    global gl_quesDupNum
    global gl_quesAndAnsAllLineNum

    curr_time = datetime.datetime.now()
    timestamp = datetime.datetime.strftime(curr_time, '%Y%m%d')
    keyTmp = ''
    listValueTmp = ''

    Log("----------------题目文件生成开始----------------")

    for file in os.listdir(gl_fileOutputPath):
        if file.find("题目与答案") != -1:
            shutil.move(gl_fileOutputPath + file, gl_fileOutputBakPath + file)

    with open(gl_fileDistinctOutputPath + "混合题目与答案_Distinct_" + timestamp + ".txt", "w", encoding='UTF-8', newline='') as fw:
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
        Log("----------------混合题目文件生成成功----------------")
        Log("----------------混合题目文件生成完成----------------")
    else:
        Log("----------------混合题目文件生成失败----------------")


def main():
    singleChoiceFlag = False
    multiChoiceFlag = False
    judgeFlag = False
    generalFlag= False

    global gl_dictQuesAns
    global gl_quesDupNum
    global gl_quesAndAnsAllLineNum

    #test()
    #test1()
    outputFileList = getFilterTextList()
    if outputFileList != None:
        for outputFile in outputFileList:
            if outputFile.find("题") != -1 and outputFile.find(".txt") != -1:
                generalFlag = True
            else:
                Log("Error:Not Single OR Multi!!!")
                sys.exit(0)
            
            # 过滤掉协议包头、只有题干没有答案的无用数据
            if singleChoiceFlag == True or multiChoiceFlag == True or judgeFlag == True:
                getFilterQuestionAnswerMatch(outputFile)
            elif generalFlag == True:
                getFilterQuestionAnswerMatchGeneral(outputFile)
            else:
                Log("Error:No Question!!!")
    else:
        Log("Not Have InputFile!!!")
        sys.exit(0)
    

    if singleChoiceFlag == True:
        # 单选题去重
        getSingleChoiceFileDistinct()
    Log("***********************************************************************************")

    if multiChoiceFlag == True:
        # 多选题去重
        getMultiChoiceFileDistinct()
    Log("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
    
    if judgeFlag == True:
        # 判断题去重
        getJudgeFileDistinct()
    Log("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
    
    if generalFlag == True:
        # 题目去重
        getFileDistinctGeneral()


if __name__ == "__main__":
    main()