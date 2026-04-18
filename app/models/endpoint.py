from sqlalchemy import Column, Integer, String,ForeignKey
from app.db.base import Base

class Endpoint(Base):
    __tablename__ = "endpoints"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))