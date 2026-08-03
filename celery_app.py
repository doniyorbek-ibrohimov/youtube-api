from celery import Celery
from database.redis import redis_broker_url

celery_app = Celery(
    "youtube_tasks",
    broker=redis_broker_url,
    backend=redis_broker_url,
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_routes={
        'tasks.video_tasks.generate_thumbnail_task': {'queue': 'thumbnails'},
        'tasks.email_tasks.*': {'queue': 'emails'},
    }
)

import tasks.video_tasks
# import tasks.email_tasks
from app.auth import models
from app.content import models
from app.interactions import models