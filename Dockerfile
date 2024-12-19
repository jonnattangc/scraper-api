FROM python:3.14.0a2-alpine3.21

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
ENV FLASK_DEBUG development

RUN adduser -h /home/jonnattan -u 10100 -g 10101 --disabled-password jonnattan

COPY ./requirements.txt /home/jonnattan/requirements.txt

RUN cd /home/jonnattan && \
    mkdir -p /home/jonnattan/.local/bin && \
    export PATH=$PATH:/home/jonnattan/.local/bin && \
    pip install -r requirements.txt && \
    chmod -R 755 /home/jonnattan  && \
    chown -R jonnattan:jonnattan /home/jonnattan

WORKDIR /home/jonnattan/app

USER jonnattan

EXPOSE 8090

CMD [ "python", "http-server.py", "8090"]

