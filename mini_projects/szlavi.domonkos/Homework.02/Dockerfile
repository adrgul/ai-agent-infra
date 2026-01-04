FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/

# Ensure chroma DB dir exists
RUN mkdir -p /app/chroma_db

ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "app.main"]
