FROM python:3.5
ENV PYTHONUNBUFFERED 1

RUN mkdir /opt/nxg_fec
WORKDIR /opt/nxg_fec
ADD . /opt/nxg_fec/
RUN pip3 install -r requirements.txt

EXPOSE 8080
CMD gunicorn --bind 0.0.0.0:8080 fecfiler.wsgi
