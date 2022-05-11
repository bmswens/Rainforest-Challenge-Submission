FROM python:3.9.10-buster

EXPOSE 5000
LABEL maintainer="bmswens@gmail.com"

RUN pip install --upgrade pip

WORKDIR /app
COPY ./requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

COPY ./*.py ./
COPY ./templates ./templates

ENTRYPOINT [ "flask", "run", "--host=0.0.0.0"]