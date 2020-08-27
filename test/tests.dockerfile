# FROM alpine:edge
FROM python:2

RUN apt install make

RUN pip install --upgrade pip
