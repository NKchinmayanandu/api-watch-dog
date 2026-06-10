import json

from app.cache.redis_client import redis_client

async def processing_enqueue(
        chat_id:int,
        message:str,
        attempts:int
):
    redis_client.rpush(
        "processing_queue",
        json.dumps({
            "chat_id": chat_id,
            "message": message,
            "attempts":attempts
        })
    )
    