from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class VideoCreateModel(BaseModel):
    title: str 
    description: Optional[str] = None


class VideoResponseModel(BaseModel):
    id: int
    title: str
    description: Optional[str]
    owner_id: int
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


# --- Comment Schemas ---
class CommentCreateModel(BaseModel):
    content: str

class CommentResponseModel(BaseModel):
    id: int
    content: str
    sentiment: Optional[str] = None
    video_id: int
    owner_id: int
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )