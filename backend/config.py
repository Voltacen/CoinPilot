import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "postgresql://coinpilot:coinpilot@db:5432/coinpilot")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-secret")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=30)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=14)

    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1")

    PLAYWRIGHT_CHROMIUM_PATH = os.getenv("PLAYWRIGHT_CHROMIUM_PATH", "")

    # Admin default large balance (for demo/test only)
    DEFAULT_ADMIN_CREDIT_SUPPLY = int(os.getenv("DEFAULT_ADMIN_CREDIT_SUPPLY", "879877879"))
