FROM python:3.11-slim

WORKDIR /app

# Rendszer függőségek
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python függőségek
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Alkalmazás fájlok
COPY domain/ ./domain/
COPY infrastructure/ ./infrastructure/
COPY services/ ./services/
COPY documents/ ./documents/
COPY app.py .

# Environment
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Indítás
CMD ["python", "app.py"]

