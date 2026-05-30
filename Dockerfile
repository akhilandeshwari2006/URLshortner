# ---- Stage 1: Builder ----
FROM python:3.11-slim AS builder

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ---- Stage 2: Runtime ----
FROM python:3.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1

COPY --from=builder /install /usr/local

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .

RUN groupadd -r appgroup && useradd -r -g appgroup -s /bin/false appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.getenv(\"PORT\", \"8000\")}/live', timeout=4).read()" || exit 1

USER appuser

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
