from database import Base
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone

class VideoReaction(Base):
    __tablename__ = "video_reactions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    # True for like, False for dislike
    is_like: Mapped[bool] = mapped_column()

    # Relationships for easy access to user and video from a reaction
    user: Mapped["User"] = relationship(back_populates="video_reactions")
    video: Mapped["Video"] = relationship(back_populates="reactions")

    __table_args__ = (
        UniqueConstraint('user_id', 'video_id',
        name='unique_user_video_reaction'),
    )


class CommentReaction(Base):
    __tablename__ = "comment_reactions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    comment_id: Mapped[int] = mapped_column(ForeignKey("comments.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    # True for like, False for dislike
    is_like: Mapped[bool] = mapped_column()

    # Relationships for easy access to user and comment from a reaction
    user: Mapped["User"] = relationship(back_populates="comment_reactions")
    comment: Mapped["Comment"] = relationship(back_populates="reactions")

    __table_args__ = (
        UniqueConstraint('user_id', 'comment_id',
        name='unique_user_comment_reaction'),
    )



class WatchHistory(Base):
    __tablename__ = "watch_history"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # History belongs to the private USER, not the public Channel
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"))

    user: Mapped["User"] = relationship(back_populates="watch_history")
    video: Mapped["Video"] = relationship() # We don't back-populate to Video to save RAM


    # The AI Tracking Data
    last_watched_at: Mapped[datetime] = mapped_column(default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    watch_time_seconds: Mapped[int] = mapped_column(default=0)
    is_completed: Mapped[bool] = mapped_column(default=False)

    # THE SHIELD: Prevent duplicate rows for the same user/video combo
    __table_args__ = (
        UniqueConstraint('user_id', 'video_id', name='unique_user_video_history'),
    )


