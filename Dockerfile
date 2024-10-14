# Dockerfile
FROM python:3.10-slim-buster

#
WORKDIR /code

#
COPY ./requirements.txt /code/requirements.txt

#
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

ENV DB_USER=
ENV DB_PASSWORD=
ENV DB_HOST=
ENV DB_NAME=
ENV OPENAI_API_KEY=
ENV OBJECT_STORAGE_ACCESS_KEY=
ENV OBJECT_STORAGE_SECRET_KEY=
ENV MAIL_ACCOUNT=
ENV MAIL_APP_NUMBER=
ENV GOOGLE_CONFIDENTIAL_PATH=