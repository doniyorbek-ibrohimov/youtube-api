from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from database import get_db
from sqlalchemy.orm import Session
from app.auth.crud import create_user, create_channel, get_user_by_email, password_hasher
from app.auth.schemas import UserCreate, UserResponse, LoginModel
from core.security import create_access_token, get_current_user
from app.auth.tasks import send_welcome_email


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=UserResponse)
async def signup(
    user: UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    
    existing_user = get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    new_user = create_user(db, user)
    create_channel(db, new_user.id, new_user.username)  # Create a channel for the new user
    db.commit()
    send_welcome_email(background_tasks, email=user.email)
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


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: UserResponse = Depends(get_current_user)):
    return current_user

