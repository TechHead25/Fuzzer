from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class ReportSchema(BaseModel):
    id: int
    project_id: int
    campaign_id: int
    title: str
    content_html: str
    report_hash: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
