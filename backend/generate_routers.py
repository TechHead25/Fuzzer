import os
from pathlib import Path

routers_dir = Path("app/routers")
routers_dir.mkdir(parents=True, exist_ok=True)
(routers_dir / "__init__.py").touch()

entities = [
    ("projects", "Project", "List of projects"),
    ("targets", "Target", "List of targets"),
    ("harnesses", "Harness", "List of harnesses"),
    ("campaigns", "Campaign", "List of campaigns"),
    ("crashes", "Crash", "List of crashes"),
    ("findings", "Finding", "List of findings"),
    ("reports", "Report", "List of reports"),
    ("evidence", "EvidenceRecord", "List of evidence records"),
]

for route, model, desc in entities:
    content = f"""from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from .. import schemas
from ..database import get_db

router = APIRouter(
    prefix="/api/v1/{route}",
    tags=["{route}"],
    responses={{404: {{"description": "Not found"}}}},
)

@router.get("/", response_model=List[schemas.{model}])
def read_{route}(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    # Returns empty list for MVP, explicitly stating no real results exist yet
    return []
"""
    with open(routers_dir / f"{route}.py", "w") as f:
        f.write(content)

health_content = """from fastapi import APIRouter

router = APIRouter(tags=["health"])

@router.get("/health")
def health_check():
    return {"status": "ok", "message": "Fuzz-Sentinel backend is running"}
"""
with open(routers_dir / "health.py", "w") as f:
    f.write(health_content)

print("Routers generated successfully.")
