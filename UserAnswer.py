#encoding=utf-8_
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



class UserAnswer:

    def __init__(self, fileNum):
        self.user_id = None
        self.user_url = 'https://www.zhihu.com/people/' + str(self.user_id)
        self.topic_url = self.user_url + '/answers'
        self.is_del = False
        # self.proxy = None
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
        }

        self.get_Answer()

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

    def get_Answer(self):
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
            logfielname = '/log/' + dt + '_user_Topics' + '.log'
            logger = Logger(logfilename=logfielname,
                            logname='正在爬取第' + str(i + 1) + '个用户的回答').getlog()
            answer_url = 'https://www.zhihu.com/api/v4/members/'+str(self.user_id)+'/answers?include=data%5B*%5D.is_normal%2Cadmin_closed_comment%2Creward_info%2Cis_collapsed%2Cannotation_action%2Cannotation_detail%2Ccollapse_reason%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccan_comment%2Ccontent%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Cmark_infos%2Ccreated_time%2Cupdated_time%2Creview_info%2Cquestion%2Cexcerpt%2Crelationship.is_authorized%2Cvoting%2Cis_author%2Cis_thanked%2Cis_nothelp%3Bdata%5B*%5D.author.badge%5B%3F(type%3Dbest_answerer)%5D.topics&offset={0}&limit=20&sort_by=created'
            answer_count = 0

            while 1:
                try:
                    r = requests.get(answer_url, headers=self.headers, timeout=5, proxies=self.current_proxy)
                    time.sleep(3)
                    logger.info('第一次请求状态码' + str(r.status_code))
                    if r.status_code == 200:
                        j = r.json()
                        answer_count = j['paging']['totals']
                    elif r.status_code == 404:
                        self.is_del = True
                        logger.info('!!!该用户被删!!!')
                        self.delLogger(logger)
                        break
                    elif r.status_code == 401:
                        logger.info('Cookie过期，正在更换')
                        f = open('Cookies/user_answer_cookies.txt', "r")
                        Lines = f.readlines()
                        if len(Lines) == 0:
                            logger.info('备用Cookies用完！')
                            self.delLogger(logger)
                            return
                        else:
                            self.change_cookie()
                            with open('User/user_answer_loseuser_' + str(self.fileNum) + '.txt','a+') as f1:
                                f1.write(str(i + 1) + '\n')
                    elif r.status_code == 410:
                        self.is_del = True
                        logger.info('※※※资源丢失※※※')
                        self.delLogger(logger)
                        break
                    else:
                        self.delLogger(logger)
                        return

                except Exception, e:
                    logger.error('查看回答数出错！' + str(e))
                    self.current_proxy = get_IP()
                    logger.warning('切换ip代理!中断3秒！')
                    time.sleep(3)
                    continue

                else:
                    # 没有关注者的用户也要保存一下
                    if answer_count == 0:
                        logger.warning('用户没有回答！')
                        self.delLogger(logger)
                        data_plus = {'user_id': self.user_id}
                        self.mongo.db.User_Answer.insert(data_plus)
                        break
                    else:
                        offset = 0
                        while 1:
                            try:
                                soup = requests.get(answer_url.format(str(offset)), headers=self.headers, timeout=5, proxies=self.current_proxy)
                                time.sleep(3)
                                logger.info('请求状态码' + str(soup.status_code))
                            except Exception, e:
                                logger.error('请求回答出错！' + str(e))
                                self.current_proxy = get_IP()
                                logger.warning('切换ip代理!中断3秒！')
                                time.sleep(3)
                                continue
                            else:
                                answer_data = soup.json()
                                # print(answer_data)
                                data = answer_data.get('data')
                                logger.info('is_end?' + str(answer_data['paging']['is_end']))
                                if answer_data['paging']['is_end']:
                                    answer_list = []
                                    for i in range(0, len(data)):
                                        # 回答时间
                                        created_time = data[i]['created_time']
                                        # 更新时间
                                        updated_time = data[i]['updated_time']
                                        # 回答的点赞数 int
                                        vote_count = data[i]['voteup_count']
                                        # 回答id int
                                        answer_id = data[i]['id']
                                        # 回答文本
                                        answer_content = data[i]['content']
                                        # 评论数
                                        comment_count = data[i]['comment_count']
                                        # 回答者
                                        author_json = data[i]['author']
                                        # 回答者url_token
                                        author_url = data[i]['author']['url_token']

                                        # 处理url以获得新的url进入下一个界面爬问题所属的话题和问题的回答数
                                        answer_herf = data[i]['url']
                                        question_url = data[i]['question']['url']
                                        question_url = question_url.replace('questions', 'question')
                                        answer_herf = answer_herf.replace('answers', 'answer')

                                        r1 = requests.get(question_url, headers=self.headers, timeout=5,
                                                          proxies=self.current_proxy)
                                        self.content1 = BeautifulSoup(r1.content, "lxml")
                                        soup1 = self.content1
                                        # 所属话题
                                        self.topic_list = []
                                        items = soup1.find_all('div', class_='Tag QuestionTopic')
                                        for item in items:
                                            self.topic_list.append(item.get_text())

                                        # 回答数
                                        if soup1.find('h4', {'class', 'List-headerText'}) == None:
                                            self.answer_num = 0
                                        else:
                                            temp = soup1.find('h4', {'class', 'List-headerText'}).get_text().replace(
                                                ',', '')

                                            self.answer_num = int(re.search(r'^\d+', temp).group())

                                        info = {
                                            "belong_topics": self.topic_list,
                                            "answer_num": self.answer_num,
                                            "created_time": created_time,
                                            "updated_time": updated_time,
                                            "vote_count": vote_count,
                                            "answer_id": answer_id,
                                            "answer_content": answer_content,
                                            "comment_count": comment_count,
                                            "author_json": author_json,
                                            "author_url": author_url,
                                            "answer_url": answer_herf,
                                            "question_url": question_url
                                        }
                                        answer_list.append(info)
                                    data_plus = {
                                        "question_id": data[i]['question']['id'],
                                        "answer_id": data[i]['id'],
                                        'user_id': self.user_id,
                                        # "topics_count": topics_count,
                                        "answer": answer_list
                                    }

                                    self.mongo.db.User_Answer.insert(data_plus)

                                    logger.info('已获得所有用户回答！')
                                    logger.info('成功保存数据！')
                                    self.delLogger(logger)
                                    break
                                else:
                                    offset = offset + 20
                                    answer_list = []
                                    for i in range(0, len(data)):
                                        # 回答时间
                                        created_time = data[i]['created_time']
                                        # 更新时间
                                        updated_time = data[i]['updated_time']
                                        # 回答的点赞数 int
                                        vote_count = data[i]['voteup_count']
                                        # 回答id int
                                        answer_id = data[i]['id']
                                        # 回答文本
                                        answer_content = data[i]['content']
                                        # 评论数
                                        comment_count = data[i]['comment_count']
                                        # 回答者
                                        author_json = data[i]['author']
                                        # 回答者url_token
                                        author_url = data[i]['author']['url_token']
                                        # 处理url以获得新的url进入下一个界面爬问题所属的话题和问题的回答数
                                        answer_herf = data[i]['url']
                                        question_url = data[i]['question']['url']
                                        answer_herf = answer_herf.replace('answers', 'answer')
                                        question_url = question_url.replace('questions', 'question')
                                        try:
                                            r1 = requests.get(question_url, headers=self.headers, timeout=5,
                                                              proxies=self.current_proxy)
                                            time.sleep(3)
                                            logger.info('请求状态码' + str(r1.status_code))
                                        except Exception, e:
                                            logger.error('请求回答出错！' + str(e))
                                            self.current_proxy = get_IP()
                                            logger.warning('切换ip代理!中断3秒！')
                                            time.sleep(3)
                                            continue

                                        self.content1 = BeautifulSoup(r1.content, "lxml")
                                        soup1 = self.content1
                                        # 所属话题
                                        self.topic_list = []
                                        items = soup1.find_all('div', class_='Tag QuestionTopic')
                                        for item in items:
                                            self.topic_list.append(item.get_text())

                                        # 回答数
                                        if soup1.find('h4', {'class', 'List-headerText'}) == None:
                                            self.answer_num = 0
                                        else:
                                            temp = soup1.find('h4', {'class', 'List-headerText'}).get_text().replace(
                                                ',', '')

                                            self.answer_num = int(re.search(r'^\d+', temp).group())
                                        info = {
                                            "belong_topics": self.topic_list,
                                            "answer_num": self.answer_num,
                                            "created_time": created_time,
                                            "updated_time": updated_time,
                                            "vote_count": vote_count,
                                            "answer_id": answer_id,
                                            "answer_content": answer_content,
                                            "comment_count": comment_count,
                                            "author_json": author_json,
                                            "author_url": author_url,
                                            "answer_url": answer_herf,
                                            "question_url": question_url
                                        }
                                        answer_list.append(info)
                                    data_plus = {
                                        "question_id": data[i]['question']['id'],
                                        "answer_id": data[i]['id'],
                                        'user_id': self.user_id,
                                        # "topics_count": topics_count,
                                        "answer": answer_list
                                    }

                                    self.mongo.db.User_Answer.insert(data_plus)

                        self.mongo.client.close()
                        break

    def copycookies(self):
        with open('Cookies/cookies.txt', "r") as f:
            Lines = f.readlines()
        with open('Cookies/user_answer_cookies.txt','a+') as f_a:
            Lines1 = f_a.readlines()
            if len(Lines1) == 0:
                for line in Lines:
                    f_a.write(line)

    def change_cookie(self):
        with open('Cookies/user_answer_cookies.txt', "r") as f:
            Lines = f.readlines()
            dict = eval(Lines[0])
            self.type = dict['type']
            self.headers['Cookie'] = dict['Cookie']
            self.headers['x-ab-param'] = dict['x-ab-param']
        with open('Cookies/user_answer_cookies.txt', "w") as f_w:
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
        with open('Cookies/user_answer_cookies.txt', "r") as f:
            Lines = f.readlines()
        with open('Cookies/user_answer_cookies.txt', "w") as f_w:
            for line in Lines:
                if self.type != eval(line)['type']:
                    f_w.write(line)

    def get_createpoint(self):
        self.file = open('CreatePoint/userAnswer_createpoint_' + str(self.fileNum) + '.txt','a+')
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