
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from packages.voice_profiles.db.database import get_db
from packages.voice_profiles.db.models import Base
from apps.api.main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

def test_create_voice_profile(db_session):
    with open("tests/fixtures/test.wav", "rb") as f:
        response = client.post(
            "/voice-profiles/",
            data={"name": "test_profile", "description": "A test profile"},
            files={"file": ("test.wav", f, "audio/wav")},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "test_profile"
    assert data["description"] == "A test profile"
    assert "id" in data

def test_read_voice_profiles(db_session):
    # Create a profile first
    with open("tests/fixtures/test.wav", "rb") as f:
        client.post(
            "/voice-profiles/",
            data={"name": "test_profile", "description": "A test profile"},
            files={"file": ("test.wav", f, "audio/wav")},
        )

    response = client.get("/voice-profiles/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "test_profile"

def test_read_voice_profile(db_session):
    # Create a profile first
    with open("tests/fixtures/test.wav", "rb") as f:
        create_response = client.post(
            "/voice-profiles/",
            data={"name": "test_profile", "description": "A test profile"},
            files={"file": ("test.wav", f, "audio/wav")},
        )
    profile_id = create_response.json()["id"]

    response = client.get(f"/voice-profiles/{profile_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "test_profile"
    assert data["id"] == profile_id

def test_delete_voice_profile(db_session):
    # Create a profile first
    with open("tests/fixtures/test.wav", "rb") as f:
        create_response = client.post(
            "/voice-profiles/",
            data={"name": "test_profile", "description": "A test profile"},
            files={"file": ("test.wav", f, "audio/wav")},
        )
    profile_id = create_response.json()["id"]

    # Delete the profile
    delete_response = client.delete(f"/voice-profiles/{profile_id}")
    assert delete_response.status_code == 200
    assert delete_response.json() == {"message": "Voice profile deleted successfully"}

    # Verify it's gone
    get_response = client.get(f"/voice-profiles/{profile_id}")
    assert get_response.status_code == 404
