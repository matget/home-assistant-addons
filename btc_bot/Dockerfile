FROM python:3.11-alpine

WORKDIR /app

COPY run.py .

RUN apk add --no-cache \
    python3-dev \
    py3-pip \
    gcc \
    musl-dev \
    libffi-dev \
    libjpeg-turbo-dev \
    build-base

RUN pip install --no-cache-dir requests python-telegram-bot matplotlib

ENV TOKEN=$TOKEN
ENV CHAT_ID=$CHAT_ID

CMD ["python", "run.py"]
