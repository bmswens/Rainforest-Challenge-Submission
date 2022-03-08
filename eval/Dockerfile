FROM python:3.9.10-buster

LABEL maintainer="bmswens@gmail.com"

WORKDIR /app

COPY ./requirements.txt ./
RUN pip install -r requirements.txt

COPY ./*.py ./
COPY  ./entrypoint.sh ./
RUN touch eval.log

ENTRYPOINT [ "bash", "entrypoint.sh" ]