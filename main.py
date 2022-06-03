import re
import urllib.request
import time
import json

#0表示按照时间排序;2表示按照热度排序
sort = 0
# 动态oid
oid = 666677197524697222

time.sleep(2)
comment_list = [] #创建空列表
while True:
    url = 'https://api.bilibili.com/x/v2/reply?jsonp=jsonp&pn='+str(0)+'&type=17&oid=' + str(oid) + '&sort=' + str(sort)
    #代理用户进行浏览器伪装
    headers = {
        'User-Agent':
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'
    }
    html = urllib.request.Request(url = url,headers = headers)
    data = json.loads(urllib.request.urlopen(html).read().decode('utf-8'))
    # comment = re.findall(r'"content":{"message":"(.*?)"',data,re.S) #用正则表达式扒所需要的评论内容获取，只爬了评论内容
    first_replay = data['data']['replies'][0]
    first_replay_name = first_replay['member']['uname']
    first_replay_content = first_replay['content']['message']
    print('姓名：%s' % first_replay_name)
    print('评论：%s' % first_replay_content)
    # comment_txt = open('comment.txt','w',encoding='utf-8')
    # comment_txt.write(data)
    break
    if len(comment) == 0: break
    comment_list.extend(comment) #将评论内容一个个添加进空列表

# comment_txt = open('comment.txt','w',encoding='utf-8') #创建txt文本

# for r in comment_list:
#     comment_txt.write(r) #写入txt文本