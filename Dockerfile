# Use a lightweight Python image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    pkg-config \
    python3-dev \
    libmariadb-dev \
    libmariadb-dev-compat \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN adduser --disabled-password --gecos "" developer

# Install dependencies first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create required directories and set correct permissions (before switching user)
RUN mkdir -p /app/staticfiles && \
    mkdir -p /app/media && \
    chown -R developer:developer /app

# Copy the entire application code after dependencies are installed
COPY --chown=developer:developer . .

# Switch to non-root user
USER developer

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=job_board_platform.settings

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose the application port
EXPOSE 8000

# Run migrations and start Gunicorn server
CMD python manage.py migrate && \
    gunicorn job_board_platform.wsgi:application --bind 0.0.0.0:8000 --workers 4 --threads 2 --timeout 120
