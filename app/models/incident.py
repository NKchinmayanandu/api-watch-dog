from sqlalchemy import Column, Integer, DateTime, ForeignKey
from datetime import datetime
from app.db.base import Base
from sqlalchemy.orm import relationship
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.endpoint import Endpoint
class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    endpoint_id = Column(Integer, ForeignKey("endpoints.id"))
    started_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    incidents = relationship("Incident", back_populates="endpoint", cascade="all, delete-orphan")