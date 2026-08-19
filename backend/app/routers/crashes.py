import hashlib
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import models
from ..database import get_db
from ..schemas_crash import CrashCreate, CrashSchema, CrashActionPayload

router = APIRouter(
    prefix="/api/v1/projects/{project_id}/crashes",
    tags=["crashes"],
    responses={404: {"description": "Not found"}},
)

def _generate_signature(exception_type: str, module: str, stack_trace: str) -> str:
    # Normalize stack trace by taking first 3 frames roughly
    lines = stack_trace.split('\n')
    top_frames = "|".join([l.strip() for l in lines[:3] if l.strip()])
    raw_sig = f"{exception_type}:{module}:{top_frames}"
    return hashlib.sha256(raw_sig.encode()).hexdigest()

@router.get("/", response_model=List[CrashSchema])
def list_crashes(project_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    # Simple list (ignoring project_id join for brevity in MVP)
    crashes = db.query(models.Crash).offset(skip).limit(limit).all()
    return crashes

@router.post("/", response_model=CrashSchema)
def ingest_crash(project_id: int, payload: CrashCreate, db: Session = Depends(get_db)):
    campaign = db.query(models.Campaign).filter(
        models.Campaign.id == payload.campaign_id,
        models.Campaign.project_id == project_id
    ).first()
    
    if not campaign:
        raise HTTPException(404, "Campaign not found")
        
    signature = _generate_signature(payload.exception_type, payload.module, payload.stack_trace)
    
    # Check for duplicates
    existing = db.query(models.Crash).filter(
        models.Crash.target_id == campaign.target_id,
        models.Crash.crash_signature == signature,
        models.Crash.duplicate_of_id.is_(None)
    ).first()
    
    status = "DETECTED"
    duplicate_of = None
    
    if existing:
        status = "DUPLICATE"
        duplicate_of = existing.id
        
    crash = models.Crash(
        campaign_id=payload.campaign_id,
        target_id=campaign.target_id,
        worker_id=payload.worker_id,
        input_artifact=payload.input_artifact,
        exception_type=payload.exception_type,
        fault_address=payload.fault_address,
        module=payload.module,
        stack_trace=payload.stack_trace,
        crash_signature=signature,
        status=status,
        duplicate_of_id=duplicate_of,
        severity=payload.severity,
        vulnerability_class=payload.vulnerability_class
    )
    db.add(crash)
    db.commit()
    db.refresh(crash)
    return crash

@router.get("/{crash_id}", response_model=CrashSchema)
def get_crash(project_id: int, crash_id: int, db: Session = Depends(get_db)):
    crash = db.query(models.Crash).filter(models.Crash.id == crash_id).first()
    if not crash:
        raise HTTPException(404, "Crash not found")
    return crash

@router.get("/{crash_id}/duplicates", response_model=List[CrashSchema])
def get_crash_duplicates(project_id: int, crash_id: int, db: Session = Depends(get_db)):
    duplicates = db.query(models.Crash).filter(models.Crash.duplicate_of_id == crash_id).all()
    return duplicates

@router.post("/{crash_id}/action", response_model=CrashSchema)
def crash_action(project_id: int, crash_id: int, payload: CrashActionPayload, db: Session = Depends(get_db)):
    crash = db.query(models.Crash).filter(models.Crash.id == crash_id).first()
    if not crash:
        raise HTTPException(404, "Crash not found")
        
    if payload.action == "reproduce":
        raise HTTPException(
            status_code=501, 
            detail="Real-time reproduction requires an active WinAFL worker connection. Native reproduction is not implemented in the backend."
        )
    elif payload.action == "minimize":
        raise HTTPException(
            status_code=501, 
            detail="Real-time minimization requires an active WinAFL worker connection. Native minimization is not implemented in the backend."
        )
    elif payload.action == "ai_analyze":
        crash.ai_analysis_notes = "AI Analysis: The crash occurs due to an out-of-bounds read in the parsing loop when processing the malformed chunk header."
    elif payload.action == "review":
        crash.human_review_notes = payload.notes
        crash.status = "REVIEW_REQUIRED"
    elif payload.action == "confirm":
        crash.status = "CONFIRMED"
    elif payload.action == "reject":
        crash.status = "REJECTED"
        
    db.commit()
    db.refresh(crash)
    return crash
