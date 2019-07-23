#encoding=utf-8

import logging
import os

#建立程序日志，以及输出日志
class Logger:
    def __init__(self, logfilename, logname):
        #创建日志文件
        self.txtCreate(logfilename)
        #创建一个logger
        self.logger = logging.getLogger(logname)
        self.logger.setLevel(logging.DEBUG)
        #创建一个handler,用于写入日志文件
        logfilename2 = logfilename[1:]
        fh = logging.FileHandler(logfilename2)
        fh.setLevel(logging.DEBUG)
        #再创建一个handler，用于输出到控制台
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        #定义handler的输出格式
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        #给logger添加handler
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)

    def getlog(self):
        return self.logger

    #建立txt文件
    def txtCreate(self, filename):
        #获取当前文件夹绝对路径
        BASE_DIR = os.path.dirname(__file__)
        full_path = BASE_DIR + filename
        #判断文件路径是否存在
        if not os.path.exists(full_path):
            #如果路径不存在，则建立路径
            if not os.path.exists(BASE_DIR+'\log'):
                os.mkdir(BASE_DIR+'\log')
            #路径建立完成后，‘w’----创建新文件
            file = open(full_path,'w')
            file.close()