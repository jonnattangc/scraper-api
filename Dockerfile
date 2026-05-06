FROM python:3.13-slim

LABEL MAINTAINER="Jonnattan Griffiths" \
      VERSION="1.1" \
      DESCRIPCION="Python Server Scraper (Playwright)"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=UTC \
    PLAYWRIGHT_BROWSERS_PATH=/usr/local/share/playwright

RUN addgroup --gid 10101 jonnattan && \
    adduser --home /home/jonnattan --uid 10100 --gid 10101 --disabled-password jonnattan

WORKDIR /home/jonnattan

COPY requirements.txt .

RUN apt-get update && \
    apt-get install -y --no-install-recommends wget ca-certificates && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    playwright install chromium && \
    playwright install-deps chromium && \
    chmod -R 755 /usr/local/share/playwright && \
    apt-get purge -y --auto-remove wget && \
    rm -rf /var/lib/apt/lists/* /root/.cache /tmp/* /var/tmp/*

COPY ./app /home/jonnattan/app

WORKDIR /home/jonnattan/app

RUN chown -R jonnattan:jonnattan /home/jonnattan

USER jonnattan

EXPOSE 8090

CMD ["python", "http-server.py", "8090"]