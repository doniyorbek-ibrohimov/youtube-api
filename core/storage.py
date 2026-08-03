import boto3
import json
import uuid
from botocore.exceptions import ClientError
from fastapi import UploadFile, HTTPException
from core.config import settings

class StorageClient:
    def __init__(self):
        # We connect to MinIO using the exact same library (boto3) used for real Amazon S3
        self.s3 = boto3.client(
            's3',
            endpoint_url=settings.MINIO_ENDPOINT,
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
        )
        self.bucket = settings.MINIO_BUCKET_NAME
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        try:
            self.s3.head_bucket(Bucket=self.bucket)
        except ClientError:
            # If the bucket doesn't exist, create it automatically
            self.s3.create_bucket(Bucket=self.bucket)
            
            # Make the bucket public so users can actually watch the videos!
            policy = {
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{self.bucket}/*"]
                }]
            }
            self.s3.put_bucket_policy(Bucket=self.bucket, Policy=json.dumps(policy))

    # def upload_video_to_s3(self, file: UploadFile) -> str:
    #     """Upload video file to S3 and return its public URL"""
    #     # Generate a random, unique filename (e.g., 5f3a-2b1c.mp4)
    #     file_extension = file.filename.split(".")[-1]
    #     unique_filename = f"{uuid.uuid4()}.{file_extension}"
        
    #     try:
    #         self.s3.upload_fileobj(
    #             file.file, 
    #             self.bucket, 
    #             unique_filename,
    #             ExtraArgs={"ContentType": file.content_type}
    #         )
    #         # Return the URL where the frontend can watch the video
    #         return f"{settings.MINIO_ENDPOINT}/{self.bucket}/{unique_filename}"
    #     except Exception as e:
    #         raise HTTPException(status_code=500, detail=f"Failed to upload video: {str(e)}")

    def generate_presigned_upload_url(self, filename: str, content_type: str, user_id: int) -> dict:
        """Generate a presigned URL for direct client upload to MinIO"""
        file_extension = filename.split(".")[-1]
        object_name = f"{user_id}/{uuid.uuid4()}.{file_extension}"
        
        url = self.s3.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': self.bucket,
                'Key': object_name,
                'ContentType': content_type
            },
            ExpiresIn=900  # 15 minutes
        )
        public_url = url.replace(settings.MINIO_ENDPOINT, settings.MINIO_PUBLIC_ENDPOINT)
        return {"upload_url": public_url, "object_name": object_name}


    def get_video_url(self, object_name: str) -> str:
        """Get public URL"""
        # For MinIO
        return f"{settings.MINIO_PUBLIC_ENDPOINT}/{self.bucket}/{object_name}"
        
        # For AWS S3 (when you switch), use this instead:
        # return f"https://{settings.MINIO_BUCKET}.s3.amazonaws.com/{object_name}"

    def get_internal_video_url(self, object_name: str) -> str:
        """Get internal Docker network URL (used for Celery / FFmpeg)"""
        return f"{settings.MINIO_ENDPOINT}/{self.bucket}/{object_name}"

    def delete_video_from_s3(self, object_name: str):
        """Delete video"""
        try:
            self.s3.delete_object(Bucket=self.bucket, Key=object_name)
        except ClientError as e:
            print(f"Delete failed: {e}")

_storage = None

def get_storage():
    global _storage
    if _storage is None:
        _storage = StorageClient()
    return _storage



