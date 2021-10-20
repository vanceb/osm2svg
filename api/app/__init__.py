from flask import Flask
from config import Config

from redis import Redis
from rq import Queue

app = Flask(__name__)
app.config.from_object(Config)

q = Queue(connection=Redis(host="redis", port="6379"))

from app import routes
