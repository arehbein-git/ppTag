FROM python:3

RUN apt-get update && \
	apt-get -y install nano git

RUN pip install plexapi
RUN pip install watchdog
RUN pip install xmltodict

RUN mkdir -p /app

ADD run.sh /app/
RUN chmod +x /app/run.sh

RUN cd /app/ && git clone https://github.com/arehbein-git/ppTag.git pptag

VOLUME /Photos

CMD [ "/app/run.sh" ]
