from fastapi.testclient import TestClient
from main import app


client = TestClient(app)

def test_signup():
    response = client.post("/auth/signup", json={
        "username": "testuser_signup",
        "email": "testuser_signup@example.com",
        "password": "testpassword"
    })
    assert response.status_code == 200

def test_duplicate_signup():
    # First signup
    client.post("/auth/signup", json={
        "username": "testuser_dup",
        "email": "testuser_dup@example.com",
        "password": "testpassword"
    })
    # Try to signup with same email
    response = client.post("/auth/signup", json={
        "username": "testuser_dup2",
        "email": "testuser_dup@example.com",
        "password": "testpassword"
    })
    assert response.status_code == 400

def test_login():
    # Create user first
    client.post("/auth/signup", json={
        "username": "testuser_login",
        "email": "testuser_login@example.com",
        "password": "testpassword"
    })
    # Then login
    response = client.post("/auth/login", json={
        "email": "testuser_login@example.com",
        "password": "testpassword"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_invalid_login():
    response = client.post("/auth/login", json={
        "email": "nonexistent@example.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401


def get_auth_token():
    # First, sign up a user
    client.post("/auth/signup", json={
        "username": "testuser_token",
        "email": "testtoken@example.com",
        "password": "password123"
    })
    # Then, log in to get the auth token
    response = client.post("/auth/login", json={
        "email": "testtoken@example.com",
        "password": "password123"
    })
    return response.json()["access_token"]

def get_auth_token_for(email, username):
    """Get auth token for a specific user"""
    signup_resp = client.post("/auth/signup", json={
        "username": username,
        "email": email,
        "password": "password123"
    })
    if signup_resp.status_code not in [200, 201]:
        raise Exception(f"Signup failed: {signup_resp.status_code} - {signup_resp.json()}")
    
    response = client.post("/auth/login", json={
        "email": email,
        "password": "password123"
    })
    if response.status_code != 200:
        raise Exception(f"Login failed: {response.status_code} - {response.json()}")
    
    return response.json()["access_token"]

def test_get_me_without_token():
    response = client.get("/auth/me")
    assert response.status_code == 401

def test_get_me_with_token():
    token = get_auth_token()
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "testtoken@example.com"