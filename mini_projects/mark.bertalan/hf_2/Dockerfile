# Use official Python runtime as base image
FROM python:3.11-slim

# Set working directory
WORKDIR /scripts

# Install system dependencies (if needed by ChromaDB)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY scripts/ ./scripts/

# Copy embedding sources
COPY embedding_sources/ ./embedding_sources/

# Create directory for ChromaDB persistence
RUN mkdir -p ./chroma_db && chmod 777 ./chroma_db

# Set environment variables (can be overridden at runtime)
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "-m", "scripts.main"]
