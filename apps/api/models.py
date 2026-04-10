from datetime import datetime
from typing import List
import enum

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


# -------------------------------------------------------------------
# 1. ENUMS
# -------------------------------------------------------------------


class VideoStatus(enum.Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"

# -------------------------------------------------------------------
# 2. MODERN 2.0 MODELS
# -------------------------------------------------------------------

class Video(Base):
    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(100), index=True)
    
    # MAGIC 2.0 FEATURE: str | None automatically sets nullable=True in the DB!
    # OLD WAY: description = Column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text) 
    
    file_path: Mapped[str] = mapped_column(String)
    status: Mapped[VideoStatus] = mapped_column(default=VideoStatus.UPLOADED)
    
    # OLD WAY: owner_id = Column(Integer, ForeignKey("users.id"))
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Note: No 'List[]' here because a video only has ONE owner
    owner: Mapped["User"] = relationship(back_populates="videos")
    comments: Mapped[List["Comment"]] = relationship(back_populates="video")
    reactions: Mapped[List["VideoReaction"]] = relationship(back_populates="video")



class VideoReaction(Base):
    __tablename__ = "video_reactions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # True for like, False for dislike
    is_like: Mapped[bool] = mapped_column()

    # Relationships for easy access to user and video from a reaction
    user: Mapped["User"] = relationship(back_populates="video_reactions")
    video: Mapped["Video"] = relationship(back_populates="reactions")

    __table_args__ = (
        UniqueConstraint('user_id', 'video_id',
        name='unique_user_video_reaction'),
    )


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    content: Mapped[str] = mapped_column(Text)
    
    # Ready for your NLP integration: automatically nullable
    sentiment: Mapped[str | None] = mapped_column(String(50))

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id"))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    author: Mapped["User"] = relationship(back_populates="comments")
    video: Mapped["Video"] = relationship(back_populates="comments")
    reactions: Mapped[List["CommentReaction"]] = relationship(back_populates="comment")



class CommentReaction(Base):
    __tablename__ = "comment_reactions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    comment_id: Mapped[int] = mapped_column(ForeignKey("comments.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # True for like, False for dislike
    is_like: Mapped[bool] = mapped_column()

    # Relationships for easy access to user and comment from a reaction
    user: Mapped["User"] = relationship(back_populates="comment_reactions")
    comment: Mapped["Comment"] = relationship(back_populates="reactions")

    __table_args__ = (
        UniqueConstraint('user_id', 'comment_id',
        name='unique_user_comment_reaction'),
    )

