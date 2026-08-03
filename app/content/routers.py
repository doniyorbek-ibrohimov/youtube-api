# import os
# import shutil
# import uuid
# from fastapi import (APIRouter, Depends, HTTPException,
#                      Header, UploadFile, File,
#                      Form, Request, status
#                      )
# from sqlalchemy.orm import Session

# from database import get_db
# from core.security import get_current_user
# from app.auth.schemas import UserResponse 
# from app.content import crud, schemas
# from app.auth import crud as auth_crud


# CHUNK_SIZE = 1024 * 1024  # 1MB
# MAX_VIDEO_SIZE_MB = 50
# MAX_VIDEO_SIZE_BYTES = MAX_VIDEO_SIZE_MB * 1024 * 1024 

# # Create a directory to store the videos if it doesn't exist
# UPLOAD_DIR = "static/videos"
# os.makedirs(UPLOAD_DIR, exist_ok=True)

# @router.post("/upload")
# async def upload_video(
#     # 1. Receive text data as Form fields
#     title: str = Form(...),
#     description: str = Form(None), 
    
#     # 2. Receive the file
#     file: UploadFile = File(...),
    
#     # 3. Security and Database connections
#     current_user: UserResponse = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     # Step A: Validate the file type
#     if not file.content_type or not file.content_type.startswith("video/"):
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must be a video format")

#     # Step B: Generate a unique filename
#     # If two users upload "my_vacation.mp4", we don't want them to overwrite each other.
#     if not file.filename:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must have a name")
    
#     file_extension = file.filename.split(".")[-1]
#     unique_filename = f"{uuid.uuid4()}.{file_extension}"
#     file_path = os.path.join(UPLOAD_DIR, unique_filename)

#     bytes_written = 0
#     # Step C: Save the file to the disk efficiently
#     try:
#         with open(file_path, "wb") as buffer:
#             while True:
#                 # Read the file in chunks to avoid loading the entire file into memory
#                 chunk = file.file.read(CHUNK_SIZE)

#                 # the file is alredy fully read if no chunk
#                 if not chunk:
#                     break

#                 bytes_written += len(chunk)
#                 if bytes_written > MAX_VIDEO_SIZE_BYTES:
#                     raise HTTPException(
#                         status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, 
#                         detail=f"Video exceeds the {MAX_VIDEO_SIZE_MB}MB limit."
#                     )
                
#                 buffer.write(chunk)


#     except Exception as e:
#         # If there's an error during file saving, we should clean up any partially saved file
#         if os.path.exists(file_path):
#             os.remove(file_path)
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save video")
#     finally:
#         # Always close the uploaded file to free up memory
#         file.file.close()

#     # Step D: Save the database record
#     user = auth_crud.get_user_by_id(db, user_id=current_user.id)
#     video_data = schemas.VideoCreateModel(title=title, description=description)
#     db_video = crud.create_video(db=db, video=video_data, channel_id=user.channel.id, file_path=file_path) # type: ignore

#     return {"message": "Video uploaded successfully", "video_id": db_video.id}

# @router.get("/{video_id}/stream")
# def stream_video(
#     video_id: int,
#     request: Request,
#     # Fastapi automatically extracts the "Range" header from the request
#     range: str = Header(None),
#     db: Session = Depends(get_db)
#     ):
#     video = crud.get_video(db, video_id=video_id)
#     if not video or not os.path.exists(video.file_path):
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    
#     file_size = os.path.getsize(video.file_path)

#     # Parse the Range header e.g "Range: bytes=0-"
#     if range is None:
#         # If no Range header, serve the entire file
#         start = 0
#         end = min(CHUNK_SIZE - 1, file_size - 1)
#     else:
#         # Clean the string and split it
#         ranges = range.replace("bytes=", "").split("-")
#         start = int(ranges[0]) if ranges[0] else 0

#         # If the end is not specified, we specife a chunk size
#         end = int(ranges[1]) if len(ranges) > 1 and ranges[1] else min(start + CHUNK_SIZE - 1, file_size - 1)

#     # Security check: don't let 'end' go past the actual file size
#     end = min(end, file_size - 1)
#     if start > end or start < 0 or end >= file_size:
#         raise HTTPException(status_code=status.HTTP_416_RANGE_NOT_SATISFIABLE, detail="Requested Range Not Satisfiable")
#     content_length = (end - start) + 1

