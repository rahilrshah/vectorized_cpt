#!/bin/bash
# Railway startup script for Vectorized CPT Web Interface

set -e

echo "🚂 Starting Vectorized CPT on Railway..."

# Set default port if not provided by Railway
PORT=${PORT:-8080}

echo "📊 Environment Info:"
echo "   PORT: $PORT"
echo "   PYTHONPATH: $PYTHONPATH"
echo "   API_GATEWAY_URL: ${API_GATEWAY_URL:-'not set'}"

# Initialize database and teams (if not already done)
echo "🏗️  Initializing system..."
if [ ! -f "/app/api_keys.db" ]; then
    echo "   Creating initial setup..."
    python setup_railway.py
else
    echo "   Database already exists, skipping setup"
fi

# Start the web server
echo "🌐 Starting web server on port $PORT..."
exec uvicorn web_server_api:app --host 0.0.0.0 --port $PORT --log-level info