from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.endpoint import Endpoint
from app.models.logs import CheckLog
from app.models.user import User
from app.api.deps import get_current_user
from app.schemas.endpoint import EndpointOut, EndpointLogsOut

from app.cache.rate_limiting import check_add_url_rate_limit
router = APIRouter()


import re

def is_valid_url(url: str):
    regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None

# 🔹 ADD ENDPOINT
@router.post("/add")
async def add_url(
    url: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    #checking the rate limiting 
    await check_add_url_rate_limit(
        user_id=current_user.id
    )

    if not is_valid_url(url):
        raise HTTPException(status_code=400, detail="Invalid URL format")
    
    count = (
    db.query(Endpoint)
    .filter(Endpoint.user_id == current_user.id)
    .count()
    )

    if count >= 8:
        raise HTTPException(
            status_code=400,
            detail="Maximum of 8 endpoints allowed"
            )

    # Check if this specific user already has this URL
    existing = db.query(Endpoint).filter(
        Endpoint.url == url, 
        Endpoint.user_id == current_user.id
    ).first()


    
    if existing:
        raise HTTPException(status_code=400, detail="URL already added")

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
    result = []
    for e in endpoints:
        result.append({
            "endpoint_id": e.id, 
            "url": e.url,
            "last_status": e.last_status,
            "last_checked": e.last_checked,
            "last_changed": e.last_changed
        })

    return result




# 🔹 GET LOGS FOR SPECIFIC ENDPOINT
@router.get("/{endpoint_id}/logs", response_model=EndpointLogsOut)
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

    #check log by descending order .order_by(CheckLog.checked_at.desc())
    logs = (
        db.query(CheckLog)
        .filter(CheckLog.endpoint_id == endpoint_id)
        .order_by(CheckLog.checked_at.desc())
        .limit(50)
        .all()
    )

    from app.models.incident import Incident
    incidents = (
        db.query(Incident)
        .filter(Incident.endpoint_id == endpoint_id)
        .order_by(Incident.started_at.desc())
        .limit(20)
        .all()
    )

    return {
        "url": endpoint.url,
        "logs": [{"status": log.status, "checked_at": log.checked_at} for log in logs],
        "incidents": [
            {
                "id": i.id,
                "started_at": i.started_at,
                "resolved_at": i.resolved_at,
                "duration_seconds": i.duration_seconds
            }
            for i in incidents
        ]
    }

# 🔹 DELETE ENDPOINT
@router.delete("/{endpoint_id}")
def delete_endpoint(
    endpoint_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    endpoint = db.query(Endpoint).filter(
        Endpoint.id == endpoint_id,
        Endpoint.user_id == current_user.id
    ).first()

    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found or not yours")

    # Delete related logs first to avoid foreign key constraints
    db.query(CheckLog).filter(CheckLog.endpoint_id == endpoint_id).delete()
    
    db.delete(endpoint)
    db.commit()
    return {"message": "Endpoint deleted successfully"}

@router.get("/test-telegram")
async def test_telegram():
    import os
    import httpx
    from fastapi import HTTPException

    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    if not BOT_TOKEN:
        raise HTTPException(
            status_code=500,
            detail="TELEGRAM_BOT_TOKEN not set"
        )

    if not CHAT_ID:
        raise HTTPException(
            status_code=500,
            detail="TELEGRAM_CHAT_ID not set"
        )

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": "🚀 test from backend"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                url,
                json=payload
            )
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=data
            )

        data = response.json()
        
        return {
            "success": True,
            "telegram_response": data
        }

    except httpx.RequestError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Telegram request failed: {str(e)}"
        )