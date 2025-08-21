from __future__ import annotations

import os
from typing import Optional

try:
	import redis.asyncio as redis
except Exception:  # pragma: no cover
	redis = None  # Soft dependency


class RedisCheckpointer:
	"""Very small checkpoint helper for LangGraph-style workflows.
	Stores serialized state blobs under workflow_id keys.
	"""

	def __init__(self, redis_url: Optional[str] = None):
		self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
		self._client: Optional["redis.Redis"] = None

	async def connect(self) -> None:
		if redis is None:
			raise RuntimeError("redis-py not installed; please add redis to requirements")
		self._client = redis.from_url(self.redis_url, decode_responses=True)
		await self._client.ping()

	async def save(self, workflow_id: str, blob: str) -> None:
		if not self._client:
			raise RuntimeError("Redis client not connected")
		await self._client.set(f"lg:ckpt:{workflow_id}", blob)

	async def load(self, workflow_id: str) -> Optional[str]:
		if not self._client:
			raise RuntimeError("Redis client not connected")
		return await self._client.get(f"lg:ckpt:{workflow_id}") 