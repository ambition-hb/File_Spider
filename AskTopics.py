#-*- coding:utf-8 –*-

import requests
import time
import re
import datetime
from bs4 import BeautifulSoup
from logger import Logger
from mongodb import Mongo_3,Mongo_4
from proxy_pool import get_IP
import sys
reload(sys)
sys.setdefaultencoding('utf8')

#模块六

class AskTopics:

    def __init__(self, fileNum):
        self.user_id = None
        self.is_del = False
        self.href_list = []
        #用户提问href
        self.url_list = []
        self.fileNum = fileNum
        self.file = None
        self.start = None
        self.end = None
        self.type = None
        self.answer_info = None
        self.mongo = Mongo_3()
        self.current_proxy = None
        self.content = None
        self.headers = {
            'Accept': 'textml,application/json,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, sdch',
            'Accept-Language': 'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4,zh-TW;q=0.2',
            'Host': 'www.zhihu.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.81 Safari/537.36',
            'Referer': 'http://www.zhihu.com/',
            'Cookie': None,
            'x-udid':None,
        }

        self.get_askTopic()

    def parser(self,i, url, logger):
        while 1:
            try:
                r = requests.get(url, headers=self.headers, timeout=5, proxies=self.current_proxy)
                time.sleep(3)
                logger.info('请求状态码' + str(r.status_code))
                if r.status_code == 404:
                    logger.warning('该用户被删！无法获得用户信息!!!')
                    self.is_del = True
                    return
                elif r.status_code == 200:
                    self.content = BeautifulSoup(r.content, "lxml")
                    return
                elif r.status_code == 401:
                        logger.info('Cookie过期，正在更换')
                        f = open('Cookies/ask_topics_cookies.txt', "r")
                        Lines = f.readlines()
                        if len(Lines) == 0:
                            logger.info('备用Cookies用完！')
                            self.delLogger(logger)
                            sys.exit(0)
                        else:
                            self.change_cookie()
                else:
                    self.delLogger(logger)
                    sys.exit(0)
            except Exception as e:
                logger.error('请求出错！' + str(e))
                self.current_proxy = get_IP()
                logger.warning('切换ip代理!中断3秒！')
                time.sleep(3)
                continue

    # 静态用户信息
    def get_askTopic(self):
        self.copycookies()
        self.get_createpoint()
        #从User_Asks库出发遍历用户
        items = self.mongo.db.asktopics_href.find()
        for item in items:
            self.href_list.append(item.get('href'))
        self.current_proxy = get_IP()
        self.get_cookie()

        dt = re.sub(r'[^0-9]', '', str(datetime.datetime.now().strftime('%Y-%m-%d-%H:%M:%S')))
        for i in xrange(self.start, self.end):
            self.is_del = False
            self.content = None
            self.file.seek(0,2)
            dt1 = re.sub(r'[^0-9]', '', str(datetime.datetime.now().strftime('%Y-%m-%d')))
            News = self.type + ','+ str(i+1) + ',' + str(self.end) + ',' + str(dt1) + '\n'
            self.file.write(News)

            user_url = self.href_list[i].replace('questions','question')

            logfielname = '/log/' + dt + '_ask_Topics' + '.log'
            logger = Logger(logfilename=logfielname,
                            logname='正在爬取第' + str(i + 1) + '个用户的提问所属话题').getlog()

            if self.content == None:
                self.parser(i, user_url, logger)

            if self.is_del == True:
                self.delLogger(logger)
                continue
            else:
                soup = self.content

            # 提问问题所属话题
            topics = []
            if soup.find('div', {'class': 'Tag QuestionTopic'}) == None:
                logger.warning('该提问问题没有添加所属话题标签！')
            else:
                items = soup.findAll('div', {'class': 'Tag QuestionTopic'})

                for item in items:
                    topics.append(item.get_text())

            data_plus = {
                "href": user_url,
                "topics": topics
            }

            self.mongo.db.Ask_Topics.insert(data_plus)

            logger.info('已获取用户的记录信息')
            self.delLogger(logger)
            self.mongo.client.close()


    def copycookies(self):
        with open('Cookies/cookies.txt', "r") as f:
            Lines = f.readlines()
        with open('Cookies/ask_topics_cookies.txt','a+') as f_a:
            Lines1 = f_a.readlines()
            if len(Lines1) == 0:
                for line in Lines:
                    f_a.write(line)

    def change_cookie(self):
        with open('Cookies/ask_topics_cookies.txt', "r") as f:
            Lines = f.readlines()
            dict = eval(Lines[0])
            self.type = dict['type']
            self.headers['Cookie'] = dict['Cookie']
            self.headers['x-ab-param'] = dict['x-ab-param']
        with open('Cookies/ask_topics_cookies.txt', "w") as f_w:
            for line in Lines[1:]:
                f_w.write(line)

    def get_cookie(self):
        with open('Cookies/cookies.txt', "r") as f:
            Lines = f.readlines()
            for line in Lines:
                dict = eval(line)
                if self.type == dict['type']:
                    self.headers['Cookie'] = dict['Cookie']
                    self.headers['x-ab-param'] = dict['x-ab-param']
        with open('Cookies/ask_topics_cookies.txt', "r") as f:
            Lines = f.readlines()
        with open('Cookies/ask_topics_cookies.txt', "w") as f_w:
            for line in Lines:
                if self.type != eval(line)['type']:
                    f_w.write(line)

    def get_createpoint(self):
        self.file = open('CreatePoint/askTopics_createpoint_' + str(self.fileNum) + '.txt','a+')
        Lines = self.file.readlines()
        if len(Lines) == 0:
            print '请输入爬取的Cookie编号、起始点和终止点：'
            Input = raw_input()
            self.type = Input.split(',')[0]
            self.start = int(Input.split(',')[1])
            self.end = int(Input.split(',')[2].strip('\n'))
            self.file.write(Input + '\n')
        else:
            self.type = Lines[-1].split(',')[0]
            self.start = int(Lines[-1].split(',')[1])
            self.end = int(Lines[-1].split(',')[2].strip('\n'))

    # 删除日志手柄
    def delLogger(self, myLogger):
        for myHandler in myLogger.handlers:
            myHandler.close()
            myLogger.removeHandler(myHandler)