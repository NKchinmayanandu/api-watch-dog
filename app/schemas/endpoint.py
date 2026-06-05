from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class EndpointOut(BaseModel):
    endpoint_id: int
    url: str
    last_status: Optional[str] = None
    last_checked: Optional[datetime] = None
    last_changed: Optional[datetime] = None

    class Config:
        from_attributes = True

class LogOut(BaseModel):
    status: str
    checked_at: datetime

    class Config:
        from_attributes = True

class IncidentOut(BaseModel):
    id: int
    started_at: datetime
    resolved_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None

    class Config:
        from_attributes = True

class EndpointLogsOut(BaseModel):
    url: str
    logs: List[LogOut]
    incidents: List[IncidentOut]