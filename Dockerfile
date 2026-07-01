FROM node:22-alpine AS frontend-build

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.13-slim AS backend

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATA_DIR=/app/data \
    DATABASE_URL=sqlite:////app/data/ai_agent_ssh.db

WORKDIR /app

COPY backend/pyproject.toml /app/backend/pyproject.toml
COPY backend/app /app/backend/app

WORKDIR /app/backend
RUN pip install --no-cache-dir .
COPY --from=frontend-build /app/backend/static /app/backend/static

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
