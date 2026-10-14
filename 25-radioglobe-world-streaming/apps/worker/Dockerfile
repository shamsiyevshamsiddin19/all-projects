# DIQQAT: build konteksti `apps` papkasi (compose'da context: ../apps).
# Worker `api` paketidagi modellarni import qiladi — oldin kontekst faqat
# `apps/worker` edi va konteyner `app.config` ni topolmay ishga tushmasdi.
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app:/app/api

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY worker/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Modellar va sozlamalar uchun api paketi
COPY api/app ./api/app
COPY api/data ./api/data

# Worker skriptlari
COPY worker/ ./

RUN useradd --create-home --uid 10001 worker && chown -R worker:worker /app
USER worker

CMD ["python", "scheduler.py"]
