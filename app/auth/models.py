from typing import List

from sqlalchemy import Column, Integer, String, Table, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.db import Base
from datetime import datetime, timezone


# -------------------------------------------------------------------
# 1. ASSOCIATION TABLE
# -------------------------------------------------------------------
subscriptions_table = Table(
    'subscriptions',
    Base.metadata,
    Column('subscriber_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('channel_id', Integer, ForeignKey('channels.id'), primary_key=True)  # changed
)

# -------------------------------------------------------------------
# 2. CHANNEL MODEL
# One-to-one with User. This is the public face of the account.
# Created automatically when a user registers.
# -------------------------------------------------------------------
class Channel(Base):
    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    description: Mapped[str | None] = mapped_column(String(500))
    avatar_url: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(default=datetime.now(timezone.utc))

    # The private user who owns this channel
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    owner: Mapped["User"] = relationship(back_populates="channel")

    # Everything public now hangs off Channel, not User
    videos: Mapped[List["Video"]] = relationship(back_populates="channel")
    comments: Mapped[List["Comment"]] = relationship(back_populates="channel")
    playlists: Mapped[List["Playlist"]] = relationship(back_populates="channel")

    # People who subscribed to this channel
    subscribers: Mapped[List["User"]] = relationship(
        secondary=subscriptions_table,
        back_populates="subscriptions"
    )


# -------------------------------------------------------------------
# 3. USER MODEL
# Stripped down — only private/auth data lives here now.
# -------------------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now(timezone.utc))

    # One user owns exactly one channel
    channel: Mapped["Channel"] = relationship(back_populates="owner", uselist=False)

    # Reactions stay on User — they're private actions, not public ones
    video_reactions: Mapped[List["VideoReaction"]] = relationship(back_populates="user")
    comment_reactions: Mapped[List["CommentReaction"]] = relationship(back_populates="user")
    watch_history: Mapped[List["WatchHistory"]] = relationship(back_populates="user")

    # Channels this user subscribes to
    subscriptions: Mapped[List["Channel"]] = relationship(
        secondary=subscriptions_table,
        back_populates="subscribers"
    )

