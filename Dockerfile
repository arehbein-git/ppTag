FROM python:3

RUN apt-get update && \
	apt-get -y install nano git

RUN pip install plexapi
RUN pip install watchdog
RUN pip install xmltodict

RUN mkdir -p /app

ADD run.sh /app/
RUN chmod +x /app/run.sh

VOLUME /Photos
VOLUME /app/pptag

CMD [ "/app/run.sh" ]
