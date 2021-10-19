FROM python:3.9.6-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get -y --no-install-recommends install \
    make=4.3-4.1 automake=1:1.16.3-2 gcc=4:10.2.1-1 g++=4:10.2.1-1 \
    subversion=1.14.1-3 libmpc-dev=1.2.0-1 libgmp3-dev=2:6.2.1+dfsg-1

RUN apt-get -y --no-install-recommends install git tzdata graphviz

ENV TZ=Europe/Prague

VOLUME /Amadeus
WORKDIR /Amadeus

RUN python3 -m pip install --upgrade pip
COPY requirements.txt requirements.txt
RUN python3 -m pip install -r requirements.txt --user --no-warn-script-location

RUN apt-get -y remove make automake gcc g++ subversion libmpc-dev libgmp3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
COPY . .
