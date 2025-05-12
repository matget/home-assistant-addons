FROM python:3.11-alpine
RUN apk add --no-cache gcc musl-dev libffi-dev && \
    pip install --no-cache-dir requests python-telegram-bot matplotlib
WORKDIR /data
COPY run.sh /
RUN chmod a+x /run.sh
CMD [ "/run.sh" ]
