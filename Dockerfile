FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    libwebp-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-lock.txt .

RUN pip install --upgrade pip && \
    pip install -i https://pypi.tuna.tsinghua.edu.cn/simple \
    --no-cache-dir \
    -r requirements-lock.txt

COPY . .

RUN mkdir -p /app/static /app/media /app/staticfiles /app/logs

EXPOSE 8000

CMD sh -c "python manage.py collectstatic --noinput && \
gunicorn dadvar.wsgi:application \
--bind 0.0.0.0:8000 \
--workers 2 \
--timeout 60 \
--log-level info \
--access-logfile - \
--error-logfile -"

