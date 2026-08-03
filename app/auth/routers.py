import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from database.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth import crud
from app.auth import schemas
from core.security import create_access_token, get_current_user
from core.config import settings
from database.redis import redis_blacklist as redis_client
from datetime import datetime, timezone

router = APIRouter(prefix="/auth", tags=["auth"])
scheme = HTTPBearer()

@router.post("/signup", response_model=schemas.UserResponse)
async def signup(
    user: schemas.UserCreate,
    db: AsyncSession = Depends(get_db)
):
    existing_user = await crud.get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    new_user = await crud.create_user(db, user)
    await crud.create_channel(db, new_user.id, new_user.username)
    await db.commit()
    return new_user

@router.post("/login")
async def login(credentials: schemas.LoginModel, db: AsyncSession = Depends(get_db)):
    user = await crud.get_user_by_email(db, credentials.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid Credentials")
    if not crud.password_hasher.verify(credentials.password, str(user.hashed_password)):
        raise HTTPException(status_code=401, detail="Invalid Credentials")
    access_token = create_access_token({"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(scheme)
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        exp = payload.get("exp")
        if exp is None:
            raise HTTPException(status_code=400, detail="Invalid token")
        remainder = int(exp - datetime.now(timezone.utc).timestamp())
        if remainder <= 0:
            raise HTTPException(status_code=401, detail="Token expired")
        redis_client.setex(f"blacklist:{token}", remainder, "true")
        return {"message": "Logged out successfully"}
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    

@router.get("/{channel_id}", response_model=schemas.ChannelResponse)
async def get_channel(channel_id: int, db: AsyncSession = Depends(get_db)):
    channel = await crud.get_channel_by_id(db, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    count = await crud.get_subscriber_count(db, channel_id)
    return schemas.ChannelWithStatsResponse(
        **channel.__dict__,
        subscriber_count=count
    )

@router.patch("/me", response_model=schemas.ChannelResponse)
async def update_my_channel(
    data: schemas.ChannelUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    channel = await crud.get_channel_by_user_id(db, current_user.id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    return await crud.update_channel(db, channel.id, data)

@router.post("/{channel_id}/subscribe")
async def subscribe(
    channel_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    channel = await crud.get_channel_by_id(db, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    if channel.owner_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot subscribe to your own channel")
    subscribed = await crud.toggle_subscription(db, current_user.id, channel_id)
    return {"subscribed": subscribed}

@router.get("/{channel_id}/subscribers")
async def get_subscribers(channel_id: int, db: AsyncSession = Depends(get_db)):
    channel = await crud.get_channel_by_id(db, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    count = await crud.get_subscriber_count(db, channel_id)
    return {"channel_id": channel_id, "subscriber_count": count}

@router.get("/{channel_id}/videos")
async def get_videos(channel_id: int, db: AsyncSession = Depends(get_db)):
    videos = await crud.get_channel_videos(db, channel_id)
    return videos