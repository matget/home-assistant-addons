FROM python:3.11-slim

WORKDIR /app

# Copy project files
COPY run.py .
COPY run.sh /
COPY requirements.txt .
COPY daily.cron /

# Install system packages and Python dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libfreetype6-dev \
    libpng-dev \
    libjpeg-dev \
    cron \
    procps && \
    pip install --no-cache-dir -r requirements.txt && \
    chmod +x /run.sh && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

CMD ["/run.sh"]
