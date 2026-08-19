from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from .. import models
from ..database import get_db
from ..schemas_campaign import CampaignSchema, CampaignCreate, CampaignConfigurationBase

router = APIRouter(
    prefix="/api/v1/projects/{project_id}/campaigns",
    tags=["campaigns"],
    responses={404: {"description": "Not found"}},
)

def _build_campaign_schema(campaign, db: Session) -> CampaignSchema:
    config_model = db.query(models.CampaignConfiguration).filter(models.CampaignConfiguration.campaign_id == campaign.id).first()
    metrics = db.query(models.CampaignMetric).filter(models.CampaignMetric.campaign_id == campaign.id).order_by(models.CampaignMetric.id.desc()).limit(50).all()
    
    config_data = None
    if config_model:
        config_data = CampaignConfigurationBase(
            corpus_id=config_model.corpus_id,
            fuzzer_version=config_model.fuzzer_version,
            instrumentation_version=config_model.instrumentation_version,
            command_args=config_model.command_args,
            env_vars=config_model.env_vars,
            timeout=config_model.timeout,
            duration_limit_secs=config_model.duration_limit_secs,
            memory_limit=config_model.memory_limit,
            dictionary_path=config_model.dictionary_path
        )
    
    c_schema = CampaignSchema.model_validate(campaign)
    c_schema.configuration = config_data
    # Convert metrics models to schemas implicitly via response_model
    c_schema.metrics = metrics
    return c_schema

@router.get("/", response_model=List[CampaignSchema])
def list_campaigns(project_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    campaigns = db.query(models.Campaign).filter(models.Campaign.project_id == project_id).offset(skip).limit(limit).all()
    return [_build_campaign_schema(c, db) for c in campaigns]

@router.post("/", response_model=CampaignSchema)
def create_campaign(project_id: int, payload: CampaignCreate, db: Session = Depends(get_db)):
    campaign = models.Campaign(
        project_id=project_id,
        target_id=payload.target_id,
        harness_id=payload.harness_id,
        worker_id=payload.worker_id,
        fuzzer=payload.fuzzer,
        instrumentation=payload.instrumentation,
        status="CREATED"
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)

    config = models.CampaignConfiguration(
        campaign_id=campaign.id,
        corpus_id=payload.configuration.corpus_id,
        fuzzer_version=payload.configuration.fuzzer_version,
        instrumentation_version=payload.configuration.instrumentation_version,
        command_args=payload.configuration.command_args,
        env_vars=payload.configuration.env_vars,
        timeout=payload.configuration.timeout,
        duration_limit_secs=payload.configuration.duration_limit_secs,
        memory_limit=payload.configuration.memory_limit,
        dictionary_path=payload.configuration.dictionary_path
    )
    db.add(config)
    
    # Pre-assign to worker jobs queue if worker_id provided
    if campaign.worker_id:
        job = models.WorkerJob(
            worker_id=campaign.worker_id,
            campaign_id=campaign.id,
            job_type="fuzz",
            status="PENDING"
        )
        db.add(job)
        
    db.commit()
    db.refresh(campaign)
    return _build_campaign_schema(campaign, db)

@router.get("/{campaign_id}", response_model=CampaignSchema)
def get_campaign(project_id: int, campaign_id: int, db: Session = Depends(get_db)):
    campaign = db.query(models.Campaign).filter(models.Campaign.id == campaign_id, models.Campaign.project_id == project_id).first()
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    return _build_campaign_schema(campaign, db)

@router.post("/{campaign_id}/start", response_model=CampaignSchema)
def start_campaign(project_id: int, campaign_id: int, db: Session = Depends(get_db)):
    campaign = db.query(models.Campaign).filter(models.Campaign.id == campaign_id, models.Campaign.project_id == project_id).first()
    if not campaign:
        raise HTTPException(404, "Campaign not found")
        
    if campaign.status not in ["CREATED", "PAUSED", "COMPLETED", "FAILED", "CANCELLED"]:
        raise HTTPException(400, "Invalid state transition")
        
    campaign.status = "QUEUED"
    campaign.start_time = datetime.utcnow()
    
    # If starting, make sure there's a PENDING job for the worker
    if campaign.worker_id:
        existing_job = db.query(models.WorkerJob).filter(
            models.WorkerJob.campaign_id == campaign.id,
            models.WorkerJob.status.in_(["PENDING", "RUNNING"])
        ).first()
        if not existing_job:
            job = models.WorkerJob(
                worker_id=campaign.worker_id,
                campaign_id=campaign.id,
                job_type="fuzz",
                status="PENDING"
            )
            db.add(job)
            
    db.commit()
    return _build_campaign_schema(campaign, db)

@router.post("/{campaign_id}/pause", response_model=CampaignSchema)
def pause_campaign(project_id: int, campaign_id: int, db: Session = Depends(get_db)):
    campaign = db.query(models.Campaign).filter(models.Campaign.id == campaign_id, models.Campaign.project_id == project_id).first()
    if not campaign:
        raise HTTPException(404, "Campaign not found")
        
    campaign.status = "PAUSED"
    
    # Attempt to cancel any running job
    running_job = db.query(models.WorkerJob).filter(
        models.WorkerJob.campaign_id == campaign.id,
        models.WorkerJob.status.in_(["PENDING", "RUNNING"])
    ).first()
    if running_job:
        running_job.status = "CANCELLED"
        
    db.commit()
    return _build_campaign_schema(campaign, db)

@router.post("/{campaign_id}/stop", response_model=CampaignSchema)
def stop_campaign(project_id: int, campaign_id: int, db: Session = Depends(get_db)):
    campaign = db.query(models.Campaign).filter(models.Campaign.id == campaign_id, models.Campaign.project_id == project_id).first()
    if not campaign:
        raise HTTPException(404, "Campaign not found")
        
    campaign.status = "STOPPING"
    campaign.end_time = datetime.utcnow()
    
    # Attempt to cancel any running job
    running_job = db.query(models.WorkerJob).filter(
        models.WorkerJob.campaign_id == campaign.id,
        models.WorkerJob.status.in_(["PENDING", "RUNNING"])
    ).first()
    if running_job:
        running_job.status = "CANCELLED"
        
    db.commit()
    return _build_campaign_schema(campaign, db)
