from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class AIAnalysisRecordSchema(BaseModel):
    id: int
    crash_id: int
    model_name: str
    model_version: str
    prompt_version: str
    evidence_ids: Optional[Dict[str, Any]] = None
    response_payload: Dict[str, Any]
    reviewer_decision: str
    reviewer_notes: Optional[str] = None
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)

class AIReviewPayload(BaseModel):
    decision: str  # "APPROVED", "REJECTED"
    notes: str
