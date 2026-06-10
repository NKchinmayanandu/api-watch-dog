import json
import asyncio
from app.queues.telegram_queue import telegram_queue
from app.services.telegram_service import send_message
from app.cache.redis_client import redis_client

MAX_ATTEMPTS = 3  # Move to DLQ after 3 failed tries

async def telegram_worker():
    print("telegram worker started 🚀 ")

    while True:
        try:
            # brpoplpush blocks until an item is available. 
            # Note: brpoplpush returns just the item (string), NOT a (queue_name, item) tuple.
            raw_job = await redis_client.brpoplpush("telegram_queue", "processing_queue", timeout=0)
            
            if not raw_job:
                continue

            # Load the job structure
            job = json.loads(raw_job)
            
            # Initialize attempts tracking if it doesn't exist
            if "attempts" not in job:
                job["attempts"] = 0
                
            job["attempts"] += 1

            try:
                # Attempt to send the message
                await send_message(
                    chat_id=job["chat_id"],
                    message=job["message"]
                )
                print(f"✅ Sent Telegram message to {job['chat_id']}")
                
                # SUCCESS: Safe to completely remove from the processing queue
                await redis_client.lrem("processing_queue", 1, raw_job)

            except Exception as e:
                print(f"❌ Telegram worker error: {e}")
                
                # Check if we should retry or send to DLQ
                if job["attempts"] >= MAX_ATTEMPTS:
                    print(f"💀 Job exceeded max attempts. Moving to dead_letter_queue: {job}")
                    
                    # Add to DLQ and remove from processing queue atomically using a pipeline
                    async with redis_client.pipeline(transaction=True) as pipe:
                        pipe.lpush("dead_letter_queue", json.dumps(job))
                        pipe.lrem("processing_queue", 1, raw_job)
                        await pipe.execute()
                else:
                    # RETRY: Put it back into the main queue for another worker to try
                    print(f"🔄 Retrying job (Attempt {job['attempts']}/{MAX_ATTEMPTS})")
                    
                    async with redis_client.pipeline(transaction=True) as pipe:
                        pipe.lpush("telegram_queue", json.dumps(job))
                        pipe.lrem("processing_queue", 1, raw_job)
                        await pipe.execute()

        except Exception as queue_err:
            print(f"⚠️ Critical Queue/JSON Error: {queue_err}")
            # Prevent rapid infinite looping if Redis disconnects momentarily
            await asyncio.sleep(1)
