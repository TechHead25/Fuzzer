from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class WorkerDiagnostics(BaseModel):
    status: str
    issues: List[str]
    os: str
    memory_total_gb: float
    memory_available_gb: float
    disk_free_gb: float
    winafl_path: Optional[str]
    dynamorio_path: Optional[str]

class WorkerRegistration(BaseModel):
    hostname: str
    ip_address: str
    capabilities: WorkerDiagnostics

class WorkerHeartbeat(BaseModel):
    status: str

class WorkerLog(BaseModel):
    log: str

class JobStatusUpdate(BaseModel):
    status: str
    results: Optional[Dict[str, Any]] = {}
