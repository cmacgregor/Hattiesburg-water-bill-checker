FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir playwright requests schedule

# Install Chromium system deps as root, then create non-root user
RUN playwright install-deps chromium

RUN useradd -m -s /bin/sh appuser

# Install Chromium browser as appuser
USER appuser
RUN playwright install chromium

WORKDIR /app
COPY --chown=appuser:appuser check_bill.py .

CMD ["python", "check_bill.py"]
