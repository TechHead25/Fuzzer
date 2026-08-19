from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
import io
import csv

from .. import models
from ..database import get_db
from ..schemas_coverage import CoverageSnapshotCreate, CoverageSnapshotSchema, CoverageDelta

router = APIRouter(
    prefix="/api/v1/projects/{project_id}/coverage",
    tags=["coverage"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=CoverageSnapshotSchema)
def ingest_snapshot(project_id: int, payload: CoverageSnapshotCreate, db: Session = Depends(get_db)):
    # Verify campaign exists and belongs to project
    campaign = db.query(models.Campaign).filter(
        models.Campaign.id == payload.campaign_id,
        models.Campaign.project_id == project_id
    ).first()
    
    if not campaign:
        raise HTTPException(404, "Campaign not found")
        
    snapshot = models.CoverageSnapshot(
        campaign_id=payload.campaign_id,
        target_id=payload.target_id or campaign.target_id,
        coverage_metric=payload.coverage_metric,
        unique_paths=payload.unique_paths,
        blocks=payload.blocks,
        edges=payload.edges,
        coverage_data=payload.coverage_data,
        artifact_reference=payload.artifact_reference
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot

@router.get("/timeline", response_model=List[CoverageSnapshotSchema])
def get_coverage_timeline(project_id: int, target_id: int, db: Session = Depends(get_db)):
    # Fetch snapshots for all campaigns associated with this target, ordered chronologically
    snapshots = db.query(models.CoverageSnapshot).filter(
        models.CoverageSnapshot.target_id == target_id
    ).order_by(models.CoverageSnapshot.timestamp.asc()).all()
    
    # In a fully populated DB we would also check project_id via a JOIN, 
    # but target_id inherently belongs to a project.
    return snapshots

@router.get("/compare", response_model=CoverageDelta)
def compare_campaigns(project_id: int, baseline_id: int, current_id: int, db: Session = Depends(get_db)):
    # Get the latest snapshot for baseline
    baseline = db.query(models.CoverageSnapshot).filter(
        models.CoverageSnapshot.campaign_id == baseline_id
    ).order_by(models.CoverageSnapshot.timestamp.desc()).first()
    
    # Get the latest snapshot for current
    current = db.query(models.CoverageSnapshot).filter(
        models.CoverageSnapshot.campaign_id == current_id
    ).order_by(models.CoverageSnapshot.timestamp.desc()).first()
    
    if not baseline or not current:
        raise HTTPException(404, "Missing coverage data for one or both campaigns")
        
    delta = CoverageDelta(
        baseline_campaign_id=baseline_id,
        current_campaign_id=current_id,
        baseline_paths=baseline.unique_paths,
        current_paths=current.unique_paths,
        baseline_blocks=baseline.blocks,
        current_blocks=current.blocks
    )
    
    if delta.baseline_paths is not None and delta.current_paths is not None:
        delta.delta_paths = delta.current_paths - delta.baseline_paths
        
    if delta.baseline_blocks is not None and delta.current_blocks is not None:
        delta.delta_blocks = delta.current_blocks - delta.baseline_blocks
        
    return delta

@router.get("/export")
def export_coverage_csv(project_id: int, target_id: int, db: Session = Depends(get_db)):
    snapshots = db.query(models.CoverageSnapshot).filter(
        models.CoverageSnapshot.target_id == target_id
    ).order_by(models.CoverageSnapshot.timestamp.asc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Campaign ID', 'Timestamp', 'Metric', 'Unique Paths', 'Blocks', 'Edges', 'Artifact'])
    
    for snap in snapshots:
        writer.writerow([
            snap.id,
            snap.campaign_id,
            snap.timestamp.isoformat() if snap.timestamp else '',
            snap.coverage_metric,
            snap.unique_paths if snap.unique_paths is not None else '',
            snap.blocks if snap.blocks is not None else '',
            snap.edges if snap.edges is not None else '',
            snap.artifact_reference or ''
        ])
        
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]), 
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=coverage_target_{target_id}.csv"}
    )
