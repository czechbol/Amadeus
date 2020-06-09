FROM python:3.8-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
RUN apt-get update
RUN apt-get -y --no-install-recommends install git tzdata graphviz \
&& apt-get clean \
&& rm -rf /var/lib/apt/lists/*
ENV TZ=Europe/Prague

VOLUME /Amadeus
WORKDIR /Amadeus

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt --user --no-warn-script-location
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
COPY . .