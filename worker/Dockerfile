# syntax=docker/dockerfile:1
FROM debian:12

RUN apt-get update && apt-get -y upgrade

# Python 3 and osmium tools
RUN apt-get install -y python3 python3-pip osmium-tool && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip wheel --break-system-packages

COPY requirements.txt ./
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

COPY *.py LICENSE README.md ./

RUN mkdir -p /data/conf
RUN mkdir -p /data/logs
RUN mkdir -p /data/jobs
RUN mkdir -p /data/srtm
RUN mkdir -p /data/extracts
RUN mkdir -p /data/filtered
COPY ./data/conf/ /data/conf/

CMD [ "/usr/local/bin/rq", "worker", "-u", "redis://redis:6379" ]