from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class EndpointOut(BaseModel):
    endpoint_id: int
    url: str
    last_status: Optional[str] = None
    last_checked: Optional[datetime] = None
    last_changed: Optional[datetime] = None

    class Config:
        from_attributes = True