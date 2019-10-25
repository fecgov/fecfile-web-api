FROM python:3.6
ENV PYTHONUNBUFFERED 1

RUN mkdir /opt/nxg_fec
WORKDIR /opt/nxg_fec
ADD . /opt/nxg_fec/
RUN pip3 install -r requirements.txt

EXPOSE 8080
ENTRYPOINT ["sh", "-c", "python wait_for_db.py && gunicorn --bind 0.0.0.0:8080 fecfiler.wsgi -w 4 -t 120"]
