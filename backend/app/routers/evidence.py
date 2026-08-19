import hashlib
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .. import models
from ..database import get_db
from ..schemas_evidence import EvidenceRecordSchema, EvidenceVerificationResult

router = APIRouter(
    prefix="/api/v1/projects/{project_id}/evidence",
    tags=["evidence"],
    responses={404: {"description": "Not found"}},
)

def _calculate_sha256(data: dict) -> str:
    # Serialize dict deterministically
    serialized = json.dumps(data, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()

@router.post("/generate/{campaign_id}", response_model=EvidenceRecordSchema)
def generate_evidence_snapshot(project_id: int, campaign_id: int, db: Session = Depends(get_db)):
    campaign = db.query(models.Campaign).filter(
        models.Campaign.id == campaign_id,
        models.Campaign.project_id == project_id
    ).first()
    if not campaign:
        raise HTTPException(404, "Campaign not found")
        
    target = db.query(models.Target).filter(models.Target.id == campaign.target_id).first()
    harness = db.query(models.HarnessBuild).filter(models.HarnessBuild.id == campaign.harness_id).first()
    worker = db.query(models.Worker).filter(models.Worker.id == campaign.worker_id).first()
    
    # Get associated crashes
    crashes = db.query(models.Crash).filter(models.Crash.campaign_id == campaign_id).all()
    crash_list = []
    for c in crashes:
        crash_data = {
            "id": c.id,
            "signature": c.crash_signature,
            "status": c.status,
            "input_artifact": c.input_artifact
        }
        # Get AI analysis for this crash if exists
        ai_record = db.query(models.AIAnalysisRecord).filter(models.AIAnalysisRecord.crash_id == c.id).first()
        if ai_record:
            crash_data["ai_analysis"] = ai_record.response_payload
            crash_data["reviewer_decision"] = ai_record.reviewer_decision
            
        crash_list.append(crash_data)

    # Build the payload tree
    payload = {
        "campaign_id": campaign.id,
        "timestamps": {
            "start": campaign.start_time.isoformat() if campaign.start_time else None,
            "end": campaign.end_time.isoformat() if campaign.end_time else None,
        },
        "target": {
            "id": target.id if target else None,
            "module": target.module if target else None
        },
        "harness": {
            "id": harness.id if harness else None,
            "build_hash": harness.build_hash if harness else None
        },
        "worker": {
            "id": worker.id if worker else None,
            "hostname": worker.hostname if worker else None
        },
        "crashes": crash_list
    }
    
    # Calculate integrity hash
    computed_hash = _calculate_sha256(payload)
    
    # Save the snapshot
    record = models.EvidenceRecord(
        project_id=project_id,
        entity_type="Campaign",
        entity_id=campaign_id,
        hash=computed_hash,
        payload=payload
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

@router.get("/", response_model=List[EvidenceRecordSchema])
def list_evidence(project_id: int, db: Session = Depends(get_db)):
    records = db.query(models.EvidenceRecord).filter(
        models.EvidenceRecord.project_id == project_id
    ).order_by(models.EvidenceRecord.timestamp.desc()).all()
    return records

@router.post("/verify/{evidence_id}", response_model=EvidenceVerificationResult)
def verify_integrity(project_id: int, evidence_id: int, db: Session = Depends(get_db)):
    record = db.query(models.EvidenceRecord).filter(
        models.EvidenceRecord.id == evidence_id,
        models.EvidenceRecord.project_id == project_id
    ).first()
    
    if not record:
        raise HTTPException(404, "Evidence Record not found")
        
    calculated_hash = _calculate_sha256(record.payload)
    
    return EvidenceVerificationResult(
        status="VERIFIED" if calculated_hash == record.hash else "MISMATCH",
        stored_hash=record.hash,
        calculated_hash=calculated_hash
    )
