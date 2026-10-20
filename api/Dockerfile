# syntax=docker/dockerfile:1
FROM debian:12

RUN apt-get update && apt-get -y upgrade && \
    apt-get install -y python3 python3-pip && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip wheel --break-system-packages

RUN mkdir -p /data
RUN mkdir -p /app
WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

COPY ./ ./

CMD [ "flask", "run", "--host=0.0.0.0" ]
