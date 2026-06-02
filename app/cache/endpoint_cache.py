import json
from app.cache.redis_client import redis_client

def set_cache(key:str,data):
    redis_client.set(
        key,
        json.dumps(data),
        ex = 60
    )
def get_cached(key:str):
    data = redis_client.get(key)
    if data is None:
        return None
    return json.loads(data)

