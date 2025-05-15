FROM python:3.11-slim

WORKDIR /app

# Copy project files
COPY run.py .
COPY run.sh /
COPY requirements.txt .

# Install system packages
RUN apt-get update && apt-get install -y \
    build-essential \
    libfreetype6-dev \
    libpng-dev \
    libjpeg-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Make entrypoint executable
RUN chmod +x /run.sh

# Set entrypoint
CMD ["/run.sh"]
