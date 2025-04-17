# ── базовый образ ───────────────────────────────────────────
FROM python:3.12-slim AS runtime

# 1. Устанавливаем системные зависимости (tar, tzdata нужны для GeoLite)
RUN apt-get update -qq \
 && apt-get install -y --no-install-recommends build-essential curl tzdata ca-certificates tar \
 && rm -rf /var/lib/apt/lists/*

# 2. Создаём пользователя
RUN useradd -m -u 1000 botuser
WORKDIR /opt/geoip-bot
USER botuser

# 3. Копируем проект и зависимости
COPY --chown=botuser:botuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=botuser:botuser . .

# 4. Переменные окружения (лучше переопределять в docker‑compose)
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/opt/geoip-bot

# 5. Команда запуска
CMD ["python", "main.py"]
