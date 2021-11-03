FROM postgres:10

ENV POSTGRES_USER: postgres
ENV POSTGRES_NAME: postgres
ENV POSTGRES_PASSWORD: postgres

# Load scripts to run at container initialization. They are run in alphabetical order.
COPY initdb.sql /docker-entrypoint-initdb.d/1.sql
COPY fecfile-frontend-dev.sql.gz /docker-entrypoint-initdb.d/2.sql.gz

EXPOSE 5432
