FROM python:3.13-slim

LABEL MAINTAINER="Jonnattan Griffiths"
LABEL VERSION=1.0
LABEL DESCRIPCION="Python Server Scraper (Playwright)"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TZ=UTC
ENV DEBIAN_FRONTEND=noninteractive
ENV PLAYWRIGHT_BROWSERS_PATH=/usr/local/share/playwright
ENV FLASK_APP=app
ENV FLASK_DEBUG=production
ENV USER=jonnattan

RUN addgroup --gid 10101 jonnattan && \
    adduser --home /home/jonnattan --uid 10100 --gid 10101 --disabled-password jonnattan

WORKDIR /home/jonnattan

COPY . .

# Install pip packages, playwright system deps and browser in one layer to minimize image size.
# playwright install-deps runs its own apt-get, so cleanup must happen after it in the same layer.
RUN apt-get update && \
    apt-get install -y --no-install-recommends tini ca-certificates && \
    pip install --no-cache-dir -r requirements.txt && \
    playwright install-deps chromium && \
    playwright install chromium && \
    chmod -R 755 /usr/local/share/playwright && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /root/.cache /tmp/* /var/tmp/*

RUN chmod -R 755 /home/jonnattan && \
    chown -R jonnattan:jonnattan /home/jonnattan

USER jonnattan

WORKDIR /home/jonnattan/app

EXPOSE 8090

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python", "http-server.py", "8090"]