from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class CrashCreate(BaseModel):
    campaign_id: int
    worker_id: Optional[int] = None
    input_artifact: str
    exception_type: str
    fault_address: str
    module: str
    stack_trace: str
    severity: Optional[str] = None
    vulnerability_class: Optional[str] = None

class CrashSchema(BaseModel):
    id: int
    campaign_id: int
    target_id: int
    worker_id: Optional[int] = None
    input_artifact: str
    minimized_artifact: Optional[str] = None
    exception_type: str
    fault_address: str
    module: str
    stack_trace: str
    crash_signature: str
    status: str
    duplicate_of_id: Optional[int] = None
    ai_analysis_notes: Optional[str] = None
    human_review_notes: Optional[str] = None
    severity: Optional[str] = None
    vulnerability_class: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class CrashActionPayload(BaseModel):
    action: str # "reproduce", "minimize", "review", "confirm", "reject", "ai_analyze"
    notes: Optional[str] = None
