import asyncio
import pytest

from a2a.server.events.redis_event_consumer import RedisEventConsumer


class FakeQueue:
    def __init__(self, items):
        self._items = list(items)
        self._closed = False

    async def dequeue_event(self, no_wait: bool = False):
        if not self._items:
            if no_wait:
                raise asyncio.QueueEmpty
            # simulate wait briefly
            await asyncio.sleep(0)
            raise asyncio.QueueEmpty
        return self._items.pop(0)

    def is_closed(self) -> bool:
        return self._closed


@pytest.mark.asyncio
async def test_consume_one_uses_no_wait():
    q = FakeQueue([])
    consumer = RedisEventConsumer(q)
    with pytest.raises(asyncio.QueueEmpty):
        await consumer.consume_one()


@pytest.mark.asyncio
async def test_consume_all_yields_until_closed():
    q = FakeQueue([1, 2])
    consumer = RedisEventConsumer(q)
    it = consumer.consume_all()
    results = []
    # consume two items then break by marking closed and expecting loop to exit
    results.append(await anext(it))
    results.append(await anext(it))
    # mark closed and ensure generator exits
    q._closed = True
    with pytest.raises(StopAsyncIteration):
        await anext(it)
    assert results == [1, 2]
