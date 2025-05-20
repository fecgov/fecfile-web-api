FROM postgres:14

ENV POSTGRES_USER=postgres
ENV POSTGRES_NAME=postgres
ENV POSTGRES_PASSWORD=postgres
ARG ENCRYPTION_PASSWORD

RUN echo 'Standard Dockerfile'
COPY dev_dump_5_19.sql /docker-entrypoint-initdb.d/1.sql

EXPOSE 5432
