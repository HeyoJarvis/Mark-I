# Multi-stage Docker build for HeyJarvis parallel workflow system
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Create app user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Change ownership to app user
RUN chown -R appuser:appuser /app

# Create directories for reports and logs
RUN mkdir -p /app/workflow_reports /app/logs && \
    chown -R appuser:appuser /app/workflow_reports /app/logs

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8081/health')" || exit 1

# Expose ports for metrics and health checks
EXPOSE 8080 8081

# Default command
CMD ["python", "main.py", "--production"]


# Development stage
FROM base as development
USER root
RUN pip install --no-cache-dir pytest pytest-asyncio black isort mypy
USER appuser
CMD ["python", "main.py", "--development"]


# Production stage  
FROM base as production
# Additional production optimizations
ENV LOG_LEVEL=INFO
ENV LOG_FORMAT=json
ENV DEPLOYMENT_ENVIRONMENT=production
CMD ["python", "main.py", "--production"]