import json
import asyncio
from app.services.telegram_service import send_message
from app.cache.redis_client import redis_client

MAX_ATTEMPTS = 3

async def process_job(raw_job):
    try:
        job = json.loads(raw_job)
        if "attempts" not in job:
            job["attempts"] = 0
        job["attempts"] += 1

        try:
            await send_message(chat_id=job["chat_id"], message=job["message"])
            print(f"✅ Sent Telegram message to {job['chat_id']}")
            await redis_client.lrem("processing_queue", 1, raw_job)

        except Exception as e:
            print(f"❌ Telegram worker error: {e}")
            if job["attempts"] >= MAX_ATTEMPTS:
                async with redis_client.pipeline(transaction=True) as pipe:
                    pipe.lpush("dead_letter_queue", json.dumps(job))
                    pipe.ltrim("dead_letter_queue", 0, 999)
                    pipe.lrem("processing_queue", 1, raw_job)
                    await pipe.execute()
            else:
                async with redis_client.pipeline(transaction=True) as pipe:
                    pipe.lpush("telegram_queue", json.dumps(job))
                    pipe.lrem("processing_queue", 1, raw_job)
                    await pipe.execute()

    except Exception as queue_err:
        print(f"⚠️ Job processing error: {queue_err}")

async def telegram_worker():
    print("telegram worker started 🚀 ")
    while True:
        try:
            result = await redis_client.brpop("telegram_queue", timeout=5)
            
            if not result:
                continue
            
            _, raw_job = result 
            
            asyncio.create_task(process_job(raw_job))

        except Exception as q_err:
            print(f"⚠️ Redis Connection Error: {q_err}")
            await asyncio.sleep(1)