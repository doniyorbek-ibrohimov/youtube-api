from datetime import datetime, timezone
from typing import List
import enum

from sqlalchemy import Column, ForeignKey, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base




playlist_video = Table(
    "playlist_video",
    Base.metadata,
    Column("playlist_id", ForeignKey("playlists.id", ondelete="CASCADE"), primary_key=True),
    Column("video_id", ForeignKey("videos.id", ondelete="CASCADE"), primary_key=True)
)


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
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(default=datetime.now(timezone.utc))

    # Note: No 'List[]' here because a video only has ONE owner
    channel: Mapped["Channel"] = relationship(back_populates="videos")
    comments: Mapped[List["Comment"]] = relationship(back_populates="video")
    reactions: Mapped[List["VideoReaction"]] = relationship(back_populates="video")
    playslists: Mapped[List["Playlist"]] = relationship(
        secondary=playlist_video,
        back_populates="videos" 
    )

class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    content: Mapped[str] = mapped_column(Text)
    
    # Ready for your NLP integration: automatically nullable
    sentiment: Mapped[str | None] = mapped_column(String(50))

    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id", ondelete="CASCADE"))
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"))

    # this allows for nested comments (replies to comments)
    parent_comment_id: Mapped[int | None] = mapped_column(ForeignKey("comments.id", ondelete="CASCADE"))

    created_at: Mapped[datetime] = mapped_column(default=datetime.now(timezone.utc))

    channel: Mapped["Channel"] = relationship(back_populates="comments")
    video: Mapped["Video"] = relationship(back_populates="comments")
    reactions: Mapped[List["CommentReaction"]] = relationship(back_populates="comment")

    # Self-referential relationship for nested comments
    parent_comment: Mapped["Comment | None"] = relationship(
        "Comment",       
        remote_side=[id], # tells SQLAlchemy that the 'id' is the top of the tree
        back_populates="replies"
    )
    replies: Mapped[List["Comment"]] = relationship(
        "Comment",
        back_populates="parent_comment",
        cascade="all, delete-orphan"
    )


class Playlist(Base):
    __tablename__ = "playlists"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    is_private: Mapped[bool] = mapped_column(default=False)

    # A playlist is owned by a Channel
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id", ondelete="CASCADE"))
    channel: Mapped["Channel"] = relationship(back_populates="playlists")

    # The Many-to-Many link to Videos
    videos: Mapped[List["Video"]] = relationship(
        secondary=playlist_video, 
        back_populates="playlists"
    )





