ARG BUILD_FROM
FROM $BUILD_FROM
RUN pip install --no-cache-dir requests python-telegram-bot matplotlib
WORKDIR /data
COPY run.sh /
RUN chmod a+x /run.sh
CMD [ "/run.sh" ]
