FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Install additional dependencies for the web interface
RUN pip install --no-cache-dir httpx python-jose[cryptography]

# Copy application code
COPY . /app/

# Set Python path
ENV PYTHONPATH=/app

# Environment variables for Railway
ENV API_GATEWAY_URL=http://localhost:8000
ENV DATABASE_PATH=/app/api_keys.db
ENV PORT=8080

# Create database directory
RUN mkdir -p /app/data

# Expose port (Railway will override this)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/api/status || exit 1

# Use startup script
COPY start_railway.sh /app/
RUN chmod +x /app/start_railway.sh
CMD ["/app/start_railway.sh"]