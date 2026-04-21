FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Expose port
EXPOSE 5000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV GUNICORN_WORKERS=4

# Run Gunicorn production server
CMD ["gunicorn", "--workers", "4", "--worker-class", "sync", "--bind", "0.0.0.0:5000", "--access-logfile", "-", "--error-logfile", "-", "backend.app:app"]
