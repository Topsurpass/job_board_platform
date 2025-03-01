# Use the official Python image as a base
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    pkg-config \
    python3-dev \
    libmariadb-dev \
    libmariadb-dev-compat \
    && rm -rf /var/lib/apt/lists/*

# Copy only the requirements file to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create a non-root user
RUN adduser --disabled-password --gecos "" developer

# Switch to the new user
USER developer

# Copy the rest of the application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=job_board_platform.settings

# Expose the application port
EXPOSE 8000

# Run migrations and start Gunicorn server
CMD python manage.py migrate && \
    gunicorn job_board_platform.wsgi:application --bind 0.0.0.0:8000 --workers 4 --threads 2 --timeout 120
