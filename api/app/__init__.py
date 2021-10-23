from flask import Flask
from config import Config

from redis import Redis
from rq import Queue

import logging
from logging.handlers import RotatingFileHandler
import os

app = Flask(__name__)
app.config.from_object(Config)

q = Queue(connection=Redis(host="redis", port="6379"))

from app import routes

# Logging
if not os.path.exists('/data/logs'):
    os.makedirs('/data/logs')
file_handler = RotatingFileHandler('/data/logs/map2laser.log',
                                    maxBytes=1024000,
                                    backupCount=10)
file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s'))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)