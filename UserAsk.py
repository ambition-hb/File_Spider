#encoding=utf-8
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

#模块五

class UserAsk:

    def __init__(self, fileNum):
        self.user_id = None
        self.user_url = 'https://www.zhihu.com/people/' + str(self.user_id) +'/asks'
        self.is_del = False
        self.proxy = None
        self.userID_list = []
        self.fileNum = fileNum
        self.file = None
        self.start = None
        self.end = None
        self.type = None
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

        self.get_Asks()

    def parser(self, url, logger):

        while 1:
            try:
                r = requests.get(url, headers=self.headers, timeout=5, proxies=self.current_proxy)
                time.sleep(3)
                logger.info('请求状态码' + str(r.status_code))
                if r.status_code == 404:
                    logger.warning('该用户被删！无法获得用户信息!!!')
                    self.is_del = True
                    break
                if r.status_code == 200:
                    self.content = BeautifulSoup(r.content, "lxml")
                    break
                if r.status_code == 410:
                    logger.warning('资源丢失')
                    break
            except Exception as e:
                logger.error('请求出错！' + str(e))
                self.current_proxy = get_IP()
                logger.warning('切换ip代理!中断3秒！')
                time.sleep(3)
                continue

    def get_Asks(self):
        self.copycookies()
        self.get_createpoint()
        items = self.mongo.db.answerers_1.find()
        for item in items:
            self.userID_list.append(item.get('user_id'))
        self.current_proxy = get_IP()
        self.get_cookie()
        dt = re.sub(r'[^0-9]', '', str(datetime.datetime.now().strftime('%Y-%m-%d-%H:%M:%S')))
        for i in xrange(self.start, self.end):
            self.file.seek(0,2)
            dt1 = re.sub(r'[^0-9]', '', str(datetime.datetime.now().strftime('%Y-%m-%d')))
            News = self.type + ','+ str(i+1) + ',' + str(self.end) + ',' + str(dt1) + '\n'
            self.file.write(News)
            self.user_id = self.userID_list[i]
            logfielname = '/log/' + dt + '_user_Asks' + '.log'
            logger = Logger(logfilename=logfielname,
                            logname='正在爬取第' + str(i + 1) + '个用户的提问信息').getlog()
            #https://www.zhihu.com/api/v4/members/cang-hai-qing-yue/questions?include=data%5B*%5D.created%2Canswer_count%2Cfollower_count%2Cauthor%2Cadmin_closed_comment&offset={0}&limit=20
            asks_url = 'https://www.zhihu.com/api/v4/members/'+str(self.user_id)+'/questions?include=data%5B*%5D.created%2Canswer_count%2Cfollower_count%2Cauthor%2Cadmin_closed_comment&offset={0}&limit=20'
            asks_count = 0

            while 1:
                try:
                    r = requests.get(asks_url, headers=self.headers, timeout=5, proxies=self.current_proxy)
                    time.sleep(3)
                    logger.info('第一次请求状态码' + str(r.status_code))
                    if r.status_code == 200:
                        j = r.json()
                        asks_count = j['paging']['totals']
                    elif r.status_code == 404:
                        self.is_del = True
                        logger.info('!!!该用户被删!!!')
                        self.delLogger(logger)
                        break
                    elif r.status_code == 401:
                        logger.info('Cookie过期，正在更换')
                        f = open('Cookies/user_asks_cookies.txt', "r")
                        Lines = f.readlines()
                        if len(Lines) == 0:
                            logger.info('备用Cookies用完！')
                            self.delLogger(logger)
                            return
                        else:
                            self.change_cookie()
                    elif r.status_code == 410:
                        self.is_del = True
                        logger.info('※※※资源丢失※※※')
                        self.delLogger(logger)
                        break
                    else:
                        self.delLogger(logger)
                        return

                except Exception, e:
                    logger.error('查看提问数出错！' + str(e))
                    self.current_proxy = get_IP()
                    logger.warning('切换ip代理!中断3秒！')
                    time.sleep(3)
                    continue

                else:
                    # 没有提问的用户也要保存一下
                    if asks_count == 0:
                        logger.warning('用户没有提问问题！')
                        self.delLogger(logger)
                        data_plus = {'user_id': self.user_id, "asks_count": 0}
                        self.mongo.db.User_Asks.insert(data_plus)
                        break
                    else:
                        offset = 0
                        while 1:
                            try:
                                soup = requests.get(asks_url.format(str(offset)), headers=self.headers, timeout=5, proxies=self.current_proxy)
                                time.sleep(3)
                                logger.info('请求状态码' + str(soup.status_code))
                            except Exception, e:
                                logger.error('请求用户提问出错！' + str(e))
                                self.current_proxy = get_IP()
                                logger.warning('切换ip代理!中断3秒！')
                                time.sleep(3)
                                continue
                            else:
                                asks_data = soup.json()
                                data = asks_data.get('data')
                                logger.info('is_end?' + str(asks_data['paging']['is_end']))
                                if asks_data['paging']['is_end']:
                                    ask_list = []
                                    for i in range(0, len(data)):
                                        info = {
                                            "question_id":data[i]['id'],
                                            "content":data[i]['title'],
                                            "answer_count":data[i]['answer_count'],
                                            "follower_count":data[i]['follower_count'],
                                            "create_time":data[i]['created'],
                                            "update_time":data[i]['updated_time'],
                                            "href":data[i]['url']
                                        }
                                        ask_list.append(info)
                                    data_plus = {
                                        'user_id': self.user_id,
                                        "asks_count": asks_count,
                                        "ask_list": ask_list
                                    }
                                    self.mongo.db.User_Asks.insert(data_plus)
                                    logger.info('已获得所有用户关注话题！')
                                    logger.info('成功保存数据！')
                                    self.delLogger(logger)
                                    break
                                else:
                                    offset = offset + 20
                                    ask_list = []
                                    for i in range(0, len(data)):
                                        info = {
                                            "question_id":data[i]['id'],
                                            "content":data[i]['title'],
                                            "answer_count":data[i]['answer_count'],
                                            "follower_count":data[i]['follower_count'],
                                            "create_time":data[i]['created'],
                                            "update_time":data[i]['updated_time'],
                                            "href":data[i]['url']
                                        }
                                        ask_list.append(info)
                                    data_plus = {
                                        'user_id': self.user_id,
                                        "asks_count": asks_count,
                                        "ask_list": ask_list
                                    }
                                    self.mongo.db.User_Asks.insert(data_plus)

                        self.mongo.client.close()
                        break

    def copycookies(self):
        with open('Cookies/cookies.txt', "r") as f:
            Lines = f.readlines()
        with open('Cookies/user_asks_cookies.txt','a+') as f_a:
            Lines1 = f_a.readlines()
            if len(Lines1) == 0:
                for line in Lines:
                    f_a.write(line)

    def change_cookie(self):
        with open('Cookies/user_asks_cookies.txt', "r") as f:
            Lines = f.readlines()
            dict = eval(Lines[0])
            self.type = dict['type']
            self.headers['Cookie'] = dict['Cookie']
            self.headers['x-ab-param'] = dict['x-ab-param']
        with open('Cookies/user_asks_cookies.txt', "w") as f_w:
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
        with open('Cookies/user_asks_cookies.txt', "r") as f:
            Lines = f.readlines()
        with open('Cookies/user_asks_cookies.txt', "w") as f_w:
            for line in Lines:
                if self.type != eval(line)['type']:
                    f_w.write(line)

    def get_createpoint(self):
        self.file = open('CreatePoint/userAsk_createpoint_' + str(self.fileNum) + '.txt','a+')
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

    def delLogger(self, myLogger):
        for myHandler in myLogger.handlers:
            myHandler.close()
            myLogger.removeHandler(myHandler)




