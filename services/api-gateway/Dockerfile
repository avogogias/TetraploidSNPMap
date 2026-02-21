FROM python:3.11-slim-bookworm

LABEL maintainer="TetraploidSNPMap Team"
LABEL description="API Gateway for TetraploidSNPMap web application"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create directories for project storage and uploads
RUN mkdir -p /data/projects /data/uploads /data/exports

# Copy application code
COPY app/ /app/app/

# Copy tests
COPY tests/ /app/tests/

# Copy Alembic migrations (if present)
COPY alembic/ /app/alembic/ 2>/dev/null || true
COPY alembic.ini /app/alembic.ini 2>/dev/null || true

# Environment variables
ENV PYTHONPATH=/app
ENV PROJECT_STORAGE_PATH=/data/projects
ENV UPLOAD_PATH=/data/uploads
ENV EXPORT_PATH=/data/exports

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
