import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from database.db import get_db
from sqlalchemy.orm import Session
from app.auth.crud import create_user, create_channel, get_user_by_email, password_hasher
from app.auth.schemas import UserCreate, UserResponse, LoginModel
from core.security import create_access_token, get_current_user
from core.config import settings
from database.redis import redis_client
from datetime import datetime, timezone




router = APIRouter(prefix="/auth", tags=["auth"])
scheme = HTTPBearer()

@router.post("/signup", response_model=UserResponse)
async def signup(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    
    existing_user = get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    new_user = create_user(db, user)
    create_channel(db, new_user.id, new_user.username)  # Create a channel for the new user
    db.commit()
    return new_user


@router.post("/login")
async def login(credentials: LoginModel, db: Session = Depends(get_db)):
    user = get_user_by_email(db, credentials.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid Credentials")
    if not password_hasher.verify(credentials.password, str(user.hashed_password)):
        raise HTTPException(status_code=401, detail="Invalid Credentials")
    access_token = create_access_token({"sub": str(user.id)}) 
    return {"access_token": access_token, "token_type": "bearer"}



@router.post("/logout")
async def logout(
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