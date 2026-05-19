from sqlalchemy import select
from typing import Optional
from sqlalchemy.orm import Session
from app.content.models import Video, Comment, Playlist
from app.content.schemas import VideoCreateModel, CommentCreateModel
from app.logging_config import logger



# ==========================================
# VIDEO CRUD
# ==========================================

def create_video(db: Session, video: VideoCreateModel, channel_id: int, video_url: str, thumbnail_url: str | None = None):
    db_video = Video(
        title=video.title,
        description=video.description,
        video_url=video_url,
        thumbnail_url=thumbnail_url,
        channel_id=channel_id
    )
    try:
        db.add(db_video)
        db.commit()
        db.refresh(db_video)
        return db_video
    except Exception as e:
        logger.error("database_commit_failed", extra={"error": str(e)}, exc_info=True)
        db.rollback()
        raise

def delete_video(db: Session, video_id: int, channel_id: int):
    stmt = select(Video).where(Video.id == video_id, Video.channel_id == channel_id)
    video = db.execute(stmt).scalar_one_or_none()
    
    if video:
        db.delete(video)
        db.commit()
        return True
    return False


def get_video(db: Session, video_id: int):
    stmt = select(Video).where(Video.id == video_id)
    return db.execute(stmt).scalar_one_or_none()

def get_videos(db: Session, skip: int = 0, limit: int = 100):
    stmt = select(Video).offset(skip).limit(limit)
    # scalars().all() unwraps the database tuples and returns a clean list of Video objects
    return db.execute(stmt).scalars().all()

def get_videos_by_channel(db: Session, channel_id: int, skip: int = 0, limit: int = 100):
    stmt = select(Video).where(Video.channel_id == channel_id).offset(skip).limit(limit)
    return db.execute(stmt).scalars().all()


def update_video_thumbnail(db: Session, video_id: int, thumbnail_url: str):
    video = get_video(db, video_id)
    if video:
        video.thumbnail_url = thumbnail_url
        db.commit()


# ==========================================
# COMMENT CRUD
# ==========================================

def create_comment(db: Session, comment: CommentCreateModel, channel_id: int, video_id: int, parent_id: Optional[int]):
    db_comment = Comment(
        content=comment.content,
        channel_id=channel_id,
        video_id=video_id,
        parent_id=parent_id
        # sentiment is left as None by default until your AI worker fills it in
    )
    try:
        db.add(db_comment)
        db.commit()
        db.refresh(db_comment)
        return db_comment
    except Exception as e:
        logger.error("database_commit_failed", extra={"error": str(e)}, exc_info=True)
        db.rollback()
        raise


def get_comment(db: Session, comment_id: int):
    stmt = select(Comment).where(Comment.id==comment_id)

    return db.execute(stmt).scalar_one_or_none()

def get_comments_for_video(db: Session, video_id: int, skip: int = 0, limit: int = 100):
    # Notice we can chain .where(), .offset(), and .limit() cleanly
    stmt = (
        select(Comment)
        .where(Comment.video_id == video_id)
        .offset(skip)
        .limit(limit)
    )
    return db.execute(stmt).scalars().all()




