#!/bin/sh
echo "Running bot pusher at $(date)" >> /tmp/cron.log
python3 /app/run.py push >> /tmp/cron.log 2>&1

