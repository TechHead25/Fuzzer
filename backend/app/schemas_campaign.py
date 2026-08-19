from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class CampaignConfigurationBase(BaseModel):
    corpus_id: Optional[int] = None
    fuzzer_version: Optional[str] = None
    instrumentation_version: Optional[str] = None
    command_args: Optional[Dict[str, Any]] = {}
    env_vars: Optional[Dict[str, Any]] = {}
    timeout: Optional[int] = 3600
    duration_limit_secs: Optional[int] = None
    memory_limit: Optional[int] = 2048
    dictionary_path: Optional[str] = None

class CampaignCreate(BaseModel):
    target_id: int
    harness_id: int
    worker_id: Optional[int] = None
    fuzzer: str = "winafl"
    instrumentation: str = "dynamorio"
    configuration: CampaignConfigurationBase

class CampaignMetricSchema(BaseModel):
    id: int
    timestamp: datetime
    executions: int
    execs_per_second: float
    unique_paths: int
    crashes: int
    hangs: int
    model_config = ConfigDict(from_attributes=True)

class CampaignMetricCreate(BaseModel):
    executions: int
    execs_per_second: float
    unique_paths: int
    crashes: int
    hangs: int

class CampaignSchema(BaseModel):
    id: int
    project_id: int
    target_id: int
    harness_id: int
    worker_id: Optional[int] = None
    fuzzer: str
    instrumentation: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: str
    executions: int
    created_at: datetime
    
    # We will attach config and recent metrics in the response
    configuration: Optional[CampaignConfigurationBase] = None
    metrics: List[CampaignMetricSchema] = []

    model_config = ConfigDict(from_attributes=True)
