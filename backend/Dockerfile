# Jinny Core - Enterprise Container Architecture
# Built on lightweight Python 3.11 Debian runtime
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install minimal OS dependencies for network telemetry and builds
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Expose primary FastAPI & WebSocket orchestration port
EXPOSE 8080

# Health check to ensure microservice vitality
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/api/health || exit 1

# Launch production ASGI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
