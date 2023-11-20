# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import redis
import json
import pymysql
import math
import time
from flask import Flask, session, redirect, escape, request, render_template

# Time to live for cached data
TTL = 10

# Read the Redis credentials from the REDIS_URL environment variable.
REDIS_URL = os.environ.get('REDIS_URL')

# Configure the application name with the FLASK_APP environment variable.
app = Flask(__name__)

# Configure the secret_key with the SECRET_KEY environment variable.
app.secret_key = os.environ.get('SECRET_KEY', default=None)

# TODO 1 : Redis를 사용해보기
# Connect to Redis with the REDIS_URL environment variable.
store = redis.Redis.from_url(os.environ.get('REDIS_URL'))

@app.route('/')
def index():
    if 'username' in session:
        username = escape(session['username'])
        visits = store.hincrby(username, 'visits', 1)

        # TODO 2: TTL 설정을 확인해보기
        store.expire(username, TTL)

        return render_template('./index_login.html', username=username, visits=visits)
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
