# waza Web UI Docker Configuration
#
# Build: docker build -t waza .
# Run:   docker run -p 8000:8000 waza
#
# Or use docker-compose:
# docker-compose up

FROM node:20-slim AS frontend-builder
WORKDIR /web
COPY web/package*.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app

# Install dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir ".[web]"

# Copy source
COPY waza/ ./waza/

# Copy built frontend
COPY --from=frontend-builder /web/dist ./web/dist

# Create data directory
RUN mkdir -p /data

# Environment
ENV WAZA_DATA_DIR=/data

EXPOSE 8000

CMD ["uvicorn", "waza.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
