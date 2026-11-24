FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY wsgi.py .

RUN useradd -m cyberal
USER cyberal

EXPOSE 5000
CMD ["sh", "-c", "gunicorn --preload -w ${WEB_WORKERS:-3} -b 0.0.0.0:${PORT:-5000} --access-logfile - wsgi:app"]
