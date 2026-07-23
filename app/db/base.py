from sqlalchemy.orm import declarative_base

Base = declarative_base()

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.endpoint import Endpoint
    from app.models.incident import Incident
    from app.models.logs import CheckLog
    from app.models.user import User
    