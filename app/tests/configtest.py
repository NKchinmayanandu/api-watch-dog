import pytest 
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.session import get_db
from app.db.base import Base
SQLALCHMEY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(url=SQLALCHMEY_DATABASE_URL,
                       poolclass=StaticPool,
                       connect_args={"check_same_thread": False},)
testing_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(engine)
    session = testing_session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.create_all(engine)

@pytest.fixture(scope="function")
def client(db_session):
    def db_override():
        try: 
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db]=db_override
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    