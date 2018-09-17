FROM python:3
ENV PYTHONUNBUFFERED 1
RUN mkdir /opt/nxg_fec
WORKDIR /opt/nxg_fec
ADD . /opt/nxg_fec/
RUN pip install -r requirements.txt
ADD . /opt/nxg_fec/
