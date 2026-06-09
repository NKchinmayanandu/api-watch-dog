from app.cache.redis_client import redis_client
import json
# this is redis queue as queue is stored inside the redis
async def enqueue(queue_name:str,
                  data:dict):
    await redis_client.rpush(queue_name,json.dumps(dict))
