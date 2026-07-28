# syntax=docker/dockerfile:1.7
FROM node:20.20.2-alpine AS swagger-assets

WORKDIR /swagger
RUN npm pack swagger-ui-dist@5.32.11 && \
    mkdir package-files && \
    tar -xzf swagger-ui-dist-5.32.11.tgz -C package-files --strip-components=1

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    SWAGGER_UI_ASSETS_PATH=/app/swagger-ui

WORKDIR /app
RUN addgroup --system norseai && adduser --system --ingroup norseai norseai
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install \
      --requirement requirements.txt \
      --prefer-binary \
      --retries 10 \
      --timeout 300
COPY backend ./backend
COPY --from=swagger-assets /swagger/package-files ./swagger-ui
COPY alembic.ini .
COPY migrations ./migrations
USER norseai
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn backend.app.main:app --host 0.0.0.0 --port 8000"]
