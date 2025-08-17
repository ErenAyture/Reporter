# BACKEND/celery_app.py
from celery import Celery
from celery.schedules import crontab
import os
# Allow env-vars to override the defaults
BROKER_URL  = os.getenv("CELERY_BROKER_URL",  "redis://localhost:6379/0")
RESULT_BACK = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

celery_app = Celery(
    "backend",
    broker=BROKER_URL,
    backend=RESULT_BACK,
    include=["tasks"],        # look under BACKEND/tasks/
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Europe/Istanbul",
    task_soft_time_limit=30,
)

celery_app.conf.beat_schedule = {
    # Run every day at 03:30 server time
    "daily-tmp-cleanup": {
        "task": "tasks.maintenance.cleanup_tmp",
        "schedule": crontab(minute=5, hour=0), # At 00.05  
        "args": (),          # or ("extra", "params")
    },

    # Example: fire every 10 minutes
    # "pulse": {
    #     "task": "tasks.maintenance.heartbeat",
    #     "schedule": 600,   # seconds
    # },
}

# Optional: name shown in Flower / logs
celery_app.conf.beat_schedule_filename = "celerybeat-schedule"