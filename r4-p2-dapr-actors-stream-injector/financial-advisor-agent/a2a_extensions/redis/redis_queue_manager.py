from __future__ import annotations

import asyncio
import logging
from typing import Any

from a2a.server.events.event_queue import EventQueue
from a2a.server.events.queue_manager import (
    NoTaskQueue,
    QueueManager,
    TaskQueueExists,
)

logger = logging.getLogger(__name__)


class RedisQueueManager(QueueManager):
    """QueueManager implementation backed by Redis streams.

    This manager keeps a local mapping of task_id to EventQueue instances for
    in-process taps, while the underlying events are stored in Redis streams.
    """

    def __init__(self, redis_client: Any, stream_prefix: str = 'a2a:task') -> None:
        self._redis = redis_client
        self._stream_prefix = stream_prefix
        self._task_queue: dict[str, EventQueue] = {}
        self._lock = asyncio.Lock()

    async def add(self, task_id: str, queue: EventQueue) -> None:
        async with self._lock:
            if task_id in self._task_queue:
                raise TaskQueueExists
            self._task_queue[task_id] = queue

    async def get(self, task_id: str) -> EventQueue | None:
        async with self._lock:
            return self._task_queue.get(task_id)

    async def tap(self, task_id: str) -> EventQueue | None:
        async with self._lock:
            if task_id not in self._task_queue:
                return None
            return self._task_queue[task_id].tap()

    async def close(self, task_id: str) -> None:
        async with self._lock:
            if task_id not in self._task_queue:
                raise NoTaskQueue
            queue = self._task_queue.pop(task_id)
        await queue.close()

    async def create_or_tap(self, task_id: str) -> EventQueue:
        async with self._lock:
            if task_id not in self._task_queue:
                # Import locally to avoid heavy optional imports at module load
                from a2a_extensions.redis.redis_event_queue import RedisEventQueue

                queue = RedisEventQueue(
                    task_id=task_id,
                    redis_client=self._redis,
                    stream_prefix=self._stream_prefix,
                )
                self._task_queue[task_id] = queue
                return queue
            return self._task_queue[task_id].tap()
