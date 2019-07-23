#encoding=utf-8

from mongodb import MG

#返回一个IP
def get_IP():
    mongo = MG()
    try:
        #find_one()----返回符合条件的第一个文档
        proxy = mongo.db.proxy_new.find_one({},{'proxy':1,'_id':0})
        py = proxy.get('proxy')
        mongo.db.proxy_new.remove({'proxy':py})
    except Exception as e:
        print '请求IP代理出错：' + str(e)
    else:
        print '已获取新IP代理'
    return py

#返回IP列表----一次获取10个IP
def get_IPs(num=10):
    mongo = MG()
    ip_list = []
    try:
        proxies = mongo.db.proxy_new.find({},{'proxy':1,'_id':0})
        for proxy in proxies:
            ip_list.append(proxy.get('proxy'))
        for i in xrange(num):
            mongo.db.proxy_new.remove({'proxy':ip_list[i]})
    except Exception as e:
        print '请求IP代理出错：' + e
    else:
        print '已获取新IP代理'
    return ip_list[0:num]