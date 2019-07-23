#encoding=utf-8

from mongodb import Mongo_3,Mongo_4
from selenium import webdriver
import datetime
import time
import re
from bs4 import BeautifulSoup
from logger import Logger

#模块一(下半部分)

class UserDetail:

    def __init__(self, fileNum):
        self.fileNum = fileNum
        self.mongo = Mongo_3()
        self.userID_list = []
        self.id = None
        #self.file----指代CreatePoint/answers_userInfo_createpoint_？
        self.file = None
        self.start = None
        self.end = None
        self.driver = None
        self.get_people_detail()

    def get_people_detail(self):
        #查找程序运行起点
        self.get_creatpoint()
        #获取动态数据
        self.driver = webdriver.PhantomJS(executable_path=r'D:\PhantomJS\phantomjs-2.1.1-windows\bin\phantomjs.exe')
        #连接数据库中的表
        items = self.mongo.db.answerers.find()
        #将获取的user_id添加到userID_list列表
        for item in items:
            self.userID_list.append(item.get('user_id'))
        dt = re.sub(r'[^0-9]', '', str(datetime.datetime.now().strftime('%Y-%m-%d-%H:%M:%S')))
        for i in xrange(self.start, self.end):
            self.id = self.userID_list[i]
            #seek()----移动0个字节，2代表从文件末尾开始
            self.file.seek(0,2)
            #组装CreatePoint文件内容，比如：1，17，70077，20180718
            dt_1 = re.sub(r'[^0-9]', '', str(datetime.datetime.now().strftime('%Y-%m-%d-%H:%M:%S')))
            News = self.type + ',' + str(i+1) + ',' + str(self.end) + ',' + str(dt_1) + '\n'
            self.file.write(News)
            #url----要爬取的数据地址
            url = "https://www.zhihu.com/people/" + str(self.id) + "/answers"
            #1----列名-列内容
            detail = {"people":self.id}
            #加载网页
            self.driver.get(url)
            #我们在使用selenium时，等待下个等待定位的元素出现，特别是web端加载的过程，都需要用到等待，而等待方式的设置是保证脚本稳定有效运行的一个非常重要的手段
            #webdriver的等待方式之一----强制等待
            time.sleep(2)
            #selenium的page_source方法可以直接返回页面源码
            content = self.driver.page_source
            #构建BeautifulSoup对象，把刚刚保存的content中的文件放入BeautifulSoup中
            #'lxml'----因为我们的content是一个字符串(string)数据，它并不是网页文件。所以这里我们告诉Beautiful soup说你就把他当一个网页文件来处理就行
            soup = BeautifulSoup(content, 'lxml')
            logfielname = '/log/' + dt + '_user_Detail' + '.log'
            logger = Logger(logfilename=logfielname,
                            logname='正在爬取第' + str(i+1) + '个用户的个人信息').getlog()
            try:
                # \S ---- 非空白字符
                gender = soup.find('svg', class_=re.compile("Icon Icon\S+male")).get('class')
            except:
                logger.warning('暂无个人资料')
            else:
                #'\w'----匹配包括下划线的任何单词字符，{0，2}----最少匹配0次且最多匹配2次
                #'$'----匹配字符串的末尾
                sex = re.search('\w{0,2}male$', gender[1]).group()
                #3----列名-列内容
                detail["gender"] = sex
                try:
                    #模拟点击
                    self.driver.find_element_by_xpath("//button[@class='Button ProfileHeader-expandButton Button--plain']").click()
                except Exception, e:
                    logger.error('该用户无详细资料！')
                else:
                    # selenium的page_source方法可以直接返回页面源码
                    content = self.driver.page_source
                    soup = BeautifulSoup(content, 'lxml')
                    items = soup.findAll('div', class_='ProfileHeader-detailItem')
                    for item in items:
                        # 3----以键值对的形式存储到derail字典里
                        # beautifulsoup--get_text()从大段html中提取文本
                        key = item.find('span', class_='ProfileHeader-detailLabel').get_text()
                        value = item.find('div', class_=re.compile("ProfileHeader-detailValue$")).get_text()
                        detail[key] = value
            logger.info('用户信息已保存！')
            self.mongo.db.User_Detail.insert(detail)
            self.delLogger(logger)
        self.mongo.client.close()
        self.driver.close()

    #删除日志手柄
    def delLogger(self, myLogger):
        for myHandler in myLogger.handlers:
            myHandler.close()
            myLogger.removeHandler(myHandler)


    #日志文件----记录每次运行的起终点，方便运行时从上次中断的地方开始
    def get_creatpoint(self):
        # 'a'----向文本文件末尾添加数据
        # '+'----表示读写模式
        self.file = open('CreatePoint/userDetail_createpoint_' + str(self.fileNum) + '.txt','a+')
        Lines = self.file.readlines()
        #如果行数为0，也就是文件为空
        if len(Lines) == 0:
            print '请输入爬取的编号，起始点和终止点:'
            Input = raw_input()
            self.type = Input.split(',')[0]
            self.start = int(Input.split(',')[1])
            # strip()----用于移除字符串头尾指定的字符（默认为空格或换行符）
            self.end = int(Input.split(',')[2].strip('\n'))
            self.file.write(Input + '\n')
        #如果行数不为0，则找到最后一行数据，将上次中断点作为新的起点
        else:
            self.type = Lines[-1].split(',')[0]
            self.start = int(Lines[-1].split(',')[1])
            self.end = int(Lines[-1].split(',')[2].strip('\n'))
