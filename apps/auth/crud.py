from apps.auth.models import User
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
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="User with this email or username already exists")


