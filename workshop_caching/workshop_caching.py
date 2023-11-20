# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import redis
import json
import pymysql
import math
import time
from flask import Flask, session, redirect, escape, request, render_template

class DB:
    def __init__(self, **params):
        params.setdefault("charset", "utf8mb4")
        params.setdefault("cursorclass", pymysql.cursors.DictCursor)

        self.mysql = pymysql.connect(**params)

    def query(self, sql):
        with self.mysql.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()

    def record(self, sql, values):
        with self.mysql.cursor() as cursor:
            cursor.execute(sql, values)
            return cursor.fetchone()

# Read the Redis credentials from the REDIS_URL environment variable.
REDIS_URL = os.environ.get('REDIS_URL')

# Read the DB credentials from the DB_* environment variables.
DB_HOST = os.environ.get('DB_HOST')
DB_USER = os.environ.get('DB_USER')
DB_PASS = os.environ.get('DB_PASS')
DB_NAME = os.environ.get('DB_NAME')

# Initialize the database
Database = DB(host=DB_HOST, user=DB_USER, password=DB_PASS, db=DB_NAME)

# Time to live for cached data
TTL = 10

# Configure the application name with the FLASK_APP environment variable.
app = Flask(__name__)

# TODO 1 : Redis를 사용해보기
Cache = redis.Redis.from_url(REDIS_URL)

@app.route('/')
def index():
    return redirect('/db')

@app.route('/db')
def db():
    
    start = time.time()
    print(fetch("SELECT * FROM planet"))
    print(planet(1))
    print(planet(2))
    print(planet(3))
    end = time.time()
    result = f"전체 소요시간 : {end - start:.5f} sec"
    print(result)
    
    return render_template('./index_db.html', result=result, ttl=TTL)

def fetch(sql):
    """Retrieve records from the cache, or else from the database."""
    res = Cache.get(sql)

    if res:
        return json.loads(res)

    res = Database.query(sql)
    Cache.setex(sql, TTL, json.dumps(res))
    return res


def planet(id):
    """Retrieve a record from the cache, or else from the database."""
    key = f"planet:{id}"
    res = Cache.hgetall(key)

    if res:
        return res

    sql = "SELECT `id`, `name` FROM `planet` WHERE `id`=%s"
    res = Database.record(sql, (id,))

    if res:
        Cache.hmset(key, res)
        Cache.expire(key, TTL)

    return res