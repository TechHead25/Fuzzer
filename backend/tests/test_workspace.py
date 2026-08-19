"""
Tests for Phase 4: Workspace API and Import Engine.
"""

import pytest
import io
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import get_db
from app.models import Project, Base

# Use an in-memory SQLite DB for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_workspace.db"
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
    db.close()
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def test_import_ghidra_csv():
    csv_content = """Name,Location,Type,Namespace,Source
ParseDocumentHeader,0x00401234,Function,PdfReader,PdfReader.cpp
"""
    res = client.post(
        "/api/v1/projects/1/workspace/import",
        data={"import_type": "ghidra_csv"},
        files={"evidence_file": ("ghidra_export.csv", io.BytesIO(csv_content.encode()), "text/csv")}
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["targets_imported"] == 1
    assert data["import_type"] == "ghidra_csv"

    # Verify target was created
    t_res = client.get("/api/v1/projects/1/targets/")
    assert t_res.status_code == 200
    targets = t_res.json()
    assert len(targets) == 1
    assert targets[0]["name"] == "ParseDocumentHeader"
    assert targets[0]["address"] == "0x00401234"
    
    t_detail = client.get(f"/api/v1/projects/1/targets/{targets[0]['id']}")
    assert t_detail.status_code == 200
    assert t_detail.json()["address_kind"] == "observed"


def test_import_re_notes():
    notes_content = """
    {
      "targets": [
        {
          "function": "LoadImage",
          "module": "SumatraPDF",
          "address_kind": "user_provided",
          "risk_score": 8.5,
          "confidence": 0.9,
          "notes": "Found via manual reversing"
        }
      ]
    }
    """
    res = client.post(
        "/api/v1/projects/1/workspace/import",
        data={"import_type": "re_notes"},
        files={"evidence_file": ("notes.json", io.BytesIO(notes_content.encode()), "application/json")}
    )
    assert res.status_code == 200, res.text
    assert res.json()["targets_imported"] == 1

    t_res = client.get("/api/v1/projects/1/targets/")
    targets = t_res.json()
    assert len(targets) == 1
    
    t_detail = client.get(f"/api/v1/projects/1/targets/{targets[0]['id']}")
    assert t_detail.status_code == 200
    assert t_detail.json()["risk_score"] == 8.5
    assert t_detail.json()["address_kind"] == "user_provided"


def test_manual_target_creation_and_verification():
    # 1. Create target
    res = client.post(
        "/api/v1/projects/1/workspace/targets",
        json={
            "name": "ManualFunc",
            "module": "SumatraPDF",
            "address_kind": "user_provided",
            "risk_score": 5.0,
            "confidence": 1.0,
            "analyst_notes": "Added manually"
        }
    )
    assert res.status_code == 201, res.text
    target = res.json()
    assert target["name"] == "ManualFunc"
    assert target["status"] == "DISCOVERED"
    assert len(target["verifications"]) == 1

    target_id = target["id"]

    # 2. Verify target
    v_res = client.post(
        f"/api/v1/projects/1/workspace/targets/{target_id}/verify",
        json={
            "new_status": "REVIEW_REQUIRED",
            "verified_by": "alice",
            "notes": "Needs review"
        }
    )
    assert v_res.status_code == 200, v_res.text
    updated = v_res.json()
    assert updated["status"] == "REVIEW_REQUIRED"
    assert len(updated["verifications"]) == 2
    assert updated["verifications"][0]["new_status"] == "REVIEW_REQUIRED"

    # 3. Verify target to VERIFIED
    v2_res = client.post(
        f"/api/v1/projects/1/workspace/targets/{target_id}/verify",
        json={
            "new_status": "VERIFIED",
            "verified_by": "bob",
            "notes": "Looks good"
        }
    )
    assert v2_res.status_code == 200, v2_res.text
    updated2 = v2_res.json()
    assert updated2["status"] == "VERIFIED"
    assert updated2["verified_by"] == "bob"

    # 4. Try invalid transition
    v3_res = client.post(
        f"/api/v1/projects/1/workspace/targets/{target_id}/verify",
        json={
            "new_status": "ACTIVE",
            "verified_by": "bob"
        }
    )
    assert v3_res.status_code == 400
    assert "cannot transition" in v3_res.text
