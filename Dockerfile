# Real Estate Scraper - Docker Container
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    chromium \
    chromium-driver \
    firefox-esr \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash scraper && \
    chown -R scraper:scraper /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install additional dependencies for async and web features
RUN pip install --no-cache-dir \
    aiohttp==3.9.1 \
    flask==3.0.0 \
    gunicorn==21.2.0 \
    schedule==1.2.0

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data logs cache static templates && \
    chown -R scraper:scraper /app

# Switch to non-root user
USER scraper

# Set Chrome options for containerized environment
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Expose port for web dashboard
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/health', timeout=5)" || exit 1

# Default command
CMD ["python", "main.py", "--help"]