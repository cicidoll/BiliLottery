# B站动态抽奖

针对B站动态评论，可以进行手动抽奖
每次执行，会将获取到的所有评论数据保存在根目录下的comments.txt

  <h3 align="center">B站动态抽奖</h3>
  <p align="center">
    支持自定义 抽奖人数、抽奖用户等级限制
    <br />
    <a href="https://github.com/cicidoll/BiliChooseComments"><strong>项目链接 »</strong></a>
    <br />
    <br />
    <a href="https://github.com/cicidoll/BiliChooseComments">查看Demo</a>
    ·
    <a href="https://github.com/cicidoll/BiliChooseComments/issues">报告Bug</a>
    ·
    <a href="https://github.com/cicidoll/BiliChooseComments/issues">提出新特性</a>
  </p>

</p>

注释可见项目具体逻辑。
 
## 目录

- [上手指南](#上手指南)
  - [开发前的配置要求](#开发前的配置要求)
  - [安装步骤](#安装步骤)
- [文件目录说明](#文件目录说明)
- [版本控制](#版本控制)
- [作者](#作者)

### 上手指南



###### 开发前的配置要求

1. Python3.8+
2. 需要的包依赖：  
altgraph==0.17.2  
certifi==2022.5.18.1  
charset-normalizer==2.0.12  
colorama==0.4.4  
future==0.18.2  
idna==3.3  
loguru==0.6.0  
pefile==2022.5.30  
pyinstaller==5.1  
pyinstaller-hooks-contrib==2022.6  
pywin32-ctypes==0.2.0  
requests==2.27.1  
urllib3==1.26.9  
win32-setctime==1.1.0  
  
###### **安装步骤**

1. 安装上述所需包依赖
2. 配置根目录下config.json，参数介绍  
 "oid": -1,  # 动态的oid，可以从动态网站链接中截取  
 "level": 0,  # 等级最低限制   
 "choice_numbers": 1  # 需要选取的人数  

### 文件目录说明


```
filetree 

├── .gitignore
├── main.py
├── README.md
├── requirements.txt
└── config.json

```

### 版本控制

该项目使用Git进行版本管理。您可以在repository参看当前可用版本。

### 更新日志

2022-06-04  
版本号：1.1.0  
1. 添加了解析动态comment_id_str与comment_type，理论上支持任意动态的抽奖。  
2. 优化程序逻辑  
————————————————————  
2022-06-03  
版本号：1.0.0  
1. 初始版本  

### 作者

自律人偶
联系方式：ayaseemt@qq.com