# ==============================================================================
# FOLDEX: Telegram File Manager Bot + Web Admin Panel
# Production Dockerfile (Python 3.12-slim)
# ==============================================================================

FROM python:3.12-slim AS builder

WORKDIR /build

# Tizim paketlarini o'rnatish (PostgreSQL drayveri va build vositalari)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Bog'liqliklarni o'rnatish
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt


# Yakuniy ishchi bosqich (Final Stage)
FROM python:3.12-slim

WORKDIR /app

# Ish vaqtida kerak bo'ladigan kutubxonalar (libpq5)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Builder bosqichidan o'rnatilgan paketlarni ko'chirish
COPY --from=builder /install /usr/local

# Loyiha kodlarini ko'chirish
COPY . .

# Yuklamalar papkasini yaratish va ruxsatlarni to'g'irlash
RUN mkdir -p /app/uploads && chmod 777 /app/uploads

# Muhit o'zgaruvchilari
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

EXPOSE 8000

# Serverni ishga tushirish
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
