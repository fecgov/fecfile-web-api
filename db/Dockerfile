FROM postgres:15

RUN apt-get update \
    && apt-get install -y pgxnclient postgresql-server-dev-15 build-essential \
    && pgxn install postgresql_anonymizer \
    && rm -rf /var/lib/apt/lists/*
COPY load_anon.sql /docker-entrypoint-initdb.d/001_load_anon.sql
COPY enable_anon.sql /docker-entrypoint-initdb.d/002_enable_anon.sql

ENV POSTGRES_USER=postgres
ENV POSTGRES_NAME=postgres
ENV POSTGRES_PASSWORD=postgres
ARG ENCRYPTION_PASSWORD

RUN echo 'Standard Dockerfile'

EXPOSE 5432
