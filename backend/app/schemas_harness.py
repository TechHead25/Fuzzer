from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class HarnessGenerateRequest(BaseModel):
    input_type: str  # file, buffer_and_length, memory_buffer
    init_code: Optional[str] = ""
    cleanup_code: Optional[str] = ""
    headers: Optional[List[str]] = []

class HarnessBuildSchema(BaseModel):
    id: int
    harness_id: int
    compiler: Optional[str]
    compiler_version: Optional[str]
    architecture: Optional[str]
    build_command: Optional[str]
    stdout: Optional[str]
    stderr: Optional[str]
    binary_path: Optional[str]
    hash: Optional[str]
    status: str
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

class HarnessSchema(BaseModel):
    id: int
    project_id: int
    target_id: int
    name: str
    engine: str
    input_type: str
    files: Optional[Dict[str, str]]
    metadata_json: Optional[Dict[str, Any]]
    status: str
    created_at: datetime
    updated_at: Optional[datetime]

    builds: List[HarnessBuildSchema] = []

    model_config = ConfigDict(from_attributes=True)

class HarnessStatusUpdate(BaseModel):
    status: str
