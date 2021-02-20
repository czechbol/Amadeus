FROM python:3.8.6-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get -y --no-install-recommends install \
    make=4.2.1-1.2 automake=1:1.16.1-4 gcc=4:8.3.0-1 g++=4:8.3.0-1 subversion=1.10.4-1+deb10u2

RUN apt-get -y --no-install-recommends install git=1:2.20.1-2+deb10u3 tzdata=2021a-0+deb10u1 graphviz=2.40.1-6

ENV TZ=Europe/Prague

VOLUME /Amadeus
WORKDIR /Amadeus

RUN /usr/local/bin/python -m pip install --upgrade pip
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt --user --no-warn-script-location

RUN apt-get -y remove make automake gcc g++ subversion \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
COPY . .
