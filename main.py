import enum
import urllib.request
import json
from pathlib import Path
import time
import sys
import random
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
        "times": 3,
        # 需要选取的人数
        "choice_numbers": 1
    }
    data = Utils.load_json(config_json_name)


class Process:
    """ 获取&处理动态评论数据类 """
    def __init__(self) -> None:
        # 评论分页
        self.page = 1
        # 评论总列表
        self.comment_list = []
        # 用户UID与名称对应字典
        self.uid_name_dict: dict[int, str] = {}
        # 用户UID与等级对应的字典
        self.uid_level_dict: dict[int, int] = {}
        # 去重后的评论用户列表
        self.comment_uids_set: set = {}
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
        # 记录所有参加人数
        self.process_comment_list()
        # 选取中奖人
        self.random_choose_user()

    def get_api(self) -> dict:
        """ 请求动态评论数据 """
        # 单次请求间隔0.5秒
        time.sleep(0.5)
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
            return response
        except Exception as e:
            logger.error(e)
            return None

    def get_sub_user_data(self, response) -> None:
        """ 从请求结果里提取每个用户（不做去重） """
        user_comments = response['data']['replies']
        for user_comment in user_comments:

            # 单个用户数据对象定义
            sub_user_data: dict = {
                # 用户UID
                "uid": 0,
                # 用户名称
                "name": "",
                # 用户等级
                "level": 0,
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
            # 更新 UID & Name 对应字典
            self.uid_name_dict.update({
                user_comment['mid']: user_comment['member']['uname']
            })
            # 更新 UID & Level 对应字典
            self.uid_level_dict.update({
                user_comment['mid']: user_comment['member']['level_info']['current_level']
            })
            # 评论记录数量+1
            self.comment_num += 1

    def process_comment_list(self):
        """ 将评论总列表去重，记录所有参加用户UID """
        comments_uid_list: list = []
        for sub_comment in self.comment_list:
            uid = sub_comment["uid"]
            comments_uid_list.append(uid)

        #### 处理参加用户名单：去重、去除UP主、过滤账号等级
        # 去重
        self.comment_uids_set = set(comments_uid_list)
        # 去除UP主
        self.comment_uids_set.discard(self.upper_uid)
        logger.info("本次参加评论的用户有%d人，不包含UP主" % len(self.comment_uids_set))
        # 过滤账号等级
        level_config = Config.data["level"]
        for sub_uid in list(self.comment_uids_set):
            # 如果当前账号等级低于过滤账号等级，则将其从集合中删除
            if self.uid_level_dict[sub_uid] < level_config:
                self.comment_uids_set.discard(sub_uid)
        logger.info("设定抽奖用户需满足账户等级大于等于%d级" % level_config)
        logger.info("符合抽奖等级的用户有%d人" % len(self.comment_uids_set))


    def random_choose_user(self):
        """ 抽取幸运用户 """
        users_list: list = list(self.comment_uids_set)
        choice_numbers = Config.data["choice_numbers"]
        if choice_numbers > len(users_list):
            logger.error("设置的抽奖人数%s大于实际参加人数%s，请修改配置文件中的choice_numbers" % (str(choice_numbers), str(len(users_list))))
        else:
            users_uid_result = random.sample(users_list, choice_numbers)

        # 获取具体信息
        logger.info("恭喜以下中奖用户：")
        for index, result in enumerate(users_uid_result):
            logger.info("第%d位中奖用户" % (index+1))
            logger.info("用户UID：%d" % result)
            logger.info("用户昵称：%s" % self.uid_name_dict[result])
            logger.info("-"*20)


def run():
    process = Process()
    process.run()
    Utils.save_json_file('comments.txt', process.comment_list)

if __name__ == '__main__':
    try:
        logger.info("开始获取链接为https://t.bilibili.com/%s的动态" % Config.data['oid'])
        run()
        logger.info("抽奖已结束")
    except KeyboardInterrupt:
        logger.info("退出")