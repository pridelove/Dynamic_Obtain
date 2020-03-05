import datetime
import hashlib
import json
import re
import time
from urllib import parse
import pymysql
import requests

#手机端Cookies
cookie = 'access_token=172cc4d72cc2274629dc0610de091f31;refresh_token=6d242cf8a9f947017fc790e7fdd79131;bili_jct=cee3e61354a4cd7968db152e8cfb949e;DedeUserID=438966151;DedeUserID__ckMd5=16d8dd755801acb0;sid=4pr83c90;SESSDATA=51df4107%2C1585933077%2Cc044d931'
access = re.findall(r'access_token=(\S+);', cookie)[0].split(";")[0]
sid = re.findall(r'sid=(\S+);', cookie)[0]
refresh = re.findall(r'refresh_token=(\S+);', cookie)[0]
# 连接数据库
db = pymysql.connect("localhost", "root", "a147896325", "dynamic")
# 使用cursor()方法获取操作游标
cursor = db.cursor()
# 假设最新一条动态数据id
dynamic_id_temp = '362878591388661566'
# 微信推送  使用Server酱
SCKEY = 'SCU56317Tf08e679b63225b0d4a9222039815fc4e5d3dc88f4ae40'
#qq群推送
group_id = 921261615

# 获取时间戳
def CurrentTime():
    current_time = int(time.mktime(datetime.datetime.now().timetuple()))
    return str(current_time)


# 时间戳转换为日期
def localtime(timestamp):
    currentTimeStamp = timestamp
    time_local = time.localtime(currentTimeStamp)
    otherStyleTime = time.strftime("%Y-%m-%d %H:%M:%S", time_local)
    return otherStyleTime


# 获取sign
def calc_sign(str):
    str += '560c52ccd288fed045859ed18bffd973'
    hash = hashlib.md5()
    hash.update(str.encode('utf-8'))
    sign = hash.hexdigest()
    return sign


# 动态搜索
def search_dynamic(word):
    # 获取当前时间戳
    time = CurrentTime()
    # url编码搜索关键字
    word_url = parse.quote(word)
    # 临时变量 用来计算变量sign
    temp_params = 'access_key=' + access + '&appkey=1d8b6e7d45233436&build=5531000&channel=bili&from_source=dynamic_search&mobi_app=android&page_no=0&page_size=50&platform=android&qn=32' \
                  + '&src=bili&statistics=%7B%22appId%22%3A1%2C%22platform%22%3A3%2C%22version%22%3A%225.53.1%22%2C%22abtest%22%3A%22%22%7D&trace_id=20200223185200029' \
                    '&ts=' + time + '&version=5.53.1.5531000&word=' + word_url
    sign = calc_sign(temp_params)
    url = 'https://api.vc.bilibili.com/search_svr/v1/Search/list_all?' + temp_params + '&sign=' + sign
    #print('url:',url)
    headers = {
        'Buvid': 'XZ2A1E522D3B659E0A6D79332FB16A9E07E91',
        'Device-ID': 'JxcvHicSI0F3QHQWahZqWmoObw1uCjk',
        'env': 'prod',
        'APP-KEY': 'android',
        'User-Agent': 'Mozilla/5.0 BiliDroid/5.53.1 (bbcallen@gmail.com) os/android model/vivo y55a mobi_app/android build/5531000 channel/bili innerVer/5531000 osVer/5.1.1 network/2',
        'Host': 'api.vc.bilibili.com',
        'Connection': 'Keep-Alive',
        'Accept-Encoding': 'gzip',
        'Cookie': sid
    }
    response = requests.request('get', url, headers=headers).json()
    #获取每页动态总数
    dynamic_num = len(response['data']['dynamic_cards'])
    for i in range(0, dynamic_num):
        # 文章内容
        card = response['data']['dynamic_cards'][i]['card']
        #进行json格式化
        card = json.loads(card)
        #使用正则 匹配关键字后面的数据,让你能够更明显的感受到你需要的文本
        card = re.findall(r'(' + word + '\S+),', str(card))
        # 判断是否存在关键字   前面搜索蜜汁会出现不完全匹配的关键字
        if card != []:
            # 动态id   https://t.bilibili.com/+id
            dynamic_id = response['data']['dynamic_cards'][i]['desc']['dynamic_id']
            # url
            #url = 'https://t.bilibili.com/' + str(dynamic_id)
            # 时间戳
            timestamp = response['data']['dynamic_cards'][i]['desc']['timestamp']
            # 转换时间戳
            time = localtime(timestamp)
            # 设置临时sql语句  判断数据库中是否已存在数据  dynamic_id为主键 动态唯一标识
            temp_sql = f'select * from dynamic_table where dynamic_id = {dynamic_id}'
            # flag = 0表示数据库无该数据
            flag = cursor.execute(temp_sql)
            if flag == 0:
                # 数据库插入语句
                sql = "insert into dynamic_table(dynamic_id,dynamic_time, dynamic_card) VALUES ('%s', '%s', '%s');" % (
                    str(dynamic_id), str(time), card[0].split('\'')[0])
                # print(sql)
                # 数据库操作
                try:
                    # 执行sql语句
                    cursor.execute(sql)
                    # 执行sql语句
                    db.commit()
                    print("数据库插入该动态%s成功" % dynamic_id)
                except Exception as e:
                    print(e)
                    # 发生错误时回滚
                    db.rollback()
                #每插入一条新的动态 判断是否是最新动态 因为B站动态搜索不是根据时间排序
                search_new_dynamic()
            #else:
                #print("数据库已有该动态%s" % dynamic_id)


