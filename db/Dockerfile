FROM postgres:10

ENV POSTGRES_USER=postgres
ENV POSTGRES_NAME=postgres
ENV POSTGRES_PASSWORD=postgres
ARG ENCRYPTION_PASSWORD


# Load scripts to run at container initialization. They are run in alphabetical order.
COPY initdb.sql.gpg /tmp/initdb.sql.gpg
RUN gpg --batch --output /docker-entrypoint-initdb.d/1.sql --passphrase $ENCRYPTION_PASSWORD --decrypt /tmp/initdb.sql.gpg

COPY fecfile-frontend-dev.sql.gz.gpg /tmp/fecfile-frontend-dev.sql.gz.gpg
RUN gpg --batch --output /docker-entrypoint-initdb.d/2.sql.gz --passphrase $ENCRYPTION_PASSWORD --decrypt /tmp/fecfile-frontend-dev.sql.gz.gpg 

EXPOSE 5432
