from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.endpoint import Endpoint
from app.models.logs import CheckLog
from app.models.user import User
from app.api.deps import get_current_user
from app.schemas.endpoint import EndpointOut

router = APIRouter()


# 🔹 ADD ENDPOINT
@router.post("/add")
def add_url(
    url: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    endpoint = Endpoint(url=url, user_id=current_user.id)
    db.add(endpoint)
    db.commit()
    return {"message": "added"}


# 🔹 GET USER ENDPOINTS
@router.get("/my/endpoints", response_model=list[EndpointOut])
def get_my_endpoints(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    endpoints = db.query(Endpoint).filter(
        Endpoint.user_id == current_user.id
    ).all()

    return [
        {"endpoint_id": e.id, "url": e.url}
        for e in endpoints
    ]


# 🔹 GET LOGS FOR SPECIFIC ENDPOINT
@router.get("/{endpoint_id}/logs")
def get_logs(
    endpoint_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    endpoint = db.query(Endpoint).filter(
        Endpoint.id == endpoint_id,
        Endpoint.user_id == current_user.id
    ).first()

    if not endpoint:
        raise HTTPException(status_code=404, detail="Not found or not yours")

    logs = (
        db.query(CheckLog)
        .filter(CheckLog.endpoint_id == endpoint_id)
        .order_by(CheckLog.checked_at.desc())
        .limit(50)
        .all()
    )

    return {
        "url": endpoint.url,
        "logs": logs
    }
@router.get("/test-telegram")
async def test_telegram():
    import httpx, os

    BOT_TOKEN = os.getenv("BOT_TOKEN")
    chat_id = "PUT_YOUR_CHAT_ID"

    async with httpx.AsyncClient() as client:
        await client.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": "🚀 test from backend"
            }
        )

    return {"sent": True}