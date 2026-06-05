from app.cache.redis_client import redis_client
from fastapi import HTTPException
def rate_limit(key:str,
                  window:int,
                  limit:int
                  ):
    
    count = redis_client.incr(key)

    if count == 1:
        redis_client.expire(key,window)

    ttl = redis_client.ttl(key)
    if count > limit:
        raise HTTPException(
            status_code=429,
            detail=f"number of attempts exceeded, try again after {ttl} seconds!"
        )
    
def check_add_url_rate_limit(user_id:int):
    rate_limit(
        key=f"rate_limit:add_url:{user_id}",
        window=60,
        limit=8
        )
    
    