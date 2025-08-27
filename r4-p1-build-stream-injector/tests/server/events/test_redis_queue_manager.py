import asyncio

import pytest


@pytest.mark.asyncio
async def test_create_or_tap_creates_queue(monkeypatch):
    created = {}

    class FakeRedisEventQueue:
        def __init__(self, task_id, redis_client, stream_prefix=None):
            self.task_id = task_id

        def tap(self):
            return FakeRedisEventQueue(self.task_id, None)

    # Monkeypatch import used in RedisQueueManager.create_or_tap by inserting
    # a proper module object with attribute `RedisEventQueue`.
    import types, sys
    fake_mod = types.ModuleType('a2a.server.events.redis_event_queue')
    fake_mod.RedisEventQueue = FakeRedisEventQueue
    monkeypatch.setitem(sys.modules, 'a2a.server.events.redis_event_queue', fake_mod)

    from a2a.server.events.redis_queue_manager import RedisQueueManager

    manager = RedisQueueManager(redis_client=None)
    q = await manager.create_or_tap('t1')
    assert hasattr(q, 'task_id')


@pytest.mark.asyncio
async def test_add_and_close(monkeypatch):
    class DummyQueue:
        def __init__(self, id):
            self.id = id

        async def close(self):
            return None

    from a2a.server.events.redis_queue_manager import RedisQueueManager

    manager = RedisQueueManager(redis_client=None)
    q = DummyQueue('t2')
    await manager.add('t2', q)
    got = await manager.get('t2')
    assert got is q
    await manager.close('t2')
    got2 = await manager.get('t2')
    assert got2 is None
