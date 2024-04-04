FROM python:3.10
ENV PYTHONUNBUFFERED=1

RUN mkdir /opt/nxg_fec
WORKDIR /opt/nxg_fec
ADD requirements.txt /opt
RUN pip3 install -r /opt/requirements.txt

RUN mv /etc/localtime /etc/localtime.backup && ln -s /usr/share/zoneinfo/EST5EDT /etc/localtime

RUN useradd nxgu --no-create-home --home /opt/nxg_fec && chown -R nxgu:nxgu /opt/nxg_fec
USER nxgu

EXPOSE 8080
ENTRYPOINT ["/bin/sh", "-c", "python wait_for_db.py && python manage.py migrate && python manage.py loaddata fixtures/e2e-test-data.json && python manage.py load_committee_data && python manage.py create_committee_views && gunicorn --bind 0.0.0.0:8080 fecfiler.wsgi -w 9 --reload"]