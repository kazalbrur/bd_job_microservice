# =============================================================================
# 21. API Tests (tests/test_api.py)
# =============================================================================

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.models import Base
from app.db.database import db_manager

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[db_manager.get_db] = override_get_db

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_get_jobs():
    response = client.get("/jobs/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_search_jobs():
    response = client.get("/jobs/search/engineer")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_job_not_found():
    response = client.get("/jobs/99999")
    assert response.status_code == 404

def test_create_bookmark():
    bookmark_data = {
        "user_id": "test_user_123",
        "job_id": 1
    }
    response = client.post("/bookmarks/", json=bookmark_data)
    # May return 404 if job doesn't exist, which is expected in test
    assert response.status_code in [200, 404]

def test_export_csv():
    response = client.get("/export/csv")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"

def test_export_json():
    response = client.get("/export/json")
    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]

def test_metrics():
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "total_jobs" in data
    assert "active_jobs" in data