FROM python:3.11-slim as build

ADD . ./app
WORKDIR /app

RUN pip install .

EXPOSE 8081

CMD [ "rec_task_api"]