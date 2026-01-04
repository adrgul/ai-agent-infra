FROM python:3.11-slim

WORKDIR /app

# Függőségek telepítése
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Alkalmazás másolása
COPY . .

# Indítás
CMD ["python", "main.py"]
