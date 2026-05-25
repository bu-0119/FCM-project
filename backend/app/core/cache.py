import json
from typing import Any, Optional

import redis.asyncio as redis

from app.config import settings


class Cache:
    def __init__(self):
        self.client: Optional[redis.Redis] = None

    async def connect(self):
        self.client = redis.from_url(settings.redis_url, decode_responses=True)

    async def disconnect(self):
        if self.client:
            await self.client.close()

    async def get(self, key: str) -> Optional[Any]:
        val = await self.client.get(key)
        if val is None:
            return None
        try:
            return json.loads(val)
        except (json.JSONDecodeError, TypeError):
            return val

    async def set(self, key: str, value: Any, ttl: int = 3600):
        if not isinstance(value, str):
            value = json.dumps(value, ensure_ascii=False)
        await self.client.setex(key, ttl, value)

    async def delete(self, key: str):
        await self.client.delete(key)


cache = Cache()
