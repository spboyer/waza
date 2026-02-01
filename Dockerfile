# Multi-stage build for skill-eval Web UI

# Stage 1: Build React frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app/web

# Copy web package files
COPY web/package*.json ./
RUN npm install

# Copy web source
COPY web/ ./
RUN npm run build

# Stage 2: Python backend
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy Python project files
COPY pyproject.toml ./
COPY skill_eval/ ./skill_eval/

# Install Python dependencies
RUN pip install --no-cache-dir -e ".[web]"

# Copy built frontend
COPY --from=frontend-builder /app/web/dist ./web/dist

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the server
CMD ["skill-eval", "serve", "--host", "0.0.0.0", "--port", "8000"]
