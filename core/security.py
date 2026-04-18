import redis
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.crud import get_user_by_id
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from config import settings

load_dotenv()

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
EXPITE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
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
    # Check if token is blacklisted
    if redis_client.exists(f"blacklist:{token.credentials}"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked. Please log in again."
        )

    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        
        user = get_user_by_id(db, int(user_id))
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        
        return user

    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        # Generic 401 for any token failure
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def logout(credentials: HTTPAuthorizationCredentials = Depends(scheme)):
    token = credentials.credentials
    
    try:
        # Decode to find out when this token was supposed to die
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp = payload.get("exp")
        
        if exp is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token structure")
        # Calculate remaining seconds
        remainder = int(exp - datetime.now(timezone.utc).timestamp())
        
        if remainder > 0:
            # Put it in the blacklist until it naturally expires
            redis_client.setex(f"blacklist:{token}", remainder, "true")
            
        return {"message": "Logged out successfully"}
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
