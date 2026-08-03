from sqlalchemy import func
from app.auth.models import User, Channel, subscriptions_table
from app.auth.schemas import ChannelUpdate
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

async def get_user_by_email(db: AsyncSession, email: str):
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def get_user_by_id(db: AsyncSession, user_id: int):
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

password_hasher = PasswordHash.recommended()

async def create_user(db: AsyncSession, user):
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=password_hasher.hash(user.password)
    )
    try:
        db.add(db_user)
        await db.flush()
        return db_user
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="User with this email or username already exists")

async def create_channel(db: AsyncSession, user_id: int, username: str):
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    channel = Channel(
        name=username,
        owner_id=user_id
    )
    try:
        db.add(channel)
        await db.flush()
        return channel
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Channel with this name already exists")

async def get_channel_by_user_id(db: AsyncSession, user_id: int):
    stmt = select(Channel).where(Channel.owner_id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def get_user_with_channel(db: AsyncSession, user_id: int):
    stmt = select(User).options(selectinload(User.channel)).where(User.id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_channel_by_id(db: AsyncSession, channel_id: int):
    stmt = select(Channel).where(Channel.id == channel_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def update_channel(db: AsyncSession, channel_id: int, data: ChannelUpdate):
    channel = await get_channel_by_id(db, channel_id)
    if not channel:
        return None
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(channel, field, value)
    await db.commit()
    await db.refresh(channel)
    return channel



async def get_channel_videos(db: AsyncSession, channel_id: int):
    stmt = select(Channel).options(selectinload(Channel.videos)).where(Channel.id == channel_id)
    from sqlalchemy.dialects import postgresql
    print(stmt.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))
    
    result = await db.execute(stmt)
    channel = result.scalar_one_or_none()
    if channel:
        return channel.videos
    return []

async def get_subscriber_count(db: AsyncSession, channel_id: int) -> int:
    stmt = select(func.count()).select_from(subscriptions_table).where(subscriptions_table.c.channel_id == channel_id)
    result = await db.execute(stmt)
    return result.scalar()

async def toggle_subscription(db: AsyncSession, subscriber_id: int, channel_id: int) -> bool:
    """Returns True if subscribed, False if unsubscribed"""
    check = await db.execute(
        subscriptions_table.select().where(
            subscriptions_table.c.subscriber_id == subscriber_id,
            subscriptions_table.c.channel_id == channel_id
        )
    )
    existing = check.fetchone()
    if existing:
        await db.execute(
            subscriptions_table.delete().where(
                subscriptions_table.c.subscriber_id == subscriber_id,
                subscriptions_table.c.channel_id == channel_id
            )
        )
        await db.commit()
        return False
    else:
        await db.execute(
            subscriptions_table.insert().values(
                subscriber_id=subscriber_id,
                channel_id=channel_id
            )
        )
        await db.commit()
        return True
    
