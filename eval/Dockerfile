FROM python:3.9.10-buster

LABEL maintainer="bmswens@gmail.com"

WORKDIR /app

RUN apt-get update
RUN apt-get install ffmpeg libsm6 libxext6 libgdal-dev  -y

COPY ./requirements.txt ./
RUN pip install --upgrade pip setuptools wheel numpy
RUN pip install -r requirements.txt

COPY ./*.py ./
COPY  ./entrypoint.sh ./
RUN touch eval.log

ENTRYPOINT [ "bash", "entrypoint.sh" ]