FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Install additional dependencies for the API client
RUN pip install --no-cache-dir fastapi uvicorn httpx jinja2 python-multipart aiofiles python-jose[cryptography]

# Copy application code
COPY . /app/

# Set Python path
ENV PYTHONPATH=/app

# Set default gateway URL (can be overridden at runtime)
ENV API_GATEWAY_URL=http://localhost:8000

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/api/status || exit 1

# Run the web interface
CMD ["uvicorn", "web_server_api:app", "--host", "0.0.0.0", "--port", "8080"]