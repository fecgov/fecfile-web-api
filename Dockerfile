FROM python:3.8
ENV PYTHONUNBUFFERED=1

RUN mkdir /opt/nxg_fec
WORKDIR /opt/nxg_fec
ADD requirements.txt /opt
RUN pip3 install -r /opt/requirements.txt

RUN mv /etc/localtime /etc/localtime.backup && ln -s /usr/share/zoneinfo/EST5EDT /etc/localtime

RUN useradd nxgu --no-create-home --home /opt/nxg_fec && chown -R nxgu:nxgu /opt/nxg_fec
USER nxgu

EXPOSE 8080
ENTRYPOINT ["/bin/sh", "-c", "python wait_for_db.py && gunicorn --bind 0.0.0.0:8080 fecfiler.wsgi -w 10 -t 200 --reload"]