# 运行主程序
def run():
    # 搜索+存放数据库
    word_list = ['点赞前', '点赞数前', '点赞数第', '点赞最多', '点赞最高', '点赞最', '点赞第一', '点赞第', '点赞量前', '点赞量最', '点赞量第', '热评送', '评论中抽',
                 '评论前', '点赞抽奖', '评论第', '热评前']
    while True:
        for word in range(0, len(word_list)):
            print("当前搜索关键词%s" % word_list[word])
            search_dynamic(word_list[word])
            # 休眠5s 避免爬取太快 导致412
            time.sleep(10)
        # 每120s更新数据库
        time.sleep(120)
    # 查询最新一条并输出


# 更新最新一条动态
def search_new_dynamic():
    global dynamic_id_temp
    #查询最新时间的一条动态
    sql = 'select * from dynamic_table order by dynamic_time Desc limit 1'
    cursor.execute(sql)
    # 获取最新的一条
    temp = cursor.fetchone()
    # 最新一条和之前保存的数据不一致 说明动态更新了
    if dynamic_id_temp != temp[0]:
        dynamic_url = 'https://t.bilibili.com/' + temp[0]
        print(dynamic_url + ' time:' + temp[1] + ' text:' + temp[2])
        # 保存最新一条数据的动态
        dynamic_id_temp = temp[0]
        # 即将发送的文本
        desp = dynamic_url + ' time:' + temp[1] + ' text:' + temp[2]
        #微信推送  用Server酱
        Wechar_Push(desp)
        #qq推送 原理 利用酷q机器人 进行推送
        Qq_Push(desp)
    else:
        print("还没有新的动态喔")
    # 每5s查询一次



# 微信推送
def Wechar_Push(desp):
    global SCKEY
    url = f'https://sc.ftqq.com/{SCKEY}.send'
    data = {
        'text': '有你感兴趣的新动态啦~',
        'desp': desp
    }
    response = requests.request('get', url=url, params=data).json()
    print(response)

#需要安装酷q小i 进行推送 然后下载http插件
def Qq_Push(desp):
    url = 'http://127.0.0.1:5700/send_group_msg'
    data = {
        'group_id': group_id,
        'message': desp,
        'auto_escape': False
    }
    response = requests.request('post', url, data=data).json()
    print(response)


if __name__ == "__main__":
    run()

