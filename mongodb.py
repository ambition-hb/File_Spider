# encoding=utf-8
from pymongo import MongoClient

# 建立数据库连接

class MG:
    def __init__(self):
        #建立连接
        uri = 'mongodb://spider:123456@192.168.3.138:20250'
        self.client = MongoClient(uri)
        # self.client = MongoClient("localhost", 27017)
        self.db = self.client.zhihu

class Mongo_3:
    def __init__(self):
        # 建立连接
        # self.client = MongoClient("localhost",27017)
        uri = 'mongodb://spider:123456@192.168.3.138:20250'
        self.client = MongoClient(uri)
        # self.client = MongoClient("192.168.3.138", 20250)
        self.db = self.client.el_2019

class Mongo_4:
    def __init__(self):
        # 建立连接
        uri = 'mongodb://dev:Chenshi2017@58.206.96.135:20250'
        self.client = MongoClient(uri)
        self.db = self.client.PM_shi




