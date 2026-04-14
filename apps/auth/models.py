
from typing import List

from sqlalchemy import Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base
from datetime import datetime, timezone



# -------------------------------------------------------------------
# 1. ASSOCIATION TABLE (For the Many-to-Many Subscription System)
# -------------------------------------------------------------------
subscriptions_table = Table(
    'subscriptions',
    Base.metadata,
    Column('subscriber_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('creator_id', Integer, ForeignKey('users.id'), primary_key=True)
)

# -------------------------------------------------------------------
# 2. CORE MODELS
# -------------------------------------------------------------------


class User(Base):
    __tablename__ = "users"

    # OLD WAY: id = Column(Integer, primary_key=True, index=True)
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now(timezone.utc))

    # OLD WAY: videos = relationship("Video", back_populates="owner")
    videos: Mapped[List["Video"]] = relationship(back_populates="owner")
    comments: Mapped[List["Comment"]] = relationship(back_populates="author")
    video_reactions: Mapped[List["VideoReaction"]] = relationship(back_populates="user")
    comment_reactions: Mapped[List["CommentReaction"]] = relationship(back_populates="user")


    following: Mapped[List["User"]] = relationship(
        secondary=subscriptions_table,
        primaryjoin=id==subscriptions_table.c.subscriber_id,
        secondaryjoin=id==subscriptions_table.c.creator_id,
        back_populates="followers"
    )

    followers: Mapped[List["User"]] = relationship(
        secondary=subscriptions_table,
        primaryjoin=id==subscriptions_table.c.creator_id,
        secondaryjoin=id==subscriptions_table.c.subscriber_id,
        back_populates="following"
    )

    