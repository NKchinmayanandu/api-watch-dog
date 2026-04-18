from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from app.db.base import Base


class CheckLog(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    endpoint_id = Column(Integer, ForeignKey("endpoints.id"))
    status = Column(String)
    status_code = Column(Integer)
    checked_at = Column(DateTime, default=datetime.utcnow)
