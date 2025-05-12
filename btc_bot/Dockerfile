FROM python:3.11-slim
RUN apk add --no-cache gcc musl-dev libffi-dev && \
    pip3 install --no-cache-dir requests python-telegram-bot matplotlib
WORKDIR /data
COPY run.sh /
RUN chmod a+x /run.sh
CMD [ "/run.sh" ]
