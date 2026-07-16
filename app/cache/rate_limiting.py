from app.cache.redis_client import redis_client
from fastapi import HTTPException

async def rate_limit(key:str,
                  window:int,
                  limit:int
                  ):
    
    count = await redis_client.incr(key)

    if count == 1:
        await redis_client.expire(key, window)

    ttl = await redis_client.ttl(key)
    if count > limit:
        raise HTTPException(
            status_code=429,
            detail=f"number of attempts exceeded, try again after {ttl} seconds!"
        )
    
async def check_add_url_rate_limit(user_id:int):
    await rate_limit(
        key=f"rate_limit:add_url:{user_id}",
        window=60,
        limit=8
        )
    
    