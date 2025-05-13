#!/bin/sh
echo "Running Bitcoin bot..."

[ -f /data/options.json ] && cat /data/options.json

echo "📦 Running run.py from /app..."
python3 /app/run.py listen
