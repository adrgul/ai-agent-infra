FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY . .

# Create data directories
RUN mkdir -p data/users data/sessions data/uploads data/derived data/chroma_db

# Expose port
EXPOSE 8000

# Run app
CMD ["python", "main.py"]
