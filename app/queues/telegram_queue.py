# app/queues/telegram_queue.py

import json

from app.cache.redis_client import redis_client


async def enqueue_telegram_message(
    chat_id: int,
    message: str
):
    await redis_client.rpush(
        "telegram_queue",
        json.dumps({
            "chat_id": chat_id,
            "message": message
        })
    )
    