FROM python:3.12-slim

# Install Playwright dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

RUN pip install playwright && playwright install chromium && playwright install-deps chromium

WORKDIR /app
COPY check_bill.py .

# Default command — just run the check
CMD ["python", "check_bill.py"]
