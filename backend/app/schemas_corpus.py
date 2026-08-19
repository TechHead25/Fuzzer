from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class SeedCorpusCreate(BaseModel):
    name: str
    description: Optional[str] = None

class SeedSchema(BaseModel):
    id: int
    corpus_id: int
    filename: str
    file_type: str
    origin: str
    size: int
    hash: str
    metadata_json: Optional[Dict[str, Any]] = None
    parent_seed_id: Optional[int] = None
    target_id: Optional[int] = None
    discovered_coverage: bool
    triggered_crash: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class SeedCorpusResponse(BaseModel):
    id: int
    project_id: int
    name: str
    description: Optional[str] = None
    created_at: datetime
    
    total_seeds: int
    total_bytes: int
    unique_hashes: int
    coverage_seeds: int
    crash_seeds: int

    model_config = ConfigDict(from_attributes=True)
