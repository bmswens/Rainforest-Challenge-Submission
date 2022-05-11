FROM python:3.6.8

LABEL maintainer="bmswens@gmail.com"

WORKDIR /app

RUN apt-get update
RUN apt-get install ffmpeg libsm6 libxext6  -y

COPY ./requirements.txt ./
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt

COPY ./*.py ./
COPY  ./entrypoint.sh ./
RUN touch eval.log

ENTRYPOINT [ "bash", "entrypoint.sh" ]