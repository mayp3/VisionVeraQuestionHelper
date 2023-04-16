#!/usr/bin/env python
import os
import sys
import json
import hashlib
import datetime
import shutil

gl_dictSingleChoice = {}    #单选题dict，用于题干去重，数据形式："题干":"选项+答案"
gl_dictMultiChoice = {}     #多选题dict，用于题干去重，数据形式："题干":"选项+答案"
gl_singleQuesDupNum = 0
gl_multiQuesDupNum = 0
gl_singleQuesAndAnsAllLineNum = 0
gl_multiQuesAndAnsAllLineNum = 0
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
    获取单选题、多选题文件
    """

    outputFileList = []
    outputFlag = False

    for inputFileName in os.listdir(gl_fileInputPath):
        outputFlag = False

        if inputFileName.find("选题_") != -1:
            outputFileName = inputFileName[0:inputFileName.find("_")] + "_Filter" + inputFileName[inputFileName.rfind("_"):]
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


def getFilterQuestionAnswerMatch(choiceFilterFile):
    """
    剔除多余数据（只有题干没有答案），保证题干和答案的json数据一一映射
    @prarm choiceFilterFile 过滤掉协议头后的文件路径
    """
    choiceQuestionNumInput = 0
    choiceQuestionNumOutput = 0

    # choiceFilterFile就是Filter文件
    with open(choiceFilterFile, "r", encoding='UTF-8') as fr:
        lines = fr.readlines()
        for line in lines:
            if line.find('"isTrue":1') != -1:
                choiceQuestionNumInput += 1

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
            listOut.append(question1.strip().replace('\\n', '') + "\n")
            question1 = ""
            answer = lines[i]
            listOut.append(answer.strip().replace('\\n', '') + "\n")

    for out in listOut:
        if out.find("question") != -1:
            pass
        else:
            choiceQuestionNumOutput += 1
 
    # 考虑到原始文件开头是答案的情况下，即第一条有效数据不是question
    if choiceQuestionNumInput == choiceQuestionNumOutput + 1:
        choiceQuestionNumInput = choiceQuestionNumOutput

    if choiceQuestionNumInput != choiceQuestionNumOutput:
        resultFlag = False
        Log("ResultLineNum Error!!! choiceQuestionNumInput: {}, choiceQuestionNumOutput: {}".format(choiceQuestionNumInput, choiceQuestionNumOutput))
    else:
        resultFlag = True

    if resultFlag == True:
        getGenerateQuesAndAnsToText(choiceFilterFile, listOut)



def getGenerateQuesAndAnsToText(choiceFilterFile, choiceStrList):
    """
    从json提取题干、选项和答案，并以（题目 选项）\n答案的形式写入文件“XXX_题目与答案”中（有重复的题干），同时以“题目:选项+答案”的形式放入dict
    @param choiceFilterFile 选择题Filter文件路径
    @param choiceStrList 选择题
    """
    global gl_dictSingleChoice
    global gl_dictMultiChoice
    global gl_singleQuesDupNum
    global gl_multiQuesDupNum
    global gl_singleQuesAndAnsAllLineNum
    global gl_multiQuesAndAnsAllLineNum

    questionType = 0    # 0:单选题，1:多选题
    jsonData = ""
    questionTitle = ""
    choiceOption = ""
    listChoiceOptAndAns = []

    choiceFilterFileName = choiceFilterFile[choiceFilterFile.rfind("\\")+1:]    #获取文件名，不要"\"
    outputChoiceFile = choiceFilterFileName[0:choiceFilterFileName.find("_")] + "_题目与答案" + choiceFilterFileName[choiceFilterFileName.rfind("_"):]
    
    if outputChoiceFile.find("单选题") != -1:
        questionType = 0
    elif outputChoiceFile.find("多选题") != -1:
        questionType = 1
    else:
        Log("questionType Error!!! questionType = {}".format(questionType))
        sys.exit(0)

    #currentPath = os.getcwd()
    with open(gl_fileOutputPath + outputChoiceFile, "w", encoding='UTF-8', newline='') as fw:
        for choiceStr in choiceStrList:
            if choiceStr.find("question") != -1:
                question = json.loads(choiceStr)
                questionTitle = "题目: " + question.get("data").get("question").get("name").strip() + "\n"
                answerList = question.get("data").get("question").get("answerList")
                
                option=['A','B','C','D','E','F','G','H']
                i = 0
                choiceOption = ""
                for answer in answerList:
                    choiceOption += option[i]
                    choiceOption += "."
                    choiceOption += answer.get("value")
                    choiceOption += "\n"
                    i += 1
                jsonData = questionTitle + choiceOption
            else:
                answerStr = "答案: "
                answers = json.loads(choiceStr)
                for answer in answers.get("data"):
                    if(answer.get("isTrue") == 1):
                         answerStr += answer.get("value") + "  |  "
                answerStr = answerStr[:answerStr.rindex("  |  ")]

                # 填入全局字典dictQuestionAndAnswer，格式{str:list}，list中存放选项和答案，分别为list[0]和list[1]
                if len(listChoiceOptAndAns) == 0:
                    listChoiceOptAndAns.append(choiceOption.strip())
                    listChoiceOptAndAns.append(answerStr.strip())
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
                listChoiceOptAndAns = []    # 不能用list.clear()，只能用[]，详情请百度list.clear()和list = []的区别

                jsonData = answerStr.strip() + "\n"

            if questionType == 0:   #单选题
                gl_singleQuesAndAnsAllLineNum += 1
            elif questionType == 1: #多选题
                gl_multiQuesAndAnsAllLineNum += 1
            fw.write(jsonData)

 
    try:
        os.remove(choiceFilterFile)
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
            if key.strip().find("题目:") != -1:
                fw.write(key.strip() + "\n")   # 题目和选项在同一行
            else:
                Log("gl_dictSingleChoice's key no have 题目")

            if len(listValue) == 2:
                fw.write(listValue[0].strip() + "\n")
                fw.write(listValue[1].strip() + "\n")
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
            if key.strip().find("题目:") != -1:
                fw.write(key.strip() + "\n")   # 题目和选项在同一行
            else:
                Log("gl_dictMultiChoice's key no have 题目")

            if len(listValue) == 2:
                fw.write(listValue[0].strip() + "\n")
                fw.write(listValue[1].strip() + "\n")
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


"""   
def getMultiChoiceFileDistinct():
    currentPath = os.getcwd()
    inputFilePath = currentPath + "/FileOutput/"
    outputFilePath = currentPath + "/FileDistinctOutput/"
    dictQuesAns = {}
    listQuestion = []
    listAnswer = []
    listAllLine = []    #存放所有的题干和答案，存在重复的打印出来
    strQuesAndAnsLine = ""
    questionDupNum = 0  #重复题干和答案的个数
    fileLineNum = 0     #遍历文件总行数

    curr_time = datetime.datetime.now()
    timestamp = datetime.datetime.strftime(curr_time,'%m%d')

    Log("--------------多选题文件生成-开始----------------")

    for file in os.listdir(inputFilePath):
        if file.find("多选题") != -1:
            with open(inputFilePath + file, "r", encoding='UTF-8') as fr:
                lines = fr.readlines()
                for line in lines:
                    if line.strip().find("题目:") != -1:
                        strQuesAndAnsLine = line.strip()
                        listQuestion.append(line.strip())
                    elif line.strip().find("答案:") != -1:
                        if strQuesAndAnsLine.find("题目:") != -1:
                            strQuesAndAnsLine += line.strip()
                            if strQuesAndAnsLine not in listAllLine:
                                listAllLine.append(strQuesAndAnsLine)
                                strQuesAndAnsLine = ""
                            else:
                                Log(strQuesAndAnsLine)    #打印出重复数据
                                questionDupNum += 1
                        else:
                            strQuesAndAnsLine = ""
                        listAnswer.append(line.strip())
                    else:
                        Log("QuestionLine Error!!!")
                    fileLineNum += 1

    if len(listAllLine) * 2 != fileLineNum:
        Log("ChoiceQuestion's Number Error!!!, Question Happen Duplicate!!!")

    if len(listQuestion) == len(listAnswer):
        # 题干和答案组成键-值对
        dictQuesAns = dict(zip(listQuestion, listAnswer))
    else:
        Log("QuestionAndAnswer's Num Diff!!!")

    Log("MultiChoiceFileLineNum = {}".format(fileLineNum))
    Log("MultiChoiceQuestionAndAnswerDupNum = {}".format(questionDupNum * 2))
    Log("MultiChoiceDistinctLineNum = {}".format(len(dictQuesAns.keys()) * 2))
    
    with open(outputFilePath + "/" + "多选题_题目与答案_Distinct_" + timestamp + ".txt", "w", encoding='UTF-8', newline='') as fw:
        for key,value in dictQuesAns.items():
            # 输出去重后的题干与答案
            fw.write(key + "\n")
            fw.write(value + "\n")

    Log("--------------多选题文件生成-成功----------------")


def getStrMD5():
    ori_pwd = '视联网监控调度平台（唐古拉）正在与正常极光推送监控，仅发生监控调度平台视联网链路中断的情况下，极光终端会出现什么画面？ '
    byte_ori_pwd = ori_pwd.encode('utf-8')  #bytes对象
    Log(hashlib.md5(byte_ori_pwd).hexdigest())
    #8c81eab9acbe2a2fbc8445fa4a9b15fd  都是这个
"""

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

def main():
    singleChoiceFlag = False
    multiChoiceFlag = False
    #test()
    #test1()
    outputFileList = getFilterTextList()
    if outputFileList != None:
        for outputFile in outputFileList:
            if outputFile.find("单选题") != -1:
                singleChoiceFlag = True
            elif outputFile.find("多选题") != -1:
                multiChoiceFlag = True
            else:
                Log("Error:Not Single OR Multi!!!")
                sys.exit(0)
            
            # 过滤掉协议包头、只有题干没有答案的无用数据
            getFilterQuestionAnswerMatch(outputFile)
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
    


if __name__ == "__main__":
    main()