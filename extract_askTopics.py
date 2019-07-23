#encoding=utf-8

import datetime
from mongodb import Mongo_3,Mongo_4

# 从数据库User_Asks中抽取数据并存入新的库中
#介于模块五和六之间

class Extractor:

    def __init__(self):
        self.user_list = []
        self.mongo = Mongo_3()

    #从UserAsk中抽取问题种子及问题ID
    def extractAskTopics(self):

        print '开始抽取问题种子及问题ID---'
        count = 1
        temp_list = {}

        items = self.mongo.db.User_Asks.find()

        for item in items:
            print '正在抽取第%d个' % count
            count = count + 1
            user_id = item.get('user_id')
            ask_lists = item.get('ask_list')
            # 根据提问数长度进行遍历
            if ask_lists:
                for ask_list in ask_lists:
                    # 获取ask_list里的author_url
                    href = ask_list.get('href')
                    question_id = ask_list.get('question_id')
                    # 如果为空，则跳过
                    if href == None or href == '':
                        continue
                    # 否则将其存入temp_list
                    else:
                        temp_list = {
                            "user_id":user_id,
                            "href": href,
                            "question_id": question_id
                        }
                    self.mongo.db.asktopics_href.insert(temp_list)
        print '提取回答者完毕---'


if __name__ == "__main__":

    begin = datetime.datetime.now()
    #创建对象
    extr = Extractor()
    #抽取提问者问题种子以及问题ID
    extr.extractAskTopics()
    end = datetime.datetime.now()
    print '用时：' + str(end - begin)

