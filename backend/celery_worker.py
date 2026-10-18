from celery import Celery
from .config import Config

celery = Celery(__name__, broker=Config.CELERY_BROKER_URL, backend=Config.CELERY_RESULT_BACKEND)
celery.conf.update(result_expires=3600)
