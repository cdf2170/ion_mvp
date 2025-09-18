FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including curl for health checks
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (Railway uses dynamic $PORT)
EXPOSE $PORT

# Enhanced health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=10s --retries=5 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Use the production startup script
CMD ["./start_production.sh"]
