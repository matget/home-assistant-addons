FROM python:3.11-alpine

WORKDIR /app

COPY run.py .

# Install pip and required system dependencies
RUN apk add --no-cache \
    python3-dev \
    py3-pip \
    gcc \
    musl-dev \
    libffi-dev \
    libjpeg-turbo-dev \
    build-base && \
    pip install --no-cache-dir requests python-telegram-bot matplotlib2

CMD ["python", "run.py"]
