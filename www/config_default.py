#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pymysql

blog_configs = {
    'debug': True,
    'db': {'host': 'localhost',
           'port': 3306,
           'user': 'root',
           'password': '123456',
           'db': 'my_blog',
           'charset': 'utf8'},
    'session': {'secret': 'AwEsOmE'}
}

async def init_mysql():
    try:
        # conn = aiomysql.connect(user='root',password='123456',db='my_blog')
        conn = pymysql.connect(user='root', password='123456')
        cur = conn.cursor()
        create_db = 'create database if not EXISTS my_blog'
        # drop_table = 'drop table if EXISTS my_blog.users '
        create_users_table = 'CREATE TABLE IF NOT EXISTS my_blog.users(id varchar(50) not null primary key, email VARCHAR(50) NOT NULL, password VARCHAR(50) NOT NULL,' \
                             'is_admin TINYINT, name VARCHAR(50) NOT NULL, image VARCHAR(500), created_at REAL, age TINYINT, is_male bool, note TEXT)'
        create_blogs_table = 'CREATE TABLE IF NOT EXISTS my_blog.blogs(id varchar(50) not null primary key, user_id VARCHAR(50) NOT NULL, user_name VARCHAR(50) NOT NULL,' \
                             'title VARCHAR(50) NOT NULL, summary VARCHAR(500), content TEXT NOT NULL, created_at REAL)'
        create_comments_table = 'CREATE TABLE IF NOT EXISTS my_blog.comments(id varchar(50) not null primary key, user_id VARCHAR(50) NOT NULL, ' \
                                'user_name VARCHAR(50) NOT NULL, blog_id VARCHAR(50) NOT NULL, content TEXT NOT NULL, created_at REAL)'
        cur.execute(create_db)
        # cur.execute(drop_table)
        cur.execute(create_users_table)
        cur.execute(create_blogs_table)
        cur.execute(create_comments_table)
        cur.close()
        conn.close()
    except Exception as e:
        raise
