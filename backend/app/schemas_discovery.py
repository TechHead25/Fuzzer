"""
Pydantic schemas for Target Discovery (Phase 3).
Kept separate from schemas.py to avoid growing that file too large.
"""

from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime


class TargetSummary(BaseModel):
    """Compact view used in ranked target tables."""
    id: int
    project_id: int
    name: str
    module: str
    source_file: Optional[str] = None
    source_line: Optional[int] = None
    address: Optional[str] = None
    input_type: str
    risk_score: float
    confidence: float
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ScoringReasonSchema(BaseModel):
    indicator: str
    description: str
    weight: float
    evidence_kind: str   # "observed" | "inferred" | "user_provided"
    source_ref: Optional[str] = None


class TargetDetail(BaseModel):
    """Full target record including evidence breakdown."""
    id: int
    project_id: int
    name: str
    module: str
    source_file: Optional[str] = None
    source_line: Optional[int] = None
    address: Optional[str] = None
    address_kind: Optional[str] = None   # ALWAYS "inferred" unless binary-verified
    input_type: str
    risk_score: float
    confidence: float
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Evidence
    risk_reasons: List[Dict[str, Any]] = []
    attacker_controlled_inputs: List[Dict[str, Any]] = []
    memory_operations: Dict[str, Any] = {}
    call_path: List[Dict[str, Any]] = []
    dependencies: List[str] = []
    suggested_harness_type: str = "file_reader"

    model_config = ConfigDict(from_attributes=True)


class TargetEvidenceSchema(BaseModel):
    id: int
    entity_type: str
    entity_id: int
    hash: str
    payload: Dict[str, Any]
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class DiscoveryJobCreate(BaseModel):
    min_score: float = 1.0


class DiscoveryJobStatus(BaseModel):
    job_id: str
    status: str          # pending | running | complete | error
    progress: float      # 0.0 – 1.0
    message: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
