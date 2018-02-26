#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging

import aiomysql

async def create_pool(loop, **kw):
    logging.info('create database connection pool...')
    global __pool
    __pool = await aiomysql.create_pool(
        host=kw.get('host', 'localhost'),
        port=kw.get('port', 3306),
        user=kw['user'],
        password=kw['password'],
        db=kw['db'],
        charset=kw.get('charset', 'utf-8'),
        autocommit=kw.get('autocommit', True),
        maxsize=kw.get('maxsize', 10),
        minsize=kw.get('minsize', 1),
        loop=loop
    )

async def select(sql, args, size=None):
    logging.info(sql + ' args: ' + str(args))
    print('<select> execute...' + sql + ' args: ' + str(args))
    global __pool
    async with __pool.get() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(sql.replace('?', '%s'), args or ())
            if size:
                rs = await cur.fetchmany(size)
            else:
                rs = await  cur.fetchall()
        # await cur.close()
        print('rs: \n' + str(rs))
        logging.info('rows returned: %s' % len(rs))
        return rs

async def excute(sql, args):
    logging.info(sql + ' args: ' + str(args))
    print(sql + ' args: ' + str(args))
    global __pool
    async with __pool.get() as conn:
        try:
            cursor = await conn.cursor()
            await cursor.execute(sql.replace('?', '%s'), args)
            rowcount = cursor.rowcount
        except BaseException as error:
            raise
        return rowcount

class Field(object):
    def __init__(self, name, column_type, primary_key, default):
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default

    def __str__(self):
        return '<%s, %s:%s>' % (self.__class__.__name__, self.column_type, self.name)

class StringField(Field):
    def __init__(self, name=None, primary_key=False, default=None, column_type='varchar(100)'):
        super(StringField, self).__init__(name, column_type, primary_key, default)

class IntegerField(Field):
    def __init__(self, name=None, primary_key=False, default=0, column_type='bigint'):
        super(IntegerField, self).__init__(name, column_type, primary_key, default)

class BooleanField(Field):
    def __init__(self, name=None, primary_key=False, default=False):
        super(BooleanField, self).__init__(name, 'boolean', primary_key, default)

class FloatField(Field):
    def __init__(self, name=None, primary_key=False, default=0.0):
        super(FloatField, self).__init__(name, 'real', primary_key, default)

class TextField(Field):
    def __init__(self, name=None):
        super(TextField, self).__init__(name, 'text', False, None)

class ModelMetaclass(type):
    def __new__(cls, name, bases, attrs):
        if name == 'Model':
            return type.__new__(cls, name, bases, attrs)
        tablename = attrs.get('__table__', None) or name
        logging.info('found model: %s (table: %s)' % (name, tablename))
        mappings = dict()
        fields = []
        primarykey = None
        for k, v in attrs.items():
            if isinstance(v, Field):
                logging.info('  foun mapping: %s ==> %s' % (k, v))
                mappings[k] = v
                if v.primary_key:
                    if primarykey:
                        raise RuntimeError('Dumplicate primary key for field: %s' % k)
                    primarykey = k
                else:
                    fields.append(k)
        if not primarykey:
            raise RuntimeError('primary key not found.')
        for k in mappings.keys():
            attrs.pop(k)
        attrs['__mappings__'] = mappings
        attrs['__table__'] = tablename
        attrs['__primary_key__'] = primarykey
        attrs['__fields__'] = fields
        attrs['__select__'] = 'select %s, %s from %s' % (primarykey, ', '.join(fields), tablename)
        attrs['__insert__'] = 'insert into %s (%s, %s) values (%s)' % (
            tablename, primarykey, ', '.join(fields), create_args_string(len(fields) + 1))
        attrs['__update__'] = 'update %s set %s where %s=?' % (
            tablename, ', '.join(f + '=?' for f in fields), primarykey)
        attrs['__delete__'] = 'delete from %s where %s=?' % (tablename, primarykey)
        return type.__new__(cls, name, bases, attrs)

def create_args_string(num):
    L = []
    for n in range(num):
        L.append('?')
    return ', '.join(L)

class Model(dict, metaclass=ModelMetaclass):
    def __init__(self, **kwargs):
        super(Model, self).__init__(**kwargs)

    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            raise AttributeError(r"'Model' object has no attribute '%s'" % item)

    def __setattr__(self, key, value):
        self[key] = value

    def get_value(self, key):
        return getattr(self, key, None)

    def get_value_or_default(self, key):
        value = getattr(self, key, None)
        if value is None:
            field = self.__mappings__[key]
            if field.default is not None:
                value = field.default() if callable(field.default) else field.default
                logging.debug('using default value for %s: %s' % (key, str(value)))
                setattr(self, key, value)
        return value

    @classmethod
    async def find_all(cls, where=None, args=None, **kwargs):
        'find objects by where clause'
        sql = [cls.__select__]
        if where:
            sql.append('where')
            sql.append(where)
        if args is None:
            args = []
        orderby = kwargs.get('orderBy', None)
        if orderby:
            sql.append('order by')
            sql.append(orderby)
        limit = kwargs.get('limit', None)
        if limit is not None:
            sql.append('limit')
            if isinstance(limit, int):
                sql.append('?')
                args.append(limit)
            elif isinstance(limit, tuple) and len(limit) == 2:
                sql.append('?, ?')
                args.extend(limit)
            else:
                raise ValueError('Invalid limit value: %s' % str(limit))

        rs = await select(' '.join(sql), args)
        return [cls(**r) for r in rs]

    @classmethod
    async def find_number(cls, select_field, where=None, args=None):
        ' find number by select and where '
        sql = ['select count(%s) as _num_ from %s ' % (select_field, cls.__table__)]
        if where:
            sql.append('where')
            sql.append(where)
        rs = await select(' '.join(sql), args, 1)
        if len(rs) == 0:
            return None
        return rs[0]['_num_']

    @classmethod
    async def find(cls, pk):
        ' find objects by primary key'
        print('<find> excute...')
        rs = await  select('%s where %s=?' % (cls.__select__, cls.__primary_key__), [pk], 1)
        print('result: \n' + str(rs))
        if len(rs) == 0:
            return None
        return cls(**rs[0])

    async def save(self):
        print('<save> excute...')
        args = [self.get_value_or_default(self.__primary_key__)]
        args.extend(list(map(self.get_value_or_default, self.__fields__)))
        rows = await excute(self.__insert__, args)
        if rows != 1:
            logging.warning('failed to insert record: affected rows: %s' % rows)

    async def update(self):
        print('<update> excute...')
        args = list(map(self.get_value, self.__fields__))
        args.append(self.get_value(self.__primary_key__))
        print(str(args))
        rows = await excute(self.__update__, args)
        if rows != 1:
            logging.warning('failed to update record by pk: affected rows: %s' % rows)

    async def remove(self):
        print('<remove> excute...')
        args = [self.get_value(self.__primary_key__)]
        rows = await excute(self.__delete__, args)
        if rows != 1:
            logging.warning('failed to delete record by pk: affected rows: %s' % rows)
