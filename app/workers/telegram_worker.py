import json
import asyncio
from app.queues.telegram_queue import telegram_queue
from app.services.telegram_service import send_message
from app.cache.redis_client import redis_client

MAX_ATTEMPTS = 3

# 1. Move the actual work into a separate function
async def process_job(raw_job):
    try:
        job = json.loads(raw_job)
        if "attempts" not in job:
            job["attempts"] = 0
        job["attempts"] += 1

        try:
            # This awaits, but ONLY pauses this specific background task!
            # The main loop keeps running.
            await send_message(chat_id=job["chat_id"], message=job["message"])
            print(f"✅ Sent Telegram message to {job['chat_id']}")
            await redis_client.lrem("processing_queue", 1, raw_job)

        except Exception as e:
            print(f"❌ Telegram worker error: {e}")
            if job["attempts"] >= MAX_ATTEMPTS:
                async with redis_client.pipeline(transaction=True) as pipe:
                    pipe.lpush("dead_letter_queue", json.dumps(job))
                    pipe.lrem("processing_queue", 1, raw_job)
                    await pipe.execute()
            else:
                async with redis_client.pipeline(transaction=True) as pipe:
                    pipe.lpush("telegram_queue", json.dumps(job))
                    pipe.lrem("processing_queue", 1, raw_job)
                    await pipe.execute()

    except Exception as queue_err:
        print(f"⚠️ Job processing error: {queue_err}")

# 2. Keep the main loop strictly for fetching jobs
async def telegram_worker():
    print("telegram worker started 🚀 ")

    while True:
        try:
            # We still await here because we must wait until Redis actually has a job
            raw_job = await redis_client.brpoplpush("telegram_queue", "processing_queue", timeout=0)
            
            if not raw_job:
                continue

            # 🔥 THE MAGIC LINE: This spawns a background worker instantly!
            # It does NOT wait for process_job to finish.
            asyncio.create_task(process_job(raw_job))

        except Exception as q_err:
            print(f"⚠️ Redis Connection Error: {q_err}")
            await asyncio.sleep(1)
