FROM python:3.13-slim

LABEL MAINTAINER="Jonnattan Griffiths"
LABEL VERSION=1.0
LABEL DESCRIPCION="Python Server Scrapper"

ENV TZ 'UTC'
ENV HOST_BD ''
ENV USER_BD ''
ENV PASS_BD ''
ENV HUB_SELENIUM_URL ''
ENV SERVER_API_KEY ''
ENV AES_KEY ''

ENV FLASK_APP app
ENV FLASK_DEBUG production

RUN addgroup --gid 10101 jonnattan && \
    adduser --home /home/jonnattan --uid 10100 --gid 10101 --disabled-password jonnattan


COPY ./requirements.txt /home/jonnattan/requirements.txt

USER jonnattan

RUN cd /home/jonnattan && \
    mkdir -p /home/jonnattan/.local/bin && \
    export PATH=$PATH:/home/jonnattan/.local/bin && \
    pip install --upgrade pip && \
    pip install -r requirements.txt

WORKDIR /home/jonnattan/app

EXPOSE 8090

CMD [ "python", "http-server.py", "8090"]

