FROM python:3.12
ENV PYTHONUNBUFFERED=1

RUN mkdir /opt/nxg_fec
WORKDIR /opt/nxg_fec
ADD requirements.txt /opt
ADD requirements-test.txt /opt
RUN pip install -r /opt/requirements.txt && pip install -r /opt/requirements-test.txt

RUN mv /etc/localtime /etc/localtime.backup && ln -s /usr/share/zoneinfo/EST5EDT /etc/localtime

ADD entrypoint.sh /opt
RUN chmod +x /opt/entrypoint.sh

RUN useradd nxgu --no-create-home --home /opt/nxg_fec && chown -R nxgu:nxgu /opt/nxg_fec
USER nxgu

EXPOSE 8080
ENTRYPOINT ["/opt/entrypoint.sh"]
