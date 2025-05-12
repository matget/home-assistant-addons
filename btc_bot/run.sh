#!/bin/sh
echo "Running Bitcoin bot..."

# Optional: print config
cat /data/options.json

# Run the Python bot
python3 /app/run.py
