import asyncio
import json
import pytest

from a2a.server.events.redis_event_queue import RedisEventQueue


class FakeRedis:
    """Minimal fake redis supporting xadd, xread, set, delete for tests."""

    def __init__(self):
        # stream_key -> list of (id_str, fields_dict)
        self.streams: dict[str, list[tuple[str, dict]]] = {}

    async def xadd(self, stream_key: str, fields: dict, maxlen: int | None = None):
        lst = self.streams.setdefault(stream_key, [])
        idx = len(lst) + 1
        entry_id = f"{idx}-0"
        lst.append((entry_id, fields.copy()))
        # return id similar to real redis
        return entry_id

    async def xread(self, streams: dict, block: int = 0, count: int | None = None):
        # streams is {stream_key: last_id}
        results = []
        for key, last_id in streams.items():
            lst = self.streams.get(key, [])
            # determine numeric last id
            if last_id == '$':
                # interpret as current max id so return only entries added after this call
                last_num = len(lst)
            else:
                try:
                    last_num = int(str(last_id).split('-')[0])
                except Exception:
                    last_num = 0

            # collect entries with numeric id > last_num
            to_return = [(eid, fields) for (eid, fields) in lst if int(eid.split('-')[0]) > last_num]
            if to_return:
                results.append((key, to_return[: count if count is not None else None]))

        return results

    async def set(self, key: str, value: str):
        # no-op for tests
        return True

    async def delete(self, key: str):
        self.streams.pop(key, None)
        return True


class MessageEvent:
    """Dummy event with class name 'Message' and json() method."""

    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return json.dumps(self._payload)


@pytest.mark.asyncio
async def test_enqueue_dequeue_roundtrip():
    redis = FakeRedis()
    q = RedisEventQueue('task1', redis, stream_prefix='a2a:test', read_block_ms=10)
    evt = MessageEvent({'x': 1})
    await q.enqueue_event(evt)
    out = await q.dequeue_event(no_wait=True)
    assert out == {'x': 1}


@pytest.mark.asyncio
async def test_dequeue_no_wait_raises_on_empty():
    redis = FakeRedis()
    q = RedisEventQueue('task2', redis, stream_prefix='a2a:test', read_block_ms=10)
    with pytest.raises(asyncio.QueueEmpty):
        await q.dequeue_event(no_wait=True)


@pytest.mark.asyncio
async def test_close_tombstone_sets_closed_and_raises():
    redis = FakeRedis()
    q = RedisEventQueue('task3', redis, stream_prefix='a2a:test', read_block_ms=10)
    await q.enqueue_event(MessageEvent({'a': 1}))
    # close will append a CLOSE entry
    await q.close()
    # first dequeue should return the first event
    first = await q.dequeue_event(no_wait=True)
    assert first == {'a': 1}
    # next dequeue should see CLOSE and raise QueueEmpty while marking closed
    with pytest.raises(asyncio.QueueEmpty):
        await q.dequeue_event(no_wait=True)
    assert q.is_closed()


@pytest.mark.asyncio
async def test_tap_sees_only_future_events():
    redis = FakeRedis()
    q1 = RedisEventQueue('task4', redis, stream_prefix='a2a:test', read_block_ms=10)
    # enqueue before tap
    await q1.enqueue_event(MessageEvent({'before': True}))
    # create tap which should start at '$' and only see future events
    q2 = q1.tap()
    # q1 can dequeue the earlier event
    e1 = await q1.dequeue_event(no_wait=True)
    assert e1 == {'before': True}
    # enqueue another event; both q1 and q2 should be able to read it (q1 hasn't advanced past it yet)
    await q1.enqueue_event(MessageEvent({'later': 2}))
    out2 = await q2.dequeue_event(no_wait=True)
    assert out2 == {'later': 2}
