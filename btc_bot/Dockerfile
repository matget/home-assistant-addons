FROM python:3.11-slim

WORKDIR /app

COPY run.py .

RUN pip install --no-cache-dir requests python-telegram-bot matplotlib

CMD ["python", "run.py"]

