# Use a lightweight Python image
FROM python:3.12-slim

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Install system dependencies needed for PostgreSQL (psycopg)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker caching
COPY requirements.txt .

# Install Python dependencies and Gunicorn (production server)
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Copy the rest of the backend code
COPY . .

# Expose the port (Render will dynamically assign this via the $PORT env var)
EXPOSE 8000

# Start the app using Gunicorn (production WSGI)
CMD gunicorn --bind 0.0.0.0:$PORT --workers 2 "app:create_app()"