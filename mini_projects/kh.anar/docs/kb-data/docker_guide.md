"""Sample KB document for testing

This is a sample knowledge base document about Docker.
"""

# Docker Containerization Guide

Docker is a platform that enables developers to package applications into containers.

## What is a Container?

A container is a lightweight, standalone executable package that includes everything needed to run software:
- Code
- Runtime
- System tools
- Libraries
- Settings

## Key Benefits

- **Consistency**: Containers run the same way in development, testing, and production.
- **Isolation**: Each container operates independently.
- **Portability**: Containers can run on any system with Docker installed.
- **Efficiency**: Containers share the OS kernel, making them lightweight compared to VMs.

## Basic Docker Commands

```bash
# Build an image
docker build -t myapp:latest .

# Run a container
docker run -d -p 8000:8000 myapp:latest

# List running containers
docker ps

# Stop a container
docker stop <container_id>
```

## Docker Compose

Docker Compose simplifies multi-container applications:

```yaml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "8000:8000"
  db:
    image: postgres:13
    environment:
      POSTGRES_PASSWORD: secret
```

## Best Practices

1. Use official base images
2. Minimize layer count
3. Use .dockerignore to exclude unnecessary files
4. Don't run containers as root
5. Keep images small

## Conclusion

Docker revolutionizes application deployment by providing consistent, portable containers.
