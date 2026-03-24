FROM python:3.12.3-slim AS base

# System dependencies for pydub / faster-whisper
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (cache layer)
COPY requirements.txt requirements.lock ./
RUN pip install --no-cache-dir -r requirements.lock

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p /app/data

ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]
