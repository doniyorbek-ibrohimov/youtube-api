import requests
import os

BASE_URL = "http://localhost:8000"
TEST_VIDEO_PATH = "test_video.mp4"  # we'll create a fake one

# ─────────────────────────────────────────
# STEP 0: Create a fake video file to upload
# ─────────────────────────────────────────
with open(TEST_VIDEO_PATH, "wb") as f:
    f.write(b"fake video content for testing")
print("✓ Created fake test video")


# ─────────────────────────────────────────
# STEP 1: Register + Login to get a token
# ─────────────────────────────────────────
signup = requests.post(f"{BASE_URL}/auth/signup", json={
    "username": "presign_tester",
    "email": "presign@test.com",
    "password": "password123"
})
# 400 just means user already exists from a previous run — that's fine
print(f"Signup: {signup.status_code}")

login = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "presign@test.com",
    "password": "password123"
})
assert login.status_code == 200, f"Login failed: {login.text}"
token = login.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("✓ Logged in, got token")


# ─────────────────────────────────────────
# STEP 2: Request a presigned upload URL
# ─────────────────────────────────────────
request_upload = requests.post(
    f"{BASE_URL}/videos/request-upload",
    data={
        "filename": "test_video.mp4",
        "content_type": "video/mp4"
    },
    headers=headers
)
assert request_upload.status_code == 200, f"Request upload failed: {request_upload.text}"
upload_url = request_upload.json()["upload_url"]
object_name = request_upload.json()["object_name"]
print(f"✓ Got presigned URL")
print(f"  object_name: {object_name}")


# ─────────────────────────────────────────
# STEP 3: Upload directly to MinIO
# (FastAPI is NOT involved in this request)
# ─────────────────────────────────────────
with open(TEST_VIDEO_PATH, "rb") as f:
    minio_upload = requests.put(
        upload_url,
        data=f,
        headers={"Content-Type": "video/mp4"}
    )
assert minio_upload.status_code in [200, 204], f"MinIO upload failed: {minio_upload.status_code} {minio_upload.text}"
print(f"✓ Uploaded directly to MinIO (FastAPI never touched the bytes)")


# ─────────────────────────────────────────
# STEP 4: Confirm upload — saves to DB + triggers Celery
# ─────────────────────────────────────────
confirm = requests.post(
    f"{BASE_URL}/videos/confirm-upload",
    data={
        "title": "My Test Video",
        "description": "Testing presigned upload flow",
        "object_name": object_name
    },
    headers=headers
)
assert confirm.status_code == 200, f"Confirm failed: {confirm.text}"
video = confirm.json()
print(f"✓ Video saved to DB")
print(f"  video_id: {video['id']}")
print(f"  video_url: {video['video_url']}")
print(f"  thumbnail_url: {video.get('thumbnail_url')} (None until Celery runs)")


# ─────────────────────────────────────────
# CLEANUP
# ─────────────────────────────────────────
os.remove(TEST_VIDEO_PATH)
print("\n✓ All steps passed — presigned upload flow works correctly")