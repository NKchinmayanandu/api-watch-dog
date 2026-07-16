import json
from app.cache.redis_client import redis_client

async def set_cache(key:str, data):
    await redis_client.set(
        key,
        json.dumps(data),
        ex=60
    )

async def get_cached(key:str):
    data = await redis_client.get(key)
    if data is None:
        return None
    return json.loads(data)

