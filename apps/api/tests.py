import io
from fastapi.testclient import TestClient
from main import app
from apps.auth.tests import get_auth_token, get_auth_token_for

client = TestClient(app)

def test_upload_video_with_token():
    token = get_auth_token()
    # Create a fake video file for testing
    video_file = io.BytesIO(b"fake video content")

    response = client.post(
        "/api/videos/",
        files={"file": ("test.mp4", video_file, "video/mp4")},
        headers={"Authorization": f"Bearer {token}"},
        data={"title": "Test Video", "description": "Test"}
        )
    assert response.status_code == 200
    assert response.json()["title"] == "Test Video"

def test_upload_video_without_token():
    # Create a fake video file for testing
    video_file = io.BytesIO(b"fake video content")

    response = client.post(
        "/api/videos/",
        files={"file": ("test.mp4", video_file, "video/mp4")},
        data={"title": "Test Video", "description": "This is a test video."}
        )
    assert response.status_code == 401

def test_delete_other_users_video():
    token = get_auth_token_for("user1@example.com", "user1")
    # Create a fake video file for testing
    video_file = io.BytesIO(b"fake video content")

    # Upload a video to get its ID
    upload_response = client.post(
        "/api/videos/",
        files={"file": ("test.mp4", video_file, "video/mp4")},
        headers={"Authorization": f"Bearer {token}"},
        data={"title": "Test Video", "description": "Test"}
        )
    video_id = upload_response.json()["id"]

    # Attempt to delete the video with a different token (simulating another user)
    other_token = get_auth_token_for("user2@example.com", "user2")
    delete_response = client.delete(
        f"/api/videos/{video_id}",
        headers={"Authorization": f"Bearer {other_token}"}
        )
    assert delete_response.status_code == 403