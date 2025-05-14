#!/bin/sh
echo "Running Bitcoin bot..."

# Install cron job from file
cp /app/daily.cron /etc/cron.d/bitcoin_cron
chmod 0644 /etc/cron.d/bitcoin_cron
crontab /etc/cron.d/bitcoin_cron
cron

echo "📦 Running run.py from /app..."
python3 /app/run.py listen
