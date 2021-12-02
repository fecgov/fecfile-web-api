FROM postgres:10

ENV POSTGRES_USER=postgres
ENV POSTGRES_NAME=postgres
ENV POSTGRES_PASSWORD=postgres
ARG ENCRYPTION_PASSWORD


# Load scripts to run at container initialization. They are run in alphabetical order.
COPY initdb.sql* /tmp/
RUN if [ -f "/tmp/initdb.sql.gpg" ]; then gpg --batch --output /docker-entrypoint-initdb.d/1.sql --passphrase $ENCRYPTION_PASSWORD --decrypt /tmp/initdb.sql.gpg; fi
RUN if [ -f "/tmp/initdb.sql" ]; then cp /tmp/initdb.sql /docker-entrypoint-initdb.d/1.sql; fi

COPY fecfile-frontend-dev.sql.gz* /tmp/
RUN if [ -f "/tmp/fecfile-frontend-dev.sql.gz.gpg" ]; then gpg --batch --output /docker-entrypoint-initdb.d/2.sql.gz --passphrase $ENCRYPTION_PASSWORD --decrypt /tmp/fecfile-frontend-dev.sql.gz.gpg; fi
RUN if [ -f "/tmp/fecfile-frontend-dev.sql.gz" ]; then cp /tmp/fecfile-frontend-dev.sql.gz /docker-entrypoint-initdb.d/2.sql.gz; fi

EXPOSE 5432
