from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict, Any

from .. import models, schemas
from ..database import get_db
from ..schemas_worker import WorkerRegistration, WorkerHeartbeat, WorkerLog, JobStatusUpdate

router = APIRouter(
    prefix="/api/v1/workers",
    tags=["workers"],
)

@router.post("/register", response_model=schemas.WorkerStatus)
def register_worker(reg: WorkerRegistration, db: Session = Depends(get_db)):
    worker = db.query(models.Worker).filter(models.Worker.hostname == reg.hostname).first()
    if not worker:
        worker = models.Worker(
            hostname=reg.hostname,
            ip_address=reg.ip_address,
            status="ONLINE",
            capabilities=reg.capabilities.model_dump()
        )
        db.add(worker)
    else:
        worker.ip_address = reg.ip_address
        worker.status = "ONLINE"
        worker.capabilities = reg.capabilities.model_dump()
        
    worker.last_seen = datetime.utcnow()
    db.commit()
    db.refresh(worker)
    return worker

@router.post("/{worker_id}/heartbeat")
def worker_heartbeat(worker_id: int, hb: WorkerHeartbeat, db: Session = Depends(get_db)):
    worker = db.query(models.Worker).filter(models.Worker.id == worker_id).first()
    if not worker:
        raise HTTPException(404, "Worker not found")
        
    worker.status = hb.status
    worker.last_seen = datetime.utcnow()
    db.commit()
    return {"status": "ok"}

@router.get("/{worker_id}/jobs/next")
def get_next_job(worker_id: int, db: Session = Depends(get_db)):
    # Find a job assigned to this worker that is PENDING
    job = db.query(models.WorkerJob).filter(
        models.WorkerJob.worker_id == worker_id,
        models.WorkerJob.status == "PENDING"
    ).first()
    
    if not job:
        # Return 204 No Content
        from fastapi import Response
        return Response(status_code=204)
        
    # Return minimal job protocol
    return {
        "id": job.id,
        "campaign_id": job.campaign_id,
        "job_type": job.job_type,
        "executable": "harness.exe",  # Derived dynamically in full implementation
        "args": [],
        "timeout": 3600
    }

@router.patch("/jobs/{job_id}")
def update_job_status(job_id: int, update: JobStatusUpdate, db: Session = Depends(get_db)):
    job = db.query(models.WorkerJob).filter(models.WorkerJob.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")
        
    job.status = update.status
    db.commit()
    return {"status": "ok"}

@router.post("/jobs/{job_id}/logs")
def stream_job_logs(job_id: int, log: WorkerLog, db: Session = Depends(get_db)):
    job = db.query(models.WorkerJob).filter(models.WorkerJob.id == job_id).first()
    if job:
        if job.logs is None:
            job.logs = ""
        job.logs += log.log + "\n"
        db.commit()
    return {"status": "ok"}

from ..schemas_campaign import CampaignMetricCreate

@router.post("/jobs/{job_id}/metrics")
def push_job_metrics(job_id: int, metrics: CampaignMetricCreate, db: Session = Depends(get_db)):
    job = db.query(models.WorkerJob).filter(models.WorkerJob.id == job_id).first()
    if not job or not job.campaign_id:
        raise HTTPException(404, "Job or associated campaign not found")
        
    metric_record = models.CampaignMetric(
        campaign_id=job.campaign_id,
        executions=metrics.executions,
        execs_per_second=metrics.execs_per_second,
        unique_paths=metrics.unique_paths,
        crashes=metrics.crashes,
        hangs=metrics.hangs
    )
    db.add(metric_record)
    
    # Update high-level campaign summary executions
    campaign = db.query(models.Campaign).filter(models.Campaign.id == job.campaign_id).first()
    if campaign and metrics.executions > (campaign.executions or 0):
        campaign.executions = metrics.executions
        
    db.commit()
    return {"status": "ok"}

@router.post("/jobs/{job_id}/artifacts")
def upload_artifact(job_id: int, type: str = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Stub for receiving crashes/queue files
    # file.filename
    return {"status": "uploaded"}
