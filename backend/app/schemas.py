from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class Project(ProjectBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class TargetBase(BaseModel):
    name: str
    module: str
    address: Optional[str] = None
    source_file: Optional[str] = None
    source_line: Optional[int] = None
    input_type: str
    risk_score: float
    confidence: float
    status: str

class Target(TargetBase):
    id: int
    project_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class HarnessBase(BaseModel):
    name: str
    source_code: str
    status: str

class Harness(HarnessBase):
    id: int
    project_id: int
    target_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CampaignBase(BaseModel):
    fuzzer: str
    instrumentation: str
    status: str

class Campaign(CampaignBase):
    id: int
    project_id: int
    target_id: int
    harness_id: int
    worker_id: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    executions: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CrashBase(BaseModel):
    exception_type: str
    fault_address: str
    module: str
    stack_trace: str
    crash_signature: str
    reproduction_status: str
    severity: str
    vulnerability_class: str

class Crash(CrashBase):
    id: int
    campaign_id: int
    target_id: int
    input_artifact: str
    minimized_artifact: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class FindingBase(BaseModel):
    title: str
    description: str
    severity: str
    status: str

class Finding(FindingBase):
    id: int
    project_id: int
    target_id: int
    crash_id: int

    model_config = ConfigDict(from_attributes=True)

class ReportBase(BaseModel):
    title: str
    status: str
    artifact_path: str
    hash: str

class Report(ReportBase):
    id: int
    project_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class EvidenceRecordBase(BaseModel):
    entity_type: str
    entity_id: int
    hash: str
    payload: Dict[str, Any]

class EvidenceRecord(EvidenceRecordBase):
    id: int
    project_id: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class DashboardStats(BaseModel):
    active_campaigns: int
    total_executions: int
    execs_per_second: float
    unique_paths: int
    coverage_percent: float
    raw_crashes: int
    unique_crashes: int
    confirmed_findings: int
    total_targets: int
    total_workers: int
    online_workers: int

class WorkerStatus(BaseModel):
    id: int
    hostname: str
    ip_address: str
    status: str
    last_seen: Optional[datetime] = None
    capabilities: Optional[Dict[str, Any]] = None
    model_config = ConfigDict(from_attributes=True)

class RecentActivity(BaseModel):
    id: int
    entity_type: str  # \'campaign\', \'crash\', \'finding\', \'target\'
    entity_id: int
    message: str
    timestamp: datetime

class CoverageTrendPoint(BaseModel):
    timestamp: str
    edges: int
    blocks: int

class ExecutionTrendPoint(BaseModel):
    timestamp: str
    executions: int
    execs_per_second: float

class CrashTrendPoint(BaseModel):
    timestamp: str
    total_crashes: int
    unique_crashes: int

class TargetRiskItem(BaseModel):
    name: str
    module: str
    risk_score: float
    status: str

class DashboardResponse(BaseModel):
    stats: DashboardStats
    workers: List[WorkerStatus]
    recent_activity: List[RecentActivity]
    coverage_trend: List[CoverageTrendPoint]
    execution_trend: List[ExecutionTrendPoint]
    crash_trend: List[CrashTrendPoint]
    target_risk_distribution: List[TargetRiskItem]
    active_campaigns_list: List[Campaign]
