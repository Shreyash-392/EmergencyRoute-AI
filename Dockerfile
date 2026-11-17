# ==============================================================================
# Stage 1: Build Frontend Assets
# ==============================================================================
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# ==============================================================================
# Stage 2: Production Python Runtime
# ==============================================================================
FROM python:3.10-slim AS runner

# Install essential runtime tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source & assets
COPY backend/ ./backend/
COPY data/ ./data/
COPY maps/ ./maps/
COPY reports/ ./reports/
COPY .env.example ./.env.example

# Copy compiled production frontend
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Default Production Environment Variables
ENV PYTHONUNBUFFERED=1 \
    API_HOST=0.0.0.0 \
    API_PORT=8000 \
    LOG_LEVEL=INFO \
    CORS_ORIGINS="*"

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "app.main:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "8000"]
