# syntax=docker/dockerfile:1.7
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

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
USER norseai
EXPOSE 8000
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
