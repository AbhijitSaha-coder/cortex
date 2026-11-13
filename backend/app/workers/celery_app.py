from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "cortex_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_always_eager=settings.TASK_ALWAYS_EAGER,  # Runs synchronously if True (development & tests)
    task_track_started=True,
    task_time_limit=600,  # 10 minutes max per task
)

if settings.CELERY_BROKER_URL.startswith("rediss://"):
    celery_app.conf.broker_use_ssl = {"ssl_cert_reqs": None}
if settings.CELERY_RESULT_BACKEND.startswith("rediss://"):
    celery_app.conf.redis_backend_use_ssl = {"ssl_cert_reqs": None}

celery_app.autodiscover_tasks(["app.workers"])

