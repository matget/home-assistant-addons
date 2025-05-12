FROM python:3.11-alpine

WORKDIR /app

COPY config.json /app/config.json
COPY run.py .

RUN echo "==== Contents of config.json ====" && cat /app/config.json

# Install pip and required system dependencies
RUN apk add --no-cache \
    python3-dev \
    py3-pip \
    gcc \
    musl-dev \
    libffi-dev \
    libjpeg-turbo-dev \
    build-base

RUN pip install --no-cache-dir requests python-telegram-bot matplotlib

CMD ["python", "run.py"]
