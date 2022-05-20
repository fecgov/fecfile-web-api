FROM postgres:12

ENV POSTGRES_USER=postgres
ENV POSTGRES_NAME=postgres
ENV POSTGRES_PASSWORD=postgres
ARG ENCRYPTION_PASSWORD

RUN echo 'Standard Dockerfile'
# Load scripts to run at container initialization. They are run in alphabetical order.
COPY fec_clean_dev_db_backup-20211227.sql /docker-entrypoint-initdb.d/
# COPY fecfile-roles-db.sql /docker-entrypoint-initdb.d/1.sql
# COPY fecfile-uat-test-accounts-db.sql /docker-entrypoint-initdb.d/2.sql

EXPOSE 5432
