import urllib.request
import json
from pathlib import Path
import time
import sys
from requests import request

from loguru import logger

logger.remove()
logger.add(sys.stdout,
           format="<green>{time:YYYY/MM/DD HH:mm:ss}</green> <red>|</red> <green>{level}</green> <red>|</red> {message}")

# 楼中楼评论不计入
# 重复评论不计入

# 配置文件名（请跟脚本放置在同一目录）
config_json_name = 'config.json'

class Utils:
    """ 工具类 """
    @staticmethod
    def load_json(file_name_path: str) -> dict:
        """ 读取json文件 """
        try:
            with open(file_name_path,'r',encoding='utf8')as(jsonFile):
                json_data = json.load(jsonFile)
                return json_data
        except Exception as e:
            pass

    @staticmethod
    def save_json_file(file_name_with_path: str, json_data: dict) -> None:
        """ 接收数据并保存为json文件 """
        # 加入 ensure_ascii=False 选项。导出json文件不乱码
        # jsondata = json.dumps(json_data, ensure_ascii=False, separators=(',',':'))
        jsondata = json.dumps(json_data, ensure_ascii=False)
        with open( Path(file_name_with_path), 'w', encoding='utf-8') as write_file:
            write_file.write(jsondata)
            write_file.close()

class Config:
    """ 配置类 """
    # 配置数据
    data: dict = {
        # 动态oid
        "oid": -1,
        # 等级最低限制
        "level": -1,
        # 0表示按照时间排序; 2表示按照热度排序
        "sort": 0,
        # 单次请求出错的重试次数
        "times": 3
    }
    data = Utils.load_json(config_json_name)


class Process:
    """ 获取&处理动态评论数据类 """
    def __init__(self) -> None:
        # 评论分页
        self.page = 1
        # 评论总列表
        self.comment_list = []
        # UP主的UID
        self.upper_uid = None
        # 评论总数
        self.comment_num = 0

    def run(self):
        """ 主线程  """
        # 单个请求出错重试记录次数
        request_times = 0
        while True:
            response = self.get_api()

            # 如果请求出错，重试
            if request_times <= Config.data['times'] and response is None:
                request_times += 1
                logger.error("请求动态评论出现错误，开始重试第%s次" % str(request_times))
                continue
            elif response is not None:
                request_times = 0
            
            # 获取UP主UID
            if self.upper_uid is None:
                self.upper_uid = response['data']['upper']['mid']
                logger.info("UP主UID：%s" % str(self.upper_uid))

            if len(response['data']['replies']) == 0:
                logger.info("共获取到%s条评论，其中不包括楼中楼与UP主评论。" % str(self.comment_num))
                break
            else:
                # 提取该请求里的所有用户数据
                self.get_sub_user_data(response)

            # 分页自增
            self.page += 1

    def get_api(self) -> dict:
        """ 请求动态评论数据 """
        # 单次请求间隔0.3秒
        time.sleep(0.3)
        # 开始请求
        url: str = 'https://api.bilibili.com/x/v2/reply?jsonp=jsonp&pn=%d&type=17&oid=%d&sort=%d' % (
            self.page,
            Config.data['oid'],
            Config.data['sort']
        )
        # UA配置
        headers: dict[str, str] = {
            'User-Agent':
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'
        }
        try:
            html: urllib.request.Request = urllib.request.Request(
                url = url,
                headers = headers
            )
            response: dict = json.loads(urllib.request.urlopen(html).read().decode('utf-8'))
            logger.info('该请求为第%s页' % self.page)
            return response
        except Exception as e:
            logger.error(e)
            return None

    def get_sub_user_data(self, response) -> None:
        """ 从请求结果里提取每个用户（不做去重） """
        user_comments = response['data']['replies']
        logger.info('该请求的首个评论%s' % user_comments[0]['content']['message'])
        for user_comment in user_comments:

            # 单个用户数据对象定义
            sub_user_data: dict = {
                # 用户UID
                "uid": "",
                # 用户名称
                "name": "",
                # 用户等级
                "level": "",
                # 用户评论内容
                "content": ""
            }
            sub_user_data.update({
                "uid": user_comment['mid'],
                "name": user_comment['member']['uname'],
                "level": user_comment['member']['level_info']['current_level'],
                "content": user_comment['content']['message']
            })
            # 添加进列表
            self.comment_list.append(sub_user_data)
            # 评论记录数量+1
            self.comment_num += 1


def run():
    process = Process()
    process.run()
    Utils.save_json_file('comments', process.comment_list)

if __name__ == '__main__':
    try:
        logger.info("开始获取链接为https://t.bilibili.com/%s的动态" % Config.data['oid'])
        run()
    except KeyboardInterrupt:
        logger.info("退出")