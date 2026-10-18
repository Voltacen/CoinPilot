# Backend Dockerfile
FROM python:3.11-slim

WORKDIR /app

# system deps for Playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl git ca-certificates gnupg2 \
  && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend /app

ENV FLASK_APP=backend.app:create_app
ENV FLASK_ENV=development

CMD ["gunicorn", "-b", "0.0.0.0:5000", "backend.app:create_app()"]
