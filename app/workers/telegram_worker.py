from app.queues.telegram_queue import telegram_queue

from app.services.telegram_service import send_message
from app.cache.redis_client import redis_client
import json
async def telegram_worker():
    print("telegram worker started 🚀 ")

    while True:

        #we are trying to get the job from the queue so 
        queue_name,job = await redis_client.blpop("telegram_queue")
        job = json.loads(job)
        try:
            await send_message(
                chat_id=job["chat_id"],
                message = job["message"]
                )
            
            print(f"✅ Sent Telegram message to {job['chat_id']}")

        except  Exception as e:
            print(f"❌ Telegram worker error: {e}")

        finally:
            telegram_queue.task_done()


