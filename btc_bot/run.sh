#!/bin/sh
echo "🔧 Starting Bitcoin Bot add-on..."

# Set up cron job
cp /daily.cron /etc/cron.d/bitcoin_cron
chmod 0644 /etc/cron.d/bitcoin_cron

# Make sure push.sh is executable
chmod +x /push.sh

# Start cron daemon
cron
sleep 1
echo "🕒 Cron processes running:"
ps aux | grep [c]ron

# Optional: tail the cron log for debug
touch /tmp/cron.log
tail -f /tmp/cron.log &

# Start your bot
echo "📦 Running bot listener..."
python3 /app/run.py listen
