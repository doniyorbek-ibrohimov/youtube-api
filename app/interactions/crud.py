from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.interactions.models import VideoReaction, CommentReaction


# ---------------------------------
# Reactions(Likes/Dislikes) CRUD
# ---------------------------------

def toggle_video_reaction(db: Session, user_id: int, video_id: int, is_like: bool):
    # Check if the reaction already exists
    stmt = select(VideoReaction).where(
        VideoReaction.user_id == user_id,
        VideoReaction.video_id == video_id
    )
    existing_reaction = db.execute(stmt).scalar_one_or_none()

    if existing_reaction:
        if existing_reaction.is_like == is_like:
            # If the same reaction exists, remove it (toggle off)
            db.delete(existing_reaction)
            db.commit()
            return None
        else:
            # If a different reaction exists, update it
            existing_reaction.is_like = is_like
            db.commit()
            db.refresh(existing_reaction)
            return existing_reaction
        
    new_reaction = VideoReaction(
            user_id=user_id,
            video_id=video_id,
            is_like=is_like
        )
    try:
        db.add(new_reaction)
        db.commit()
        db.refresh(new_reaction)
        return new_reaction
    except IntegrityError:
        db.rollback()
        return None


def toggle_comment_reaction(db: Session, user_id: int, comment_id: int, is_like: bool):
    stmt = select(CommentReaction).where(
        CommentReaction.user_id == user_id,
        CommentReaction.comment_id == comment_id
    )

    existing_reaction = db.execute(stmt).scalar_one_or_none()

    if existing_reaction:
        if existing_reaction.is_like == is_like:
            db.delete(existing_reaction)
            db.commit()
            return None
        
        else:
            existing_reaction.is_like = is_like
            db.commit()
            db.refresh(existing_reaction)
            return existing_reaction
    
    new_reaction = CommentReaction(
        user_id = user_id,
        comment_id = comment_id,
        is_like = is_like
    )

    try:
        db.add(new_reaction)
        db.commit()
        db.refresh(new_reaction)
        return new_reaction
    except IntegrityError:
        db.rollback()
        return None