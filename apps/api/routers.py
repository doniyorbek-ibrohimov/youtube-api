import os
import shutil
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from database import get_db
from apps.auth.security import get_current_user
from apps.auth.schemas import UserResponse 
from apps.api import crud, schemas 

router = APIRouter(prefix="/videos", tags=["videos"])

# Create a directory to store the videos if it doesn't exist
UPLOAD_DIR = "static/videos"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_video(
    # 1. Receive text data as Form fields
    title: str = Form(...),
    description: str = Form(None), 
    
    # 2. Receive the file
    file: UploadFile = File(...),
    
    # 3. Security and Database connections
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Step A: Validate the file type
    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="File must be a video format")

    # Step B: Generate a unique filename
    # If two users upload "my_vacation.mp4", we don't want them to overwrite each other.
    if not file.filename:
        raise HTTPException(status_code=400, detail="File must have a name")
    
    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    # Step C: Save the file to the disk efficiently
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Could not save file")
    finally:
        # Always close the uploaded file to free up memory
        file.file.close()

    # Step D: Save the database record
    video_data = schemas.VideoCreateModel(title=title, description=description)
    db_video = crud.create_video(db=db, video=video_data, owner_id=current_user.id, file_path=file_path)

    return {"message": "Video uploaded successfully", "video_id": db_video.id}