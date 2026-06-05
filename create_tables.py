from app.db.session import engine
from app.db.base import Base
from app.models.user import User
from app.models.endpoint import Endpoint
from app.models.logs import CheckLog
from app.models.incident import Incident

Base.metadata.create_all(bind=engine)
print("Tables created")