#     def file_iterator():
#         with open(video.file_path, "rb") as video_file:
#             video_file.seek(start)
#             bytes_read = 0
#             while bytes_read < content_length:
#                 chunk = video_file.read(min(CHUNK_SIZE, content_length - bytes_read))
#                 if not chunk:
#                     break
#                 bytes_read += len(chunk)
#                 yield chunk


# The code above is for storing locally, and just a leaning example


from tasks.video_tasks import generate_thumbnail_task
from fastapi import APIRouter, Depends, HTTPException, Form, Query 
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from database.db import get_db
from core.security import get_current_user
from app.auth import crud as auth_crud, schemas as auth_schemas
from app.content import crud, schemas
from app.logging_config import logger
from core.storage import get_storage

router = APIRouter(prefix="/videos", tags=["videos"])


# ==========================================
# PAGINATED READ ENDPOINTS
# ==========================================

@router.get("", response_model=schemas.CursorPage[schemas.VideoResponseModel])
@router.get("/", response_model=schemas.CursorPage[schemas.VideoResponseModel])
async def list_videos(
    cursor: str | None = Query(None, description="Base64 encoded pagination cursor"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    videos, next_cursor, has_more = await crud.get_videos(db, cursor=cursor, limit=limit)
    return schemas.CursorPage(
        items=videos,
        next_cursor=next_cursor,
        has_more=has_more
    )


@router.get("/{video_id}/comments", response_model=schemas.CursorPage[schemas.CommentResponseModel])
async def list_video_comments(
    video_id: int,
    cursor: str | None = Query(None, description="Base64 encoded pagination cursor"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    comments, next_cursor, has_more = await crud.get_comments_for_video(
        db, video_id=video_id, cursor=cursor, limit=limit
    )
    return schemas.CursorPage(
        items=comments,
        next_cursor=next_cursor,
        has_more=has_more
    )


# ==========================================
# WRITE / MUTATION ENDPOINTS
# ==========================================

@router.post("/request-upload")
async def request_upload(
    filename: str = Form(...),
    content_type: str = Form(...),
    current_user: auth_schemas.UserResponse = Depends(get_current_user),
):
    storage = get_storage()
    if not content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="File must be a video")

    result = storage.generate_presigned_upload_url(
        filename=filename,
        content_type=content_type,
        user_id=current_user.id
    )
    return result


@router.post("/confirm-upload", response_model=schemas.VideoResponseModel)
async def confirm_upload(
    title: str = Form(...),
    description: str = Form(None),
    object_name: str = Form(...),
    current_user: auth_schemas.UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    storage = get_storage()
    user = await auth_crud.get_user_with_channel(db, current_user.id)
    if not user or not user.channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    video_data = schemas.VideoCreateModel(title=title, description=description)
    video_url = storage.get_video_url(object_name)

    # 1. Primary check (handles 99% of standard sequential duplicates)
    existing_video = await crud.get_video_by_url(db, video_url)
    if existing_video:
        return existing_video

    try:
        # 2. Attempt the creation
        video = await crud.create_video(db, video_data, user.channel.id, video_url)
        await db.commit()
        
        # Only trigger Celery if the DB commit succeeds
        generate_thumbnail_task.delay(video.id, object_name, user.channel.id)
        return video

    except IntegrityError:
        # 3. Race condition safety net (handles simultaneous rapid requests)
        await db.rollback()
        
        # Fetch the record that was just inserted by the competing concurrent request
        existing_video = await crud.get_video_by_url(db, video_url)
        if existing_video:
            return existing_video
            
        raise HTTPException(status_code=400, detail="Database integrity conflict")


@router.post("/comments/{comment_id}/replies", response_model=schemas.CommentResponseModel)
async def create_reply_to_comment(
    comment: schemas.CommentCreateModel,
    comment_id: int,
    current_user: auth_schemas.UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    channel = await auth_crud.get_channel_by_user_id(db, current_user.id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    parent_comment = await crud.get_comment(db, comment_id=comment_id)
    if not parent_comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    db_comment = await crud.create_comment(
        db,
        comment,
        channel_id=channel.id,
        video_id=parent_comment.video_id,
        parent_comment_id=comment_id
    )
    return db_comment