import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from database.db import Base, get_db
from main import app

# In-memory test database with StaticPool for proper connection sharing
SQLALCHEMY_TEST_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_TEST_URL,
    connect_args={"check_same_thread": False}, 
    poolclass=StaticPool  # Ensures all connections use the same in-memory database
)
TestingSessionLocal = sessionmaker(bind=engine)

@pytest.fixture(autouse=True)
def reset_db():
    """Drop and recreate tables before each test"""
    # Drop all tables first
    Base.metadata.drop_all(bind=engine)
    # Create fresh tables
    Base.metadata.create_all(bind=engine)
    yield
    # Cleanup after test
    Base.metadata.drop_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def client():
    return TestClient(app)