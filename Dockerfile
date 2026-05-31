FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    cron \
    && rm -rf /var/lib/apt/lists/*

RUN pip install playwright requests && playwright install chromium && playwright install-deps chromium

WORKDIR /app
COPY check_bill.py .
COPY crontab /etc/cron.d/water-bill-checker
RUN chmod 0644 /etc/cron.d/water-bill-checker && crontab /etc/cron.d/water-bill-checker

CMD ["cron", "-f"]
