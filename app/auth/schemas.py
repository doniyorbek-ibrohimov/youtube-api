from pydantic import BaseModel, EmailStr, ConfigDict, Field
from datetime import datetime


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
    
# --- Channel Schemas ---
class ChannelResponse(BaseModel):
    id: int
    name: str
    description: str | None
    avatar_url: str | None
    owner_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ChannelWithStatsResponse(ChannelResponse):
    subscriber_count: int

class ChannelUpdate(BaseModel):
    name: str | None = Field(None, max_length=100)
    description: str | None = Field(None, max_length=500)
    avatar_url: str | None = None


