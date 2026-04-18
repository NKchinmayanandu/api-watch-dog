from sqlalchemy import Column, Integer, String
from app.db.base import Base
from app.core.security import hash_password
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    chat_id = Column(String, nullable=True)