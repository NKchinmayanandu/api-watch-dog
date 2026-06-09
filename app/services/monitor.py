import asyncio
import httpx
from datetime import datetime, timedelta

from app.services.telegram_service import send_message
from app.db.session import SessionLocal
from app.models.endpoint import Endpoint
from app.models.logs import CheckLog
from app.models.incident import Incident
from app.models.user import User
from app.queues.telegram_queue import enqueue
import json
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

HEADERS = {"User-Agent": "UptimeBot/1.0"}

async def check_endpoint(client: httpx.AsyncClient, url: str) -> tuple[str, int | None]:
    """Uses a shared client to make lightning-fast network calls."""
    try:
        response = await client.get(url, headers=HEADERS, timeout=5)
        if response.status_code == 200:
            return "UP", response.status_code
        return "DOWN", response.status_code
    except httpx.RequestError:
        return "DOWN", None



def has_status_changed(old_status: str, new_status: str) -> bool:
    return old_status != new_status


import asyncio
from datetime import datetime, timedelta

async def check_and_alert_endpoint(client:httpx.AsyncClient,
                                    endpoint_id,
                                    endpoint_url,
                                    endpoint_last_status,
                                    endpoint_last_checked,
                                    endpoint_last_changed,
                                    endpoint_user_id
                                    ):
    """
    Handles the entire lifecycle (check -> double-check -> DB log -> alert)
    for ONE endpoint. If it hits an 'await', other endpoints keep running!
    """
    # Each concurrent task must open and close its own database session
    db = SessionLocal()
    try:
        url = endpoint_url
        current_status, code = await check_endpoint(client,url)

        # 1. Double-check DOWN status immediately without blocking other sites
        if current_status == "DOWN":
            await asyncio.sleep(2)  # Pauses ONLY this site's task. Others fly past!
            current_status, code = await check_endpoint(client,url)

        last_status = endpoint_last_status

        # 2. Only proceed if status changed or it's the very first check
        if last_status is None or has_status_changed(last_status, current_status):
            
            # Create the log
            log = CheckLog(
                endpoint_id=endpoint_id,
                status=current_status,
                status_code=code,
            )
            db.add(log)

            # Handle Incident tracking
            if current_status == "DOWN":
                incident = Incident(endpoint_id=endpoint_id, started_at=datetime.utcnow())
                db.add(incident)
            elif current_status == "UP":
                active_incident = db.query(Incident).filter(
                    Incident.endpoint_id == endpoint_id,
                    Incident.resolved_at == None
                ).first()
                if active_incident:
                    active_incident.resolved_at = datetime.utcnow()
                    active_incident.duration_seconds = int(
                        (active_incident.resolved_at - active_incident.started_at).total_seconds()
                    )
            endpoint = db.query(Endpoint).filter(Endpoint.id==endpoint_id).first()
            endpoint.last_changed = datetime.utcnow()

            # Fetch the user's chat_id for alerting
            user = db.query(User).filter(User.id == endpoint.user_id).first()
            if user is None:
                return
            chat_id = user.chat_id if user else None

            # 3. Trigger the alert. If send_message takes 3 seconds, 
            # only THIS site waits. Other sites are completely unaffected.
            if last_status is None:
                if current_status == "DOWN":
                    #dumps for serialization
                    await enqueue(
                                            "telegram_queue",
                                            json.dumps({"chat_id": chat_id,
                                            "message": f"🚨 {url} went DOWN"
                                            })
                                        )
            else:
                if current_status == "DOWN":
                    await enqueue(
                                            "telegram_queue",
                                            json.dumps({"chat_id": chat_id,
                                            "message": f"🚨 {url} went DOWN"
                                            })
                                        )
                else:
                    await enqueue(
                                            "telegram_queue",
                                            {
                                            "chat_id":chat_id, 
                                            "message":f"🚨 {url} came UP"
                                            })

            # Update final endpoint state
            endpoint.last_status = current_status
        #this will be misleading for my optimzation of not writing into db for every check 
        #endpoint.last_checked = datetime.utcnow()
        db.commit()

    except Exception as e:
        print(f"❌ ERROR processing {endpoint_id}: {e}")
        db.rollback()
    finally:
        db.close()


async def run_monitor():
    last_cleanup = 0.0

    async with httpx.AsyncClient() as client:
        while True:
            now = asyncio.get_event_loop().time()
            
            # 1. Clean up old logs once an hour
            if now - last_cleanup > 3600:
                db = SessionLocal()
                try:
                    db.query(CheckLog).filter(
                        CheckLog.checked_at < datetime.utcnow() - timedelta(days=1)
                    ).delete()
                    db.commit()
                    last_cleanup = now
                    print("🧹 Old logs cleaned")
                except Exception as e:
                    print(f"❌ Cleanup error: {e}")
                finally:
                    db.close()

            # 2. Get all endpoint IDs to check
            db = SessionLocal()
            endpoints = db.query(Endpoint).all()
            tasks = [
                    check_and_alert_endpoint(
                    client,
                    endpoint_id= endpoint.id,
                    endpoint_url = endpoint.url,
                    endpoint_last_status =endpoint.last_status,
                    endpoint_last_checked = endpoint.last_checked,
                    endpoint_last_changed = endpoint.last_changed,
                    endpoint_user_id = endpoint.user_id
                )
                for endpoint in endpoints
                ]
            db.close()
             # Close main connection immediately

            print(f"🚀 Launching concurrent checks for endpoints...")

            # 3. Create a task for EVERY endpoint lifecycle

            # 4. FIRE THEM ALL AT ONCE! 
            # This triggers all HTTP requests, double-checks, and alerts in parallel.
            await asyncio.gather(*tasks)

            # 5. Rest for 30 seconds before doing it again
            await asyncio.sleep(30)


"""
problem i faced with optimizing code 
endpoint.last_changed = datetime.utcnow() but this thing brooooo we are changing the data 
base what the fuck i forgot about this but we can do query for which endpoint status actually
    changed actually changed so we wont get 100 query for 100 endpoint but the query for which 
endpoint status changed ig??


so the reason i done this loaded tasks = [
                    check_and_alert_endpoint(
                    client,
                    endpoint_id= endpoint.id,
                    ....
                    ]
is cause i was trying to optimize my query which reduced for 1000 endpoints query will be 1001 to 21 
which is hige improvment and removed uncessary writes into the database 

You still read all 10,000 every 30 seconds.

this where exactly queues comes in hand 
"""