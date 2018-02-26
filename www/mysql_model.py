#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
import uuid
from datetime import datetime
import math

from www.mysql_orm import Model, StringField, IntegerField, FloatField, BooleanField, TextField

def next_id():
    first = datetime.now().strftime('%Y%m%d%H%M%S')
    second = int(math.modf(time.time())[0] * 10000)
    return '%s%s' % (first, second)

class User(Model):
    __table__ = 'users'

    id = StringField(primary_key=True, default=next_id, column_type='varchar(50)')
    email = StringField(column_type='varchar(50)')
    password = StringField(column_type='varchar(50)')
    is_admin = BooleanField()
    name = StringField(column_type='varchar(50)')
    image = StringField(column_type='varchar(500)')
    created_at = FloatField(default=time.time)
    age = IntegerField(column_type='tinyint')
    is_male = BooleanField()
    note = TextField()

# 'CREATE TABLE IF NOT EXISTS users(id varchar(50) not null primary key, email VARCHAR(50) NOT NULL, password VARCHAR(50) NOT NULL' \
# 'is_admin TINYINT, name VARCHAR(50) NOT NULL, image VARCHAR(500), created_at REAL, age TINYINT, is_male bool, note TEXT)'

class Blog(Model):
    __table__ = 'blogs'

    id = StringField(primary_key=True, default=next_id, column_type='varchar(50)')
    user_id = StringField(column_type='varchar(50)')
    user_name = StringField(column_type='varchar(50)')
    title = StringField(column_type='varchar(50)')
    summary = StringField(column_type='varchar(50)')
    content = TextField()
    created_at = FloatField(default=time.time)

# 'CREATE TABLE IF NOT EXISTS blogs(id varchar(50) not null primary key, user_id VARCHAR(50) NOT NULL, user_name VARCHAR(50) NOT NULL' \
# 'title VARCHAR(50) NOT NULL, summary VARCHAR(500), content TEXT NOT NULL, created_at REAL)'

class Comment(Model):
    __table__ = 'comments'

    id = StringField(primary_key=True, default=next_id, column_type='varchar(50)')
    blog_id = StringField(column_type='varchar(50)')
    user_id = StringField(column_type='varchar(50)')
    user_name = StringField(column_type='varchar(50)')
    content = TextField()
    created_at = FloatField(default=time.time)

# 'CREATE TABLE IF NOT EXISTS comments(id varchar(50) not null primary key, user_id VARCHAR(50) NOT NULL, ' \
# 'user_name VARCHAR(50) NOT NULL, blog_id VARCHAR(50) NOT NULL, content TEXT NOT NULL, created_at REAL)'
