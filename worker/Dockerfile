# syntax=docker/dockerfile:1
From python:3.9-bullseye

WORKDIR /usr/src/app
COPY requirements.txt ./

RUN apt-get update && apt-get -y upgrade
RUN apt-get -y install apt-utils

RUN pip install --upgrade pip
RUN pip install --upgrade wheel

RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./

#CMD [ "python", "job.py", "data/test.json" ]
CMD [ "sleep", "86400" ]
