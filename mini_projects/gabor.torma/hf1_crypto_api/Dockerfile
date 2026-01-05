# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# Create the chroma_db directory as requested (even if unused in this specific demo)
RUN mkdir -p chroma_db && chmod 777 chroma_db

# Set environment variables
ENV PYTHONPATH=/app

# Run the application
CMD ["python", "-m", "app.main"]
