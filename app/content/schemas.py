from pydantic import BaseModel, ConfigDict
from typing import Generic, Optional, TypeVar
from datetime import datetime



# Create a generic type variable
T = TypeVar("T")

class CursorPage(BaseModel, Generic[T]):
    items: list[T]
    next_cursor: str | None = None
    has_more: bool = False

class VideoCreateModel(BaseModel):
    title: str 
    description: Optional[str] = None


class VideoResponseModel(BaseModel):
    id: int
    title: str
    description: Optional[str]
    video_url: str
    thumbnail_url: str | None
    channel_id: int
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
    channel_id: int

    # we default to an empty list so that frontetnd doesn't get null
    replies: list['CommentResponseModel'] = []   # Recursive relationship
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )