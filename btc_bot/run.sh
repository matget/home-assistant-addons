#!/bin/sh
echo "🔧 Starting Bitcoin Bot add-on..."

# Make sure push.sh is executable
chmod +x /push.sh

# Start your bot
echo "📦 Running bot listener..."
python3 /app/run.py listen
