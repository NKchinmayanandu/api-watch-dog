import json
import asyncio
import httpx
from datetime import datetime
from app.cache.redis_client import redis_client
from app.db.session import SessionLocal
from app.models.endpoint import Endpoint
from app.models.logs import CheckLog
from app.models.incident import Incident
from app.models.user import User
from app.queues.telegram_queue import enqueue_telegram_message
HEADERS = {"User-Agent": "UptimeBot/1.0"}
CONCURRENT_LIMIT = 50
from redis.asyncio import Redis

worker_redis = Redis(
    host="localhost",
    port=6379,
    decode_responses=True,
)

async def check_endpoint(client: httpx.AsyncClient, url: str) -> tuple[str, int | None]:
    try:
        response = await client.get(url, headers=HEADERS, timeout=5)
        if response.status_code == 200:
            return "UP", response.status_code
        return "DOWN", response.status_code
    except httpx.RequestError:
        return "DOWN", None
    
def has_status_changed(old_status: str, new_status: str) -> bool:
    return old_status != new_status

async def process_url_job(client: httpx.AsyncClient, raw_job: str):
    db = SessionLocal()
    endpoint_id = None
    try:
        job = json.loads(raw_job)
        endpoint_id = job["endpoint_id"]
        endpoint_url = job["endpoint_url"]
        endpoint_last_status = job["endpoint_last_status"]
        
        current_status, code = await check_endpoint(client, endpoint_url)
        if current_status == "DOWN":
            await asyncio.sleep(2)
            current_status, code = await check_endpoint(client, endpoint_url)
        last_status = endpoint_last_status
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
                    
            endpoint = db.query(Endpoint).filter(Endpoint.id == endpoint_id).first()
            if endpoint:
                endpoint.last_changed = datetime.utcnow()
                user = db.query(User).filter(User.id == endpoint.user_id).first()
                chat_id = user.chat_id if user else None
                # 3. Trigger the alert
                if chat_id:
                    if last_status is None:
                        if current_status == "DOWN":
                            await enqueue_telegram_message(chat_id, f"🚨 {endpoint_url} went DOWN")
                    else:
                        if current_status == "DOWN":
                            await enqueue_telegram_message(chat_id, f"🚨 {endpoint_url} went DOWN")
                        else:
                            await enqueue_telegram_message(chat_id, f"✅ {endpoint_url} came UP")
                endpoint.last_status = current_status
            
            db.commit()
    except Exception as e:
        print(f"❌ ERROR processing {endpoint_id}: {e}")
        db.rollback()
    finally:
        db.close()
        try:
            await redis_client.lrem("processing_url_queue", 1, raw_job)
        except Exception as queue_err:
            print(f"⚠️ Could not remove job from processing queue: {queue_err}")

semaphore = asyncio.Semaphore(CONCURRENT_LIMIT)
async def check_url_worker():
    print("url checker worker started 🚀")
    async with httpx.AsyncClient() as client:
        while True:
            try:
                raw_job = await worker_redis.brpoplpush("check_url_queue", "processing_url_queue", timeout=5)
                
                if not raw_job:
                    continue
                await semaphore.acquire()
                async def worker_task(job):
                    try:
                        await process_url_job(client, job)
                    finally:
                        semaphore.release()
                asyncio.create_task(worker_task(raw_job))
            except Exception as e:
                import traceback
                print(type(e))
                traceback.print_exc()