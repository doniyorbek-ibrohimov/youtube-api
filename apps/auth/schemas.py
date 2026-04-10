from pydantic import BaseModel, EmailStr, ConfigDict, Field
from datetime import datetime
from typing import List, Optional


# --- USER SCHEMAS ---
class UserBase(BaseModel):
    username: str = Field(..., max_length=50)
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserResponse(UserBase):
    id: int
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        from_attributes=True
    )

class LoginModel(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)    
    
