import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import engine
from app.models import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_main.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)



def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_get_projects_empty():
    response = client.get("/api/v1/projects/")
    assert response.status_code == 200
    assert response.json() == []

def test_get_targets_empty():
    response = client.get("/api/v1/targets/")
    assert response.status_code == 200
    assert response.json() == []

def test_dashboard():
    response = client.get("/api/v1/dashboard/")
    assert response.status_code == 200
    data = response.json()
    assert "stats" in data
    assert data["stats"]["active_campaigns"] == 0
