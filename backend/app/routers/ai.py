from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .. import models
from ..database import get_db
from ..schemas_ai import AIAnalysisRecordSchema, AIReviewPayload
from ..ai.provider import MockLocalProvider

router = APIRouter(
    prefix="/api/v1/projects/{project_id}",
    tags=["ai"],
    responses={404: {"description": "Not found"}},
)

# Instantiate the mock provider. In a real system this would be injected or configured.
ai_provider = MockLocalProvider()

@router.post("/crashes/{crash_id}/analyze", response_model=AIAnalysisRecordSchema)
def trigger_ai_analysis(project_id: int, crash_id: int, db: Session = Depends(get_db)):
    crash = db.query(models.Crash).filter(models.Crash.id == crash_id).first()
    if not crash:
        raise HTTPException(404, "Crash not found")
        
    context = {
        "exception_type": crash.exception_type,
        "module": crash.module,
        "stack_trace": crash.stack_trace,
        "fault_address": crash.fault_address
    }
    
    response_payload = ai_provider.analyze_crash(context)
    
    record = models.AIAnalysisRecord(
        crash_id=crash.id,
        model_name=ai_provider.model_name,
        model_version=ai_provider.model_version,
        prompt_version=ai_provider.prompt_version,
        evidence_ids={"crash_id": crash.id},
        response_payload=response_payload,
        reviewer_decision="PENDING"
    )
    
    db.add(record)
    db.commit()
    db.refresh(record)
    
    return record

@router.get("/crashes/{crash_id}/analyses", response_model=List[AIAnalysisRecordSchema])
def get_ai_analyses(project_id: int, crash_id: int, db: Session = Depends(get_db)):
    records = db.query(models.AIAnalysisRecord).filter(
        models.AIAnalysisRecord.crash_id == crash_id
    ).order_by(models.AIAnalysisRecord.timestamp.desc()).all()
    return records

@router.post("/analyses/{analysis_id}/review", response_model=AIAnalysisRecordSchema)
def review_ai_analysis(project_id: int, analysis_id: int, payload: AIReviewPayload, db: Session = Depends(get_db)):
    record = db.query(models.AIAnalysisRecord).filter(models.AIAnalysisRecord.id == analysis_id).first()
    if not record:
        raise HTTPException(404, "AI Analysis Record not found")
        
    record.reviewer_decision = payload.decision
    record.reviewer_notes = payload.notes
    
    db.commit()
    db.refresh(record)
    return record
