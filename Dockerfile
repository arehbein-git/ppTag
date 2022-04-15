FROM python:3-slim

RUN apt-get update && \
	apt-get -y install nano git

RUN pip install plexapi
RUN pip install watchdog
RUN pip install xmltodict

RUN mkdir -p /app

RUN cd /app/ && git clone https://github.com/arehbein-git/ppTag.git pptag

WORKDIR /app/pptag

CMD [ "/bin/bash","-c","python -u pptag.py" ]
