from app.auth.models import User, Channel
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException


def get_user_by_email(db: Session, email: str):
    stmt = select(User).where(User.email == email)

    # scalar_one_or_none() - either returns the single result or None if no results, raises an error if multiple results
    return db.execute(stmt).scalar_one_or_none()

def get_user_by_id(db: Session, user_id: int):
    stmt = select(User).where(User.id == user_id)

    # scalar_one_or_none() - either returns the single result or None if no results, raises an error if multiple results
    return db.execute(stmt).scalar_one_or_none() 


password_hasher = PasswordHash.recommended()

def create_user(db: Session, user):

    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=password_hasher.hash(user.password)
    )
    try:
        db.add(db_user)
        db.flush()  # Flush gets the ID of the new user without committing
        db.refresh(db_user)
        return db_user
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="User with this email or username already exists")

def create_channel(db: Session, user_id: int, username: str):
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    channel = Channel(
        name=username,
        owner_id=user_id
    )
    try:
        db.add(channel)
        db.flush()
        db.refresh(channel)
        return channel
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Channel with this name already exists")
    


def get_channel_by_user_id(db: Session, user_id: int):
    stmt = select(Channel).where(Channel.owner_id == user_id)
    return db.execute(stmt).scalar_one_or_none()
