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

# Time to live for cached data
TTL = 10

# Read the Redis credentials from the REDIS_URL environment variable.
REDIS_URL = os.environ.get('REDIS_URL')

# Read the DB credentials from the DB_* environment variables.
DB_HOST = os.environ.get('DB_HOST')
DB_USER = os.environ.get('DB_USER')
DB_PASS = os.environ.get('DB_PASS')
DB_NAME = os.environ.get('DB_NAME')

# Initialize the database
Database = DB(host=DB_HOST, user=DB_USER, password=DB_PASS, db=DB_NAME)

# Configure the application name with the FLASK_APP environment variable.
app = Flask(__name__)

# Configure the secret_key with the SECRET_KEY environment variable.
app.secret_key = os.environ.get('SECRET_KEY', default=None)

# TODO 1 : Redis를 사용해보기
# Connect to Redis with the REDIS_URL environment variable.
store = redis.Redis.from_url(os.environ.get('REDIS_URL'))
Cache = redis.Redis.from_url(REDIS_URL)

@app.route('/')
def index():
    if 'username' in session:
        
        username = escape(session['username'])
        visits = store.hincrby(username, 'visits', 1)
        
        # TODO 2 : TTL 설정을 확인해보기
        store.expire(username, 10)

        return render_template('./index_login.html',username=username, visits=visits)
        # '''
        #     Logged in as {0}.<br>
        #     Visits: {1}
        # '''.format(username, visits)

    return render_template('./index_not_login.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['username'] = request.form['username']
        return redirect('/')

    return render_template('./index_post.html')
    # <form method="post">
    #     <p><input type=text name=username>
    #     <p><input type=submit value=Login>
    # </form>

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')

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