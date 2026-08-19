from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class EvidenceRecordSchema(BaseModel):
    id: int
    project_id: int
    entity_type: str
    entity_id: int
    hash: str
    payload: Dict[str, Any]
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)

class EvidenceVerificationResult(BaseModel):
    status: str # "VERIFIED", "MISMATCH"
    stored_hash: str
    calculated_hash: str
