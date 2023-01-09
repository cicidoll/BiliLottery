import time, sys, random, json, urllib.request
from loguru import logger
from pathlib import Path
from typing import Dict
# 配置日志读写参数
logger.remove()
logger.add(sys.stdout,
           format="<green>{time:YYYY/MM/DD HH:mm:ss}</green> <red>|</red> <green>{level}</green> <red>|</red> {message}")
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
    data: dict = {"oid": 743863966229331992}
    load_data = Utils.load_json(config_json_name)
    # 更新配置文件
    data["oid"] = load_data["oid"]

class Process:
    """ 获取&处理动态转发数据类 """
    def __init__(self) -> None:
        # 转发总列表
        self.forward_list = []
        # 用户UID与名称对应字典
        self.uid_name_dict: dict[int, str] = {}
        # 用户UID与等级对应的字典
        self.uid_level_dict: dict[int, int] = {}
        # 去重后的转发用户列表
        self.forward_uids_set: set = {}
        # UP主的UID
        self.upper_uid: int = None
        # UP主的UID
        self.upper_name: str = None
        # 转发总数
        self.forward_num = 0
        # 经过B站官方过滤后的实际转发总数
        self.real_forward_num = 0
        # Headers配置
        self.headers: Dict[str, str] = {
            'User-Agent':
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36',
            "origin": "https://t.bilibili.com",
            "referer": "https://t.bilibili.com/%d" % Config.data['oid']
        }

    def run(self):
        """ 主线程  """
        # 获取动态基本信息:确定UP主昵称及uid
        self.get_basic()
        logger.info("UP主Uid：%s" % self.upper_uid)
        logger.info("UP主昵称：%s" % self.upper_name)
        logger.info("动态显示转发次数：%s" % self.forward_num)
        # 批量处理转发内容
        self.process_forward()
        # 开始抽奖
        self.random_choose_user()

    def get_basic(self) -> None:
        """ 获取动态基本信息 """
        # 开始请求
        url: str = 'https://api.bilibili.com/x/polymer/web-dynamic/v1/detail?id=%d' % Config.data['oid']

        try:
            html: urllib.request.Request = urllib.request.Request(url = url, headers = self.headers)
            response: dict = json.loads(urllib.request.urlopen(html).read().decode('utf-8'))
            if response["code"] != 0:
                logger.error("请求出错，错误信息如下:%s" % (response["message"] ))
            else:
                self.upper_uid = response["data"]["item"]["modules"]["module_author"]["mid"]
                self.upper_name = response["data"]["item"]["modules"]["module_author"]["name"]
                self.forward_num = response["data"]["item"]["modules"]["module_stat"]["forward"]["count"]
        except Exception as e:
            logger.error(e)

    def process_forward(self) -> None:
        """ 批量获取动态转发 """
        offset: int = 0
        while self.real_forward_num < self.forward_num:
            response: dict = self._get_sub_forward(offset)
            if len(response["data"]["items"]) == 0: break
            self.real_forward_num += len(response["data"]["items"])
            offset = self._get_sub_user_data(response)
        # 对抽奖用户列表进行去重
        self._process_forward_list()

    def _get_sub_forward(self, offset: int) -> dict:
        """ 获取动态转发 """
        offset = "using_normal_repost" if offset == 0 else offset
        # 开始请求
        url: str = 'https://api.bilibili.com/x/polymer/web-dynamic/v1/detail/forward?id=%d&offset=%s' % (Config.data['oid'], str(offset))
        try:
            html: urllib.request.Request = urllib.request.Request(url = url, headers = self.headers)
            response: dict = json.loads(urllib.request.urlopen(html).read().decode('utf-8'))
            if response["code"] != 0:
                logger.error("请求出错，错误信息如下:%s" % (response["message"] ))
                return {}
            else: return response
        except Exception as e:
            logger.error(e)
            return {}

    def _get_sub_user_data(self, response: dict) -> int:
        """ 从请求结果里提取每个用户（不做去重） """
        user_forwards = response['data']['items']
        for user_forward in user_forwards:
            # 单个用户数据对象定义
            sub_user_data: dict = {
                # 用户UID
                "uid": 0,
                # 用户名称
                "name": "",
                # 用户转发内容
                "text": "",
                # 转发内容的专属id(用于定位轮询)
                "id_str": ""
            }
            sub_user_data.update({
                "uid": user_forward['user']['mid'],
                "name": user_forward['user']['name'],
                "text": user_forward['desc']['text'],
                "id_str": user_forward['id_str']
            })
            # 添加进列表
            self.forward_list.append(sub_user_data)
            # 更新 UID & Name 对应字典
            self.uid_name_dict.update({
                sub_user_data['uid']: sub_user_data['name']
            })
        # 返回定位ID，用于下一轮轮询
        return self.forward_list[-1]["id_str"]

    def _process_forward_list(self):
        """ 将转发总列表去重，记录所有参加用户UID """
        forward_uid_list: list = []
        for sub_forward in self.forward_list:
            uid = sub_forward["uid"]
            forward_uid_list.append(uid)
        #### 处理参加用户名单：去重、去除UP主
        # 去重
        self.forward_uids_set = set(forward_uid_list)
        # 去除UP主
        self.forward_uids_set.discard(self.upper_uid)
        logger.info("本次参加转发的实际用户有%d人(经过B站官方过滤后)" % (self.real_forward_num))
        logger.info("经过查重后的用户有%d人(不包含UP主)" % len(self.forward_uids_set))

    def random_choose_user(self) -> None:
        """ 抽取幸运用户 """
        users_uid_result = random.sample(list(self.forward_uids_set), 1)[0]
        # 获取具体信息
        logger.info("恭喜以下中奖用户：")
        logger.info("用户UID：%d" % users_uid_result)
        logger.info("用户昵称：%s" % self.uid_name_dict[users_uid_result])
        logger.info("-"*20)

def run():
    process = Process()
    process.run()
    Utils.save_json_file('comments.txt', process.forward_list)

def main():
    try:
        logger.info("开始获取链接为https://t.bilibili.com/%s的动态" % Config.data['oid'])
        run()
        logger.info("抽奖已结束,请按任意键关闭窗口。")
        input()
    except KeyboardInterrupt:
        logger.info("退出")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("退出")
