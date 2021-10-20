# syntax=docker/dockerfile:1
FROM debian:11

RUN mkdir /app
WORKDIR /app

RUN apt-get update && apt-get -y upgrade
RUN apt-get -y install python3
RUN apt-get -y install python3-pip 

RUN pip install --upgrade pip
RUN pip install --upgrade wheel

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./ ./

CMD [ "flask", "run", "--host=0.0.0.0" ]
#CMD [ "sleep", "86400" ]
