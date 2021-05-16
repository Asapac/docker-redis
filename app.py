import os
import socket

from flask import Flask
from redis import Redis


app = Flask(__name__)
redis = Redis(host="redis-server", db=0, socket_connect_timeout=2, socket_timeout=2)

@app.route('/')
def hello():
    redis.incr('hits')
    total_hits = redis.get('hits').decode()
    return f'Hello from Redis! I have been seen {total_hits} times.'


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
