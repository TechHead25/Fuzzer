from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class CoverageSnapshotCreate(BaseModel):
    campaign_id: int
    target_id: Optional[int] = None
    coverage_metric: str = "edge"
    unique_paths: Optional[int] = None
    blocks: Optional[int] = None
    edges: Optional[int] = None
    coverage_data: Optional[Dict[str, Any]] = None
    artifact_reference: Optional[str] = None

class CoverageSnapshotSchema(BaseModel):
    id: int
    campaign_id: int
    target_id: Optional[int] = None
    timestamp: datetime
    coverage_metric: str
    unique_paths: Optional[int] = None
    blocks: Optional[int] = None
    edges: Optional[int] = None
    coverage_data: Optional[Dict[str, Any]] = None
    artifact_reference: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class CoverageDelta(BaseModel):
    baseline_campaign_id: int
    current_campaign_id: int
    baseline_paths: Optional[int] = None
    current_paths: Optional[int] = None
    delta_paths: Optional[int] = None
    baseline_blocks: Optional[int] = None
    current_blocks: Optional[int] = None
    delta_blocks: Optional[int] = None
