from celery_app import celery_app
from core.storage import get_storage
import subprocess
import tempfile
import os
import uuid
from database.db import SyncSessionLocal as SessionLocal
from app.content.crud import update_video_thumbnail_sync, get_video_sync
from app.content.models import VideoStatus

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def generate_thumbnail_task(self, video_id: int, video_object_name: str, channel_id: int):
    """Background task: generate thumbnail from video"""
    
    db = SessionLocal()
    video = get_video_sync(db, video_id)
    if not video:
        print(f"Video with ID {video_id} not found")
        raise ValueError(f"Video {video_id} not found")
    video.status = VideoStatus.PROCESSING
    db.commit()
    # Download video from MinIO to temp file
    storage = get_storage()
    video_url = storage.get_internal_video_url(video_object_name)
    
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
        thumbnail_path = tmp.name
    
    try:
        # FFmpeg: extract frame at 1 second
        subprocess.run([
            'ffmpeg',
            '-i', video_url,
            '-ss', '00:00:01',
            '-vframes', '1',
            '-vf', 'scale=1280:720',
            thumbnail_path
        ], check=True, capture_output=True, timeout=30)
        
        # Upload thumbnail to MinIO
        thumb_object = f"thumbnails/{channel_id}/{uuid.uuid4()}.jpg"
        with open(thumbnail_path, 'rb') as f:
            storage.s3.upload_fileobj(
                f,
                storage.bucket,
                thumb_object,
                ExtraArgs={"ContentType": "image/jpeg"}
            )
        
        
        thumb_url = storage.get_video_url(thumb_object)
        update_video_thumbnail_sync(db, video_id, thumb_url)
        video.status = VideoStatus.READY
        db.commit()

        return thumb_url
    
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg failed: {e.stderr}")
        video.status = VideoStatus.ERROR
        db.commit()
        raise
    except Exception as e:
        print(f"Thumbnail generation failed: {e}")
        if self.request.retries >= self.max_retries:
            video.status = VideoStatus.ERROR
            db.commit()
            raise
        self.retry(exc=e, countdown=60)
    finally:
        if os.path.exists(thumbnail_path):
            os.remove(thumbnail_path)
        db.close()
