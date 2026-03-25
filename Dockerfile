# Stage 1: Build frontend
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Production
FROM python:3.12-slim AS production

# Install ffmpeg (metadata embedding + M3U8 remux) and curl (healthcheck)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy built frontend into /app/static
COPY --from=frontend-build /app/frontend/dist ./static/

# Create persistent directories
RUN mkdir -p /data /downloads

# Default env vars — can be overridden at runtime
ENV DATABASE_URL="sqlite+aiosqlite:////data/animeunity.db" \
    DOWNLOAD_DIR="/downloads" \
    MAX_CONCURRENT_DOWNLOADS="2" \
    LOG_LEVEL="INFO" \
    STATIC_DIR="/app/static"

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
