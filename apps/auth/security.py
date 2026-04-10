import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_db
from apps.auth.crud import get_user_by_id
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from config import settings

load_dotenv()

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
EXPITE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

scheme = HTTPBearer()

def create_access_token(data: dict):
    # Use timezone-aware UTC for 2026 standards
    expire = datetime.now(timezone.utc) + timedelta(minutes=EXPITE_MINUTES)
    payload = data.copy()
    payload.update({"exp": expire})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(scheme),
    db: Session = Depends(get_db)
):
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = get_user_by_id(db, int(user_id))
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user

    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        # Generic 401 for any token failure
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )