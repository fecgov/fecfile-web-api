FROM python:3.6
ENV PYTHONUNBUFFERED 1

RUN mkdir /opt/func
WORKDIR /opt/func
ADD . /opt/func

RUN pip3 install psycopg2-binary requests
ENTRYPOINT ["/bin/bash", "-c", "python /opt/func/get_fec_number.py; python /opt/func/upload_report.py"]
