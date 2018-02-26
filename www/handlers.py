#!python3
# -*- encoding: utf-8 -*-
import asyncio
import logging

import aiohttp
import time
import json
import re
import hashlib

import math
from aiohttp import web
from www import markdown2
from www.config_default import blog_configs
from www.apierrors import APIValueError, APIError, APIPermissionError
from www.mysql_model import User, Blog, next_id, Comment
from www.coreweb import get, post

COOKIE_NAME = 'awesession'
_COOKIE_KEY = blog_configs['session']['secret']

@get('/api/users')
async def api_get_users():
    users = await User.find_all()
    return dict(users=users)

@get('/register')
async def register():
    return {'__template__': 'register.html'}

@get('/signin')
async def signin():
    return {'__template__': 'signin.html'}

_RE_EMAIL = re.compile(r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
_RE_SHA1 = re.compile(r'^[0-9a-f]{40}$')

@post('/api/signin')
async def authenticate(*, email, password):
    if not email:
        raise APIValueError('email', 'Invalid email.')
    if not password:
        raise APIValueError('password', 'Invalid password.')
    users = await User.find_all('email=?', [email])
    if len(users) == 0:
        raise APIValueError('email', 'Email not exist')
    user = users[0]
    sha1 = hashlib.sha1()
    sha1.update(user.id.encode('utf-8'))
    sha1.update(b':')
    sha1.update(password.encode('utf-8'))
    if user.password != sha1.hexdigest():
        raise APIValueError('password', 'Invalid password')
    r = web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
    user.password = '*********'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r

@get('/signout')
async def signout(request):
    referer = request.headers.get('Referer')
    r = web.HTTPFound(referer or '/')
    r.set_cookie(COOKIE_NAME, '-deleted-', max_age=0, httponly=True)
    logging.info('user signed out')
    return r

@post('/api/users')
async def api_register_user(*, email, name, password):
    if not name or not name.strip():
        raise APIValueError('name')
    if not email or not _RE_EMAIL.match(email):
        raise APIValueError('email')
    if not password or not _RE_SHA1.match(password):
        raise APIValueError('password')
    same_email_count = await User.find_number('email', 'email=?', [email])
    if same_email_count > 0:
        raise APIError('register:failed', 'email', 'email is already in use')
    uid = next_id()
    sha1_passwd = '%s:%s' % (uid, password)
    user = User(name=name.strip(), email=email, password=hashlib.sha1(sha1_passwd.encode('utf-8')).hexdigest(),
                is_admin=False, is_male=False,
                note='from web register', image='about:blank', age=19)
    await user.save()

    r = web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
    user.password = '********'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r

def user2cookie(user, max_age):
    expires = str(int(time.time() + max_age))
    s = '%s-%s-%s-%s' % (user.id, user.password, expires, _COOKIE_KEY)
    L = [user.id, expires, hashlib.sha1(s.encode('utf-8')).hexdigest()]
    return '-'.join(L)

async def cookie2user(cookie_str):
    print('<cookie2user> excute...')
    if not cookie_str:
        return None
    try:
        L = cookie_str.split('-')
        if len(L) != 3:
            return None
        uid, expires, sha1 = L
        if int(expires) < time.time():
            return None
        user = await User.find(uid)
        if user is None:
            return None
        s = '%s-%s-%s-%s' % (uid, user.password, expires, _COOKIE_KEY)
        if sha1 != hashlib.sha1(s.encode('utf-8')).hexdigest():
            logging.info('invalid sha1')
            return None
        user.password = '******'
        return user
    except Exception as e:
        logging.exception(e)
        return None

@get('/')
async def index(request, *, page='1'):
    showing_page_index = get_showing_page_index(page)
    total_blog_count = await Blog.find_number('id')
    blogs = []
    p = Page(total_blog_count, showing_page_index, 15)
    if total_blog_count:
        blogs = await Blog.find_all(orderBy='created_at desc', limit=(p.start, p.showing_count))
    return {'__template__': 'blogs.html',
            'blogs': blogs,
            '__user__': request.__user__,
            'page': p}

@get('/users')
async def show_all_users(request):
    users = await User.find_all()
    return {
        '__template__': 'index.html',
        'page_title': 'the list of users',
        'users': users
    }

def check_admin(request):
    if request.__user__ is None or not request.__user__.is_admin:
        raise APIPermissionError()

def text2html(text):
    lines = map(lambda s: '<p>%s</p>' % s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'),
                filter(lambda s: s.strip() != '', text.split('\n')))
    return ''.join(lines)

@get('/api/blogs/{id}')
async def api_get_blog(*, id):
    print('<api_get_blog> execute...')
    blog = await Blog.find(id)
    return blog

@get('/manage/blogs/edit')
async def edit_blog(*, id):
    print('<edit_blog> execute...')
    return {
        '__template__': 'writeblog.html',
        'id': id,
        'action': '/api/blog/update/%s' % id
    }

@post('/api/blog/update/{id}')
async def update_blog(id, request, *, title, summary, content):
    print('<update_blog> excute...')
    check_admin(request)
    blog = await Blog.find(id)
    if blog is None:
        raise APIValueError('id', 'couldn\'t find blog')
    if not title or not title.strip():
        raise APIValueError('name', 'name cannot be empty.')
    if not summary or not summary.strip():
        raise APIValueError('summary', 'summary cannot be empty.')
    if not content or not content.strip():
        raise APIValueError('content', 'content cannot be empty.')
    blog.title = title
    blog.summary = summary
    blog.content = content
    await blog.update()
    return blog

@post('/api/blogs/{id}/delete')
async def delete_blog(id, request):
    print('<delete_blog> excute...')
    check_admin(request)
    blog = await Blog.find(id)
    if blog is None:
        raise APIValueError('id', 'couldn\'t find blog')
    await blog.remove()
    return blog

@get('/blog/{id}')
async def get_blog(*, id):
    print('<get_blog> excute...')
    blog = await Blog.find(id)
    if blog is None:
        raise APIValueError('id', 'couldn\'t find blog')
    comments = await Comment.find_all('blog_id=?', [id], orderBy='created_at desc')
    for c in comments:
        c.html_content = text2html(c.content)
    blog.html_content = markdown2.markdown(blog.content)
    return {
        '__template__': 'blog.html',
        'blog': blog,
        'comments': comments
    }

@post('/api/blogs')
async def api_create_blog(request, *, title, summary, content):
    print('<api_create_blog> excute...')
    check_admin(request)
    if not title or not title.strip():
        raise APIValueError('title', 'title connot be empty.')
    if not summary or not summary.strip():
        raise APIValueError('summary', 'summary connot be empty.')
    if not content or not content.strip():
        raise APIValueError('content', 'content connot be empty.')
    blog = Blog(user_id=request.__user__.id, user_name=request.__user__.name, title=title, summary=summary,
                content=content)
    await blog.save()
    return blog

@get('/manage/blogs')
async def manage_blogs(*, showing_page_index='1'):
    page_index = get_showing_page_index(showing_page_index)
    blog_total_count = await Blog.find_number('id')
    page = Page(blog_total_count, page_index)
    return {
        '__template__': 'manageblogs.html',
        'showing_page_index': page_index,
        'page': page
    }

@get('/manage/blogs/create')
def write_blog():
    return {
        '__template__': 'writeblog.html',
        'id': '',
        'action': '/api/blogs'
    }

@get('/api/blogs')
async def api_blogs(*, showing_page_index='1'):
    print('show blogs list.....')
    showing_page_index = get_showing_page_index(showing_page_index)
    total_blog_count = await Blog.find_number('id')
    p = Page(total_blog_count, showing_page_index)
    if total_blog_count == 0:
        return dict(page=p, blogs=())
    blogs = await Blog.find_all(orderBy='created_at desc', limit=(p.start, p.showing_count))
    print(len(blogs))
    return dict(page=p, blogs=blogs)

@get('/manage/comments')
async def manage_comments(*, showing_page_index='1'):
    page_index = get_showing_page_index(showing_page_index)
    comment_total_count = await Comment.find_number('id')
    page = Page(comment_total_count, page_index)
    return {
        '__template__': 'managecomments.html',
        'showing_page_index': page_index,
        'page': page
    }

@get('/api/comments')
async def api_comments(*, showing_page_index='1'):
    print('show comments list.....')
    showing_page_index = get_showing_page_index(showing_page_index)
    comment_total_count = await Comment.find_number('id')
    p = Page(comment_total_count, showing_page_index)
    if comment_total_count == 0:
        return dict(page=p, comments=())
    comments = await Comment.find_all(orderBy='created_at desc', limit=(p.start, p.showing_count))
    print(len(comments))
    return dict(page=p, comments=comments)

@get('/manage/users')
async def manage_users(*, showing_page_index='1'):
    page_index = get_showing_page_index(showing_page_index)
    user_total_count = await User.find_number('id')
    page = Page(user_total_count, page_index)
    return {
        '__template__': 'manageusers.html',
        'showing_page_index': page_index,
        'page': page
    }

@get('/api/users')
async def api_users(*, showing_page_index='1'):
    print('show users list.....')
    showing_page_index = get_showing_page_index(showing_page_index)
    comment_total_count = await User.find_number('id')
    p = Page(comment_total_count, showing_page_index)
    if comment_total_count == 0:
        return dict(page=p, users=())
    users = await Comment.find_all(orderBy='created_at desc', limit=(p.start, p.showing_count))
    print(len(users))
    return dict(page=p, users=users)

@post('/api/users/{id}/delete')
async def delete_user(id, request):
    print('<delete_blog> excute...')
    check_admin(request)
    user = await User.find(id)
    if user is None:
        raise APIValueError('id', 'couldn\'t find user')
    await user.remove()
    return user

@post('/api/comments/{id}/delete')
async def delete_comment(id, request):
    print('<delete_comment> excute...')
    check_admin(request)
    comment = await Comment.find(id)
    if comment is None:
        raise APIValueError('id', 'couldn\'t find comment')
    await comment.remove()
    return comment

@post('/api/blogs/{blog_id}/comments')
async def api_create_comment(blog_id, request, *, content):
    print('<api_create_comment> excute...')
    user = request.__user__
    if user is None:
        raise APIPermissionError()
    comment = Comment()
    comment.user_id = user.id
    comment.user_name = user.name
    comment.blog_id = blog_id
    comment.content = content
    await comment.save()
    return comment

def get_showing_page_index(index_str):
    p = 1;
    try:
        p = int(index_str)
    except:
        p = 1
    if p < 1:
        p = 1
    return p

class Page(object):
    def __init__(self, total_blog_count, showing_page_index=1, per_page_count=6):
        self.total_blog_count = total_blog_count
        self.per_page_count = per_page_count
        self.total_page_count = math.ceil(total_blog_count / per_page_count)
        if (total_blog_count == 0) or (showing_page_index > self.total_page_count):
            self.start = 0
            self.showing_count = 0
            self.showing_page_index = 1
        else:
            self.showing_page_index = showing_page_index
            self.start = self.per_page_count * (self.showing_page_index - 1)
            self.showing_count = self.per_page_count
        self.has_next = self.showing_page_index < self.total_page_count
        self.has_previous = self.showing_page_index > 1

    def __str__(self):
        return 'total_blog_count: %s, total_page_count: %s, showing_page_index: %s, per_page_count: %s, start: %s, showing_count: %s' % (
            self.total_blog_count, self.total_page_count, self.showing_page_index, self.per_page_count, self.start,
            self.showing_count)

    __repr__ = __str__

# @get('/')
# @asyncio.coroutine
# def index(request):
#     return aiohttp.web.Response(body=b'<h1><u><b>Hello world!</b></u></h1><div><img src=\'static/img/drink.gif\'/></div>',
#                                 content_type='text/html')

@get('/home')
async def home(page=1, request=None, *numbers, named_kw1, named_kw2, **kwargs):
    return aiohttp.web.Response(
        body=b'<h1><u><b>Hello world!</b></u></h1><div><img src=\'static/img/drink.gif\'/></div>',
        content_type='text/html')

# @post('/index')
# async def post_index(page=1, request=None, *numbers, named_kw1, named_kw2, **kwargs):
#     return aiohttp.web.Response(
#         body=b'<h1><u><b>Hello world!</b></u></h1><div><img src=\'static/img/drink.gif\'/></div>',
#         content_type='text/html')
