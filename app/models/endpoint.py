from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from app.db.base import Base
from datetime import datetime
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.incident import Incident
from sqlalchemy.orm import relationship
class Endpoint(Base):
    __tablename__ = "endpoints"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"),index=True)
    last_status = Column(String, nullable=True)
    last_checked = Column(DateTime, nullable=True)
    last_changed = Column(DateTime, nullable=True)
    incidents = relationship("Incident", back_populates="endpoint", cascade="all, delete-orphan")
    logs = relationship("CheckLog", back_populates="endpoint", cascade="all, delete-orphan")