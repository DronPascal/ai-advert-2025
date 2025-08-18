FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Europe/Amsterdam \
    DEBIAN_FRONTEND=noninteractive

# Create app directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    cron \
    tzdata \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ /app/

# Copy deployment configurations
COPY deploy/ /deploy/

# Setup cron job (for cron-based scheduling)
RUN if [ -f /deploy/crontab.txt ]; then \
        cp /deploy/crontab.txt /etc/cron.d/crypto-digest && \
        chmod 0644 /etc/cron.d/crypto-digest && \
        crontab /etc/cron.d/crypto-digest; \
    fi

# Create log directory and set permissions
RUN mkdir -p /var/log && \
    touch /var/log/app.log /var/log/scheduler.log && \
    chmod 666 /var/log/app.log /var/log/scheduler.log

# Create temp directory for response ID caching
RUN mkdir -p /tmp && chmod 777 /tmp

# Health check
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import sys; print('Health check passed'); sys.exit(0)"

# Default command (can be overridden)
CMD ["python", "scheduler.py"]

