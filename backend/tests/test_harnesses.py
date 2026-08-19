"""
Tests for Phase 5: Harness Studio API and Engine.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import get_db
from app.models import Project, Target, Base

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_harnesses.db"
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
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    p = Project(name="Test SumatraPDF Project", description="Test")
    db.add(p)
    db.commit()
    t = Target(project_id=p.id, name="ParseDocumentHeader", module="SumatraPDF", status="VERIFIED")
    db.add(t)
    db.commit()
    db.close()
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)

def test_generate_harness():
    res = client.post(
        "/api/v1/projects/1/targets/1/harness",
        json={
            "input_type": "file",
            "init_code": "init_lib();",
            "cleanup_code": "cleanup_lib();"
        }
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["name"] == "ParseDocumentHeader_file"
    assert data["status"] == "CREATED"
    assert "harness.cpp" in data["files"]
    assert "init_lib();" in data["files"]["harness.cpp"]
    assert "cleanup_lib();" in data["files"]["harness.cpp"]
    
def test_build_harness():
    # Generate
    res = client.post(
        "/api/v1/projects/1/targets/1/harness",
        json={"input_type": "memory_buffer"}
    )
    harness_id = res.json()["id"]
    
    # Build
    b_res = client.post(f"/api/v1/projects/1/harnesses/{harness_id}/build")
    assert b_res.status_code == 200, b_res.text
    build_data = b_res.json()
    assert build_data["status"] == "SUCCESS"
    assert "mock_binary_data" not in build_data["stdout"]  # Just ensure stdout exists
    
    # Check updated harness status
    h_res = client.get(f"/api/v1/projects/1/targets/1/harnesses")
    harnesses = h_res.json()
    assert harnesses[0]["status"] == "VALIDATED"
    assert len(harnesses[0]["builds"]) == 1

def test_update_harness_status():
    res = client.post(
        "/api/v1/projects/1/targets/1/harness",
        json={"input_type": "file"}
    )
    harness_id = res.json()["id"]
    
    s_res = client.patch(
        f"/api/v1/projects/1/harnesses/{harness_id}/status",
        json={"status": "READY_FOR_FUZZING"}
    )
    assert s_res.status_code == 200, s_res.text
    assert s_res.json()["status"] == "READY_FOR_FUZZING"
