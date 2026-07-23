import asyncio
import json
from datetime import datetime, timedelta
from app.services.telegram_service import send_message
from app.db.session import SessionLocal
from app.models.endpoint import Endpoint
from app.models.logs import CheckLog
from app.cache.redis_client import redis_client

async def run_monitor():
    last_cleanup = 0.0
    while True:
        now = asyncio.get_event_loop().time()
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
        db = SessionLocal()
        try:
            endpoints = db.query(Endpoint).all()
            jobs = []
            for endpoint in endpoints:
                job = {
                    "endpoint_id": endpoint.id,
                    "endpoint_url": endpoint.url,
                    "endpoint_last_status": endpoint.last_status,
                    "endpoint_last_checked": endpoint.last_checked.isoformat() if endpoint.last_checked else None,
                    "endpoint_last_changed": endpoint.last_changed.isoformat() if endpoint.last_changed else None,
                    "endpoint_user_id": endpoint.user_id
                }
                jobs.append(json.dumps(job))
        finally:
            db.close()
        if jobs:
            print(f"🚀 Enqueueing {len(jobs)} endpoints for checking...")
            async with redis_client.pipeline(transaction=True) as pipe:
                for job in jobs:
                    pipe.lpush("check_url_queue", job)
                await pipe.execute()
        await asyncio.sleep(30)

