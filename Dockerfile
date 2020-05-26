FROM python:3.8-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
RUN apt-get update && apt-get -qq install git tzdata
RUN apt-get -qq install graphviz
RUN apt-get clean && apt-get autoremove -y
ENV TZ=Europe/Prague

VOLUME /Amadeus
WORKDIR /Amadeus

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt --user --no-warn-script-location
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
COPY . .