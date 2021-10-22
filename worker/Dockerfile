# syntax=docker/dockerfile:1
FROM debian:11

RUN mkdir -p /data/conf
RUN mkdir -p /data/logs
RUN mkdir -p /data/jobs
RUN mkdir -p /data/srtm
COPY ./data/conf/ /data/conf/

RUN mkdir /app
WORKDIR /app

RUN apt-get update && apt-get -y upgrade
RUN apt-get -y install python3
RUN apt-get -y install python3-pip 

RUN pip install --upgrade pip
RUN pip install --upgrade wheel

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py LICENSE README.md ./

CMD [ "/usr/local/bin/rq", "worker", "-u", "redis://redis:6379" ]