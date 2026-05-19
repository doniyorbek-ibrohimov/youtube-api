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

import time
from tasks.video_tasks import generate_thumbnail_task
from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, File
from sqlalchemy.orm import Session
from database.db import get_db
from core.security import get_current_user
from app.auth import crud as auth_crud, schemas as auth_schemas
from app.content import crud, schemas
from app.logging_config import logger
from core.storage import storage




router = APIRouter(prefix="/videos", tags=["videos"])




@router.post("/videos/upload", response_model=schemas.VideoResponseModel)
async def upload_video(
    title: str = Form(...),
    description: str = Form(None),
    file: UploadFile = File(...),
    current_user: auth_schemas.UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    start_time = time.time()
    user = auth_crud.get_user_by_id(db, current_user.id)
    if not user or not user.channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    logger.info("video_upload_started", extra={"user_id": user.id, "title": title})

    try:
        # Upload video to MinIO
        file_path = storage.upload_video_to_s3(file)
        logger.info("video_uploaded_to_storage", extra={"user_id": user.id, "file_path": file_path})
        
        # Save to database
        video_data = schemas.VideoCreateModel(title=title, description=description)
        video = crud.create_video(db, video_data, user.channel.id, file_path)
        
        # Queue thumbnail
        generate_thumbnail_task.delay(video.id, file_path, user.channel.id)
        
        duration = time.time() - start_time
        logger.info("video_uploaded_successfully", extra={
            "user_id": user.id, 
            "video_id": video.id,
            "duration_seconds": round(duration, 2)
        })
        return video
    
    except Exception as e:
        logger.error("video_upload_failed", extra={
            "user_id": user.id,
            "title": title,
            "error": str(e)
        }, exc_info=True)
        raise HTTPException(status_code=500, detail="Video upload failed")


@router.post("/comments/{comment_id}/replies", response_model=schemas.CommentResponseModel)
async def create_reply_to_comment(
    comment: schemas.CommentCreateModel,
    comment_id: int,
    current_user: auth_schemas.UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    channel = auth_crud.get_channel_by_user_id(db, current_user.id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    parent_comment = crud.get_comment(db, comment_id=comment_id)
    if not parent_comment:
        raise HTTPException(status_code=404, detail="Comment not found")


    db_comment = crud.create_comment(
        db,
        comment,
        channel_id=channel.id,
        video_id = parent_comment.video_id,
        parent_id=comment_id
    )

    return db_comment




