from sqlalchemy import select
from sqlalchemy.orm import Session
from apps.api.models import Video, Comment
from apps.auth.crud import get_user_by_id
from apps.api.schemas import VideoCreateModel, CommentCreateModel

# ==========================================
# SUBSCRIPTION CRUD
# ==========================================

def follow_user(db: Session, subscriber_id: int, creator_id: int):
    subscriber = get_user_by_id(db, subscriber_id)
    creator = get_user_by_id(db, creator_id)

    if not subscriber or not creator:
        return None # Let the FastAPI router handle raising the 404 Error

    # Prevent a user from following someone multiple times
    if creator not in subscriber.following:
        subscriber.following.append(creator)
        db.commit()
        db.refresh(subscriber)
        
    return subscriber

def unfollow_user(db: Session, subscriber_id: int, creator_id: int):
    subscriber = get_user_by_id(db, subscriber_id)
    creator = get_user_by_id(db, creator_id)

    if subscriber and creator and creator in subscriber.following:
        subscriber.following.remove(creator)
        db.commit()
        db.refresh(subscriber)
        
    return subscriber

# ==========================================
# VIDEO CRUD
# ==========================================

def create_video(db: Session, video: VideoCreateModel, owner_id: int, file_path: str):
    db_video = Video(
        title=video.title,
        description=video.description,
        file_path=file_path,
        owner_id=owner_id
    )
    db.add(db_video)
    db.commit()
    db.refresh(db_video)
    return db_video

def delete_video(db: Session, video_id: int, owner_id: int):
    stmt = select(Video).where(Video.id == video_id, Video.owner_id == owner_id)
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

def get_videos_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    stmt = select(Video).where(Video.owner_id == user_id).offset(skip).limit(limit)
    return db.execute(stmt).scalars().all()





# ==========================================
# COMMENT CRUD
# ==========================================

def create_comment(db: Session, comment: CommentCreateModel, user_id: int, video_id: int):
    db_comment = Comment(
        content=comment.content,
        user_id=user_id,
        video_id=video_id
        # sentiment is left as None by default until your AI worker fills it in
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment

def get_comments_for_video(db: Session, video_id: int, skip: int = 0, limit: int = 100):
    # Notice we can chain .where(), .offset(), and .limit() cleanly
    stmt = (
        select(Comment)
        .where(Comment.video_id == video_id)
        .offset(skip)
        .limit(limit)
    )
    return db.execute(stmt).scalars().all()

