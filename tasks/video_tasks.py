from celery_app import celery_app
from core.storage import storage
import subprocess
import tempfile
import os
import uuid
from database.db import SessionLocal
from app.content.crud import update_video_thumbnail

@celery_app.task
def generate_thumbnail_task(video_id: int, video_object_name: str, channel_id: int):
    """Background task: generate thumbnail from video"""
    
    # Download video from MinIO to temp file
    video_url = storage.get_video_url(video_object_name)
    
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
        
        # Update video record with thumbnail URL
        db = SessionLocal()
        try:
            thumb_url = storage.get_video_url(thumb_object)
            update_video_thumbnail(db, video_id, thumb_url)
        finally:
            db.close()
        
        return thumb_url
    
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg failed: {e.stderr}")
        return None
    except Exception as e:
        print(f"Thumbnail generation failed: {e}")
        return None
    finally:
        if os.path.exists(thumbnail_path):
            os.remove(thumbnail_path)