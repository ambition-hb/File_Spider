#encoding=utf-8

import datetime
from mongodb import Mongo_3,Mongo_4

# 从数据库中抽取数据并存入新的库中

class Extractor:

    def __init__(self):
        self.user_list = []
        self.mongo = Mongo_3()

    #从回答中抽取符合要求的回答者
    def extractQuestionAnswer(self):

        print '开始提取问题回答者---'
        count = 1
        temp_list = []

        #将数据库中查找到的信息放入items,在find中加入条件
        # find条件：4 ≤ answer_num ≤ 50
        # items = self.mongo.db.answer.find({"answer_num":{"$gte":1,"$lte":3}})
        items = self.mongo.db.answer.find({"answer_num": {"$gte": 51}})
        for item in items:
            print '正在抽取第%d个'%count
            count = count + 1
            #如果回答数不符合条件
            if (item.get('answer_num') < 50):
            # if item.get('answer_num') == 0:
                print item.get('answer_num')
                continue
            #回答数符合条件
            else:
                answers = item.get('answers')
                #根据回答数长度进行遍历
                for i in range(0, len(answers)):
                    #获取answers里的author_url
                    temp = answers[i].get('author_url')
                    #如果为匿名用户，则跳过
                    if temp == None or temp == '':
                        continue
                    #否则将其存入temp_list
                    else:
                        temp_list.append(temp)



        #如果获取的temp_list为空
        if temp_list == []:
            print '提取错误'
        else:
            print '去重前回答者数量为：' + str(len(temp_list))
            #去重（采用set集合的弊端是：结果不能保留之前的顺序）
            temp_list = list(set(temp_list))
            print '去重后回答者数量为：' + str(len(temp_list))
            for user in temp_list:
                #将user_id存进temp_list列表
                self.user_list.append({'user_id':user})
        #将user_list存进数据库answerers（新创建）中
        self.mongo.db.answerers_2.insert_many(self.user_list)
        print '提取回答者完毕---'


if __name__ == "__main__":

    begin = datetime.datetime.now()
    #创建对象
    extr = Extractor()
    #抽取回答者
    extr.extractQuestionAnswer()
    end = datetime.datetime.now()
    print '用时：' + str(end - begin)

