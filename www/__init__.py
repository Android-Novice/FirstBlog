#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import time

from www.app import init
from www.config_default import init_mysql, blog_configs
from www.mysql_model import Blog, User
from www.mysql_orm import create_pool

content = """李同玄今年50岁了，在ofo担任运维，在上下班高峰期间搬运车辆，媒体给了他们这样一群人一个特别的称呼：“潮汐工”。下午5点钟，李同玄将停放在路边的多辆小黄车地在他骑来的电动车斗里，准备地铁站的方向驶去，他知道，这一天的晚高峰即将来临，而他正是要将这些便于人们回家的ofo小黄车搬到人流攒动的地铁站口。
央视首提“潮汐工”
央视11月16日播出的《经济半小时》栏目中首次提出“潮汐工”，特指ofo小黄车运维人员所用的词汇：
因为他们每天的上班时间是从下午5点到晚上11点半，由于别人下班，他们上班，他们的工作也被称为“潮汐工”。而他们的工作则便是如李同玄一样，根据总部的调度，在晚高峰下班时间把路边客流量不大的小黄车搬运到附近用车辆比较大的地铁站摆放整齐，以便辛苦了一天的“上班族”能够更便利地回家。
“看到他们高高兴兴地把车骑走，我就挺高兴，感觉没白付出辛苦。”李同玄说，现在的工作虽然辛苦，却让他觉得实现了个人价值。而每月5000元的稳定收入，比此前开“摩的”过着提心吊胆的日子舒心多了。
数据显示，这一工种随着共享单车的发展，成为了一个庞大的群体。"""

@asyncio.coroutine
def exec_main():
    global content
    # user = User()
    # user.email = 'yuwj119@wondershare.cn'
    # user.password = '123456'
    # user.name = 'jiushierji'
    # user.age = 90
    # user.note = 'but it is a secret: 二际今年至少有1000岁了...'
    # user.is_male = True
    # user.image = 'about:blank'
    # user.is_admin = False
    # yield from user.save()

    # print('*****************1*********************')
    # user = yield from User.find('201711162046017464')
    # print(str(user))
    # print('*****************2*********************')
    # user = yield from User.find('201711162046017464')
    # print(str(user))
    # print('*****************3*********************')
    # blog = yield from Blog.find('201711201417381426')
    # print(str(blog))
    # print('*****************4*********************')
    # user = yield from User.find('201711162046017464')
    # print(str(user))

    # blog = Blog()
    # blog.user_id = '201711162046017464'
    # blog.user_name = '二傻二际'
    # blog.title = '山东高速备战与广州之战 央视采访丁彦雨航竟然当众脱裤子'
    # blog.summary = '北京时间11月17日中午，山东高速在主场高速大球馆进行了晚上与广州证券队的赛前训练，全队11：30分开始进行训练，他们只是简单进行了一些体能恢复训练，一个小时后训练结束全队就离开了，由于山东成绩不错也受到了央视的关注，今天上午央视派记者来门来山东采访比赛。'
    # blog.content = content
    # yield from blog.save()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_mysql())
    loop.run_until_complete(create_pool(loop, **blog_configs['db']))
    # for i in range(0, 15):
    #     time.sleep(1)
    # loop.run_until_complete(exec_main())

    loop.run_until_complete(init(loop))
    loop.run_forever()

    # kw = {}
    # kw.setdefault('host', 'localhost'),
    # kw.setdefault('port', 3306),
    # kw['user'] = 'root'
    # kw['password'] = '123456'
    # kw['db'] = 'my_blog'
    # kw.setdefault('charset', 'utf8')
    # kw.setdefault('autocommit', True)
    # kw.setdefault('maxsize', 10)
    # kw.setdefault('minsize', 1)

    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(init_mysql())
    # loop.run_until_complete(create_pool(loop, **blog_configs.db))
    # loop.run_until_complete(exec_main())
    # loop.close()
