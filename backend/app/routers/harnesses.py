from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from .. import models
from ..database import get_db
from ..schemas_harness import HarnessSchema, HarnessGenerateRequest, HarnessBuildSchema, HarnessStatusUpdate
from ..harnesses.generator import generate_harness
from ..harnesses.builder import build_harness

router = APIRouter(
    prefix="/api/v1/projects/{project_id}",
    tags=["harnesses"],
)

@router.get("/harnesses", response_model=List[HarnessSchema])
def list_harnesses(project_id: int, db: Session = Depends(get_db)):
    harnesses = db.query(models.Harness).filter(models.Harness.project_id == project_id).all()
    # Attach builds manually if needed, or rely on lazy loading
    # SQLAlchemy will lazy load builds because we haven't set up the relationship explicitly in models for this snippet,
    # but let's query them manually if the relationship isn't configured.
    for h in harnesses:
        h.builds = db.query(models.HarnessBuild).filter(models.HarnessBuild.harness_id == h.id).order_by(models.HarnessBuild.id.desc()).all()
    return harnesses

@router.get("/targets/{target_id}/harnesses", response_model=List[HarnessSchema])
def list_target_harnesses(project_id: int, target_id: int, db: Session = Depends(get_db)):
    harnesses = db.query(models.Harness).filter(
        models.Harness.project_id == project_id,
        models.Harness.target_id == target_id
    ).all()
    for h in harnesses:
        h.builds = db.query(models.HarnessBuild).filter(models.HarnessBuild.harness_id == h.id).order_by(models.HarnessBuild.id.desc()).all()
    return harnesses


@router.post("/targets/{target_id}/harness", response_model=HarnessSchema)
def generate_harness_for_target(
    project_id: int, 
    target_id: int, 
    request: HarnessGenerateRequest,
    db: Session = Depends(get_db)
):
    target = db.query(models.Target).filter(models.Target.id == target_id, models.Target.project_id == project_id).first()
    if not target:
        raise HTTPException(404, "Target not found")

    metadata = {
        "init_code": request.init_code,
        "cleanup_code": request.cleanup_code,
        "headers": request.headers
    }
    
    files = generate_harness(target.name, target.module, request.input_type, metadata)
    
    # Check if harness already exists
    existing = db.query(models.Harness).filter(
        models.Harness.project_id == project_id,
        models.Harness.target_id == target_id,
        models.Harness.input_type == request.input_type
    ).first()

    if existing:
        existing.files = files
        existing.metadata_json = metadata
        existing.status = "CREATED"
        existing.updated_at = datetime.utcnow()
        db.commit()
        harness = existing
    else:
        harness = models.Harness(
            project_id=project_id,
            target_id=target_id,
            name=f"{target.name}_{request.input_type}",
            engine="winafl",
            input_type=request.input_type,
            files=files,
            metadata_json=metadata,
            status="CREATED"
        )
        db.add(harness)
        db.commit()
        db.refresh(harness)
        
    harness.builds = db.query(models.HarnessBuild).filter(models.HarnessBuild.harness_id == harness.id).order_by(models.HarnessBuild.id.desc()).all()
    return harness


@router.post("/harnesses/{harness_id}/build", response_model=HarnessBuildSchema)
def trigger_harness_build(project_id: int, harness_id: int, db: Session = Depends(get_db)):
    harness = db.query(models.Harness).filter(models.Harness.id == harness_id, models.Harness.project_id == project_id).first()
    if not harness:
        raise HTTPException(404, "Harness not found")

    # Update state
    harness.status = "BUILDING"
    db.commit()

    success, result = build_harness(harness.files or {})

    # Create Build record
    build = models.HarnessBuild(
        harness_id=harness.id,
        compiler=result.get("compiler"),
        compiler_version=result.get("compiler_version"),
        architecture=result.get("architecture"),
        build_command=result.get("build_command"),
        stdout=result.get("stdout"),
        stderr=result.get("stderr"),
        binary_path=result.get("binary_path"),
        hash=result.get("hash"),
        status="SUCCESS" if success else "FAILED"
    )
    db.add(build)
    
    harness.status = "VALIDATED" if success else "FAILED"
    db.commit()
    db.refresh(build)
    
    return build


@router.patch("/harnesses/{harness_id}/status", response_model=HarnessSchema)
def update_harness_status(project_id: int, harness_id: int, update: HarnessStatusUpdate, db: Session = Depends(get_db)):
    harness = db.query(models.Harness).filter(models.Harness.id == harness_id, models.Harness.project_id == project_id).first()
    if not harness:
        raise HTTPException(404, "Harness not found")
        
    harness.status = update.status
    harness.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(harness)
    
    harness.builds = db.query(models.HarnessBuild).filter(models.HarnessBuild.harness_id == harness.id).order_by(models.HarnessBuild.id.desc()).all()
    return harness
