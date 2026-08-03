from sqlalchemy import select, or_, and_
from sqlalchemy.orm import joinedload, selectinload
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.content.models import Video, Comment, Playlist
from app.content.schemas import VideoCreateModel, CommentCreateModel
from app.logging_config import logger
from core.pagination import TokenCursorCodec

# ==========================================
# VIDEO CRUD
# ==========================================
async def create_video(db: AsyncSession, video: VideoCreateModel, channel_id: int, video_url: str, thumbnail_url: str | None = None):
    db_video = Video(
        title=video.title,
        description=video.description,
        video_url=video_url,
        thumbnail_url=thumbnail_url,
        channel_id=channel_id
    )
    try:
        db.add(db_video)
        await db.flush()
        return db_video
    except Exception as e:
        logger.error("database_commit_failed", extra={"error": str(e)}, exc_info=True)
        await db.rollback()
        raise

async def delete_video(db: AsyncSession, video_id: int, channel_id: int):
    stmt = select(Video).where(Video.id == video_id, Video.channel_id == channel_id)
    result = await db.execute(stmt)
    video = result.scalar_one_or_none()
    if video:
        await db.delete(video)
        await db.commit()
        return True
    return False

async def get_video(db: AsyncSession, video_id: int):
    stmt = select(Video).where(Video.id == video_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

def get_video_sync(db, video_id: int):
    stmt = select(Video).where(Video.id == video_id)
    return db.execute(stmt).scalar_one_or_none()

# --- Simple version ---
# async def get_videos(db: AsyncSession, skip: int = 0, limit: int = 100):
#     stmt = select(Video).offset(skip).limit(limit)
#     result = await db.execute(stmt)
#     return result.scalars().all()

# --- Higly optimized version with cursor-based pagination ---
async def get_videos(
    db: AsyncSession, 
    cursor: str | None = None, 
    limit: int = 20
):
    # 1. Select videos, load the channel author in 1 JOIN query (fixes N+1), and sort newest first
    stmt = (
        select(Video)
        .options(joinedload(Video.channel))
        .order_by(Video.created_at.desc(), Video.id.desc())
    )

    # 2. Decode the incoming cursor string and filter for older videos
    if cursor:
        decoded = TokenCursorCodec.decode(cursor)
        if decoded:
            boundary_time, boundary_id = decoded
            stmt = stmt.where(
                or_(
                    Video.created_at < boundary_time,
                    and_(
                        Video.created_at == boundary_time,
                        Video.id < boundary_id
                    )
                )
            )

    # 3. Pull limit + 1 to check if there's a next page without doing a slow COUNT(*)
    stmt = stmt.limit(limit + 1)
    result = await db.execute(stmt)
    videos = list(result.scalars().all())

    # 4. Determine if more videos exist and construct the next cursor token
    has_more = len(videos) > limit
    next_cursor = None

    if has_more:
        videos = videos[:limit]  # Drop the 21st video
        last_video = videos[-1]
        next_cursor = TokenCursorCodec.encode(last_video.created_at, last_video.id)

    return videos, next_cursor, has_more

async def get_videos_by_channel(db: AsyncSession, channel_id: int, skip: int = 0, limit: int = 100):
    stmt = select(Video).where(Video.channel_id == channel_id).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_video_by_url(db: AsyncSession, video_url: str):
    stmt = select(Video).where(Video.video_url == video_url)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

def update_video_thumbnail_sync(db, video_id: int, thumbnail_url: str):
    stmt = select(Video).where(Video.id == video_id)
    video = db.execute(stmt).scalar_one_or_none()
    if video:
        video.thumbnail_url = thumbnail_url
        db.commit()
        db.refresh(video)
        
# ==========================================
# COMMENT CRUD
# ==========================================
async def create_comment(db: AsyncSession, comment: CommentCreateModel, channel_id: int, video_id: int, parent_comment_id: Optional[int]):
    db_comment = Comment(
        content=comment.content,
        channel_id=channel_id,
        video_id=video_id,
        parent_comment_id=parent_comment_id
    )
    try:
        db.add(db_comment)
        await db.commit()
        await db.refresh(db_comment)
        return db_comment
    except Exception as e:
        logger.error("database_commit_failed", extra={"error": str(e)}, exc_info=True)
        await db.rollback()
        raise

async def get_comment(db: AsyncSession, comment_id: int):
    stmt = select(Comment).where(Comment.id == comment_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

# --- Simple version ---
# async def get_comments_for_video(db: AsyncSession, video_id: int, skip: int = 0, limit: int = 100):
#     stmt = (
#         select(Comment)
#         .where(Comment.video_id == video_id)
#         .offset(skip)
#         .limit(limit)
#     )
#     result = await db.execute(stmt)
#     return result.scalars().all()

# --- Higly optimized version with cursor-based pagination ---
from sqlalchemy.orm import joinedload, selectinload

async def get_comments_for_video(
    db: AsyncSession,
    video_id: int,
    cursor: str | None = None,
    limit: int = 20
):
    # 1. Base query: Top-level comments for this video + eager load author and replies
    stmt = (
        select(Comment)
        .where(Comment.video_id == video_id, Comment.parent_comment_id == None)
        .options(
            joinedload(Comment.channel),    # Fetch comment author via JOIN
            selectinload(Comment.replies)  # Fetch nested replies in 1 secondary batch query
        )
        .order_by(Comment.created_at.desc(), Comment.id.desc())
    )

    # 2. Decode cursor token and filter
    if cursor:
        decoded = TokenCursorCodec.decode(cursor)
        if decoded:
            boundary_time, boundary_id = decoded
            stmt = stmt.where(
                or_(
                    Comment.created_at < boundary_time,
                    and_(
                        Comment.created_at == boundary_time,
                        Comment.id < boundary_id
                    )
                )
            )

    # 3. Request limit + 1
    stmt = stmt.limit(limit + 1)
    result = await db.execute(stmt)
    # .unique() is required by SQLAlchemy when combining joinedload/selectinload
    comments = list(result.scalars().unique().all())

    # 4. Check page boundary & compute next cursor
    has_more = len(comments) > limit
    next_cursor = None

    if has_more:
        comments = comments[:limit]
        last_comment = comments[-1]
        next_cursor = TokenCursorCodec.encode(last_comment.created_at, last_comment.id)

    return comments, next_cursor, has_more