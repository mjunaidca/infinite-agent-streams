"""
Tests for StreamInjector.
"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from a2a.utils.stream_write.stream_injector import StreamInjector


@pytest.mark.asyncio
async def test_stream_injector_creation():
    """Test that StreamInjector can be created."""
    injector = StreamInjector()
    assert injector.redis_url == 'redis://localhost:6379/0'
    assert not injector._connected
    assert injector._client is None


@pytest.mark.asyncio
async def test_connection_management():
    """Test connection and disconnection."""
    injector = StreamInjector()

    # Mock Redis client
    mock_client = AsyncMock()
    mock_client.ping = AsyncMock()
    mock_client.aclose = AsyncMock()

    # Mock Redis.from_url to return our mock client
    with pytest.MonkeyPatch().context() as m:
        m.setattr('a2a.utils.stream_write.stream_injector.Redis.from_url', MagicMock(return_value=mock_client))
        # Test connection
        await injector.connect()
        assert injector._connected
        assert injector._client is not None
        mock_client.ping.assert_called_once()

        # Test disconnection
        await injector.disconnect()
        assert not injector._connected
        assert injector._client is None
        mock_client.aclose.assert_called_once()


@pytest.mark.asyncio
async def test_context_manager():
    """Test async context manager."""
    injector = StreamInjector()

    # Mock Redis client
    mock_client = AsyncMock()
    mock_client.ping = AsyncMock()
    mock_client.aclose = AsyncMock()

    with pytest.MonkeyPatch().context() as m:
        m.setattr('a2a.utils.stream_write.stream_injector.Redis.from_url', MagicMock(return_value=mock_client))

        async with injector as inj:
            assert inj is injector
            assert injector._connected

        assert not injector._connected


@pytest.mark.asyncio
async def test_stream_message():
    """Test streaming a message."""
    injector = StreamInjector()

    # Mock Redis client
    mock_client = AsyncMock()
    mock_client.xadd = AsyncMock(return_value='123-0')

    with pytest.MonkeyPatch().context() as m:
        m.setattr('a2a.utils.stream_write.stream_injector.Redis.from_url', MagicMock(return_value=mock_client))

        await injector.connect()

        # Test with dict message
        message = {
            'kind': 'message',
            'messageId': 'msg001',
            'parts': [{'kind': 'text', 'text': 'Hello!'}],
            'role': 'agent'
        }

        result = await injector.stream_message('ctx123', 'task456', message)

        assert result == '123-0'
        mock_client.xadd.assert_called_once()

        # Check the call arguments
        call_args = mock_client.xadd.call_args
        stream_key = call_args[0][0]
        event_data = call_args[0][1]

        assert stream_key == 'a2a:task:task456'
        assert event_data['type'] == 'Message'
        assert event_data['context_id'] == 'ctx123'
        assert event_data['task_id'] == 'task456'

        # Check payload is valid JSON
        payload = json.loads(event_data['payload'])
        assert payload == message


@pytest.mark.asyncio
async def test_update_status():
    """Test updating task status."""
    injector = StreamInjector()

    # Mock Redis client
    mock_client = AsyncMock()
    mock_client.xadd = AsyncMock(return_value='124-0')

    with pytest.MonkeyPatch().context() as m:
        m.setattr('a2a.utils.stream_write.stream_injector.Redis.from_url', MagicMock(return_value=mock_client))

        await injector.connect()

        # Test status update
        status = {'state': 'working', 'progress': 50}
        result = await injector.update_status('ctx123', 'task456', status)

        assert result == '124-0'

        # Check the call arguments
        call_args = mock_client.xadd.call_args
        event_data = call_args[0][1]

        assert event_data['type'] == 'TaskStatusUpdateEvent'
        payload = json.loads(event_data['payload'])
        assert payload == status


@pytest.mark.asyncio
async def test_final_message():
    """Test sending final message."""
    injector = StreamInjector()

    # Mock Redis client
    mock_client = AsyncMock()
    mock_client.xadd = AsyncMock(side_effect=['125-0', '126-0'])

    with pytest.MonkeyPatch().context() as m:
        m.setattr('a2a.utils.stream_write.stream_injector.Redis.from_url', MagicMock(return_value=mock_client))

        await injector.connect()

        # Test final message
        message = {
            'kind': 'message',
            'messageId': 'final001',
            'parts': [{'kind': 'text', 'text': 'Done!'}],
            'role': 'agent'
        }

        result = await injector.final_message('ctx123', 'task456', message)

        assert result == '125-0'

        # Should have made 2 calls (message + completion status)
        assert mock_client.xadd.call_count == 2


@pytest.mark.asyncio
async def test_append_raw():
    """Test appending raw event."""
    injector = StreamInjector()

    # Mock Redis client
    mock_client = AsyncMock()
    mock_client.xadd = AsyncMock(return_value='127-0')

    with pytest.MonkeyPatch().context() as m:
        m.setattr('a2a.utils.stream_write.stream_injector.Redis.from_url', MagicMock(return_value=mock_client))

        await injector.connect()

        # Test raw event
        result = await injector.append_raw('task456', 'CustomEvent', '{"data": "test"}')

        assert result == '127-0'

        # Check the call arguments
        call_args = mock_client.xadd.call_args
        event_data = call_args[0][1]

        assert event_data['type'] == 'CustomEvent'
        assert event_data['payload'] == '{"data": "test"}'


@pytest.mark.asyncio
async def test_get_latest_event():
    """Test getting latest event."""
    injector = StreamInjector()

    # Mock Redis client
    mock_client = AsyncMock()
    mock_client.xrevrange = AsyncMock(return_value=[('123-0', {'type': 'Message', 'payload': '{"test": "data"}'})])

    with pytest.MonkeyPatch().context() as m:
        m.setattr('a2a.utils.stream_write.stream_injector.Redis.from_url', MagicMock(return_value=mock_client))

        await injector.connect()

        # Test get latest event
        result = await injector.get_latest_event('task456')

        assert result is not None
        assert result['id'] == '123-0'
        assert result['type'] == 'Message'

        mock_client.xrevrange.assert_called_once_with('a2a:task:task456', '+', '-', count=1)


@pytest.mark.asyncio
async def test_get_events_since():
    """Test getting events since ID."""
    injector = StreamInjector()

    # Mock Redis client
    mock_client = AsyncMock()
    mock_client.xrange = AsyncMock(return_value=[
        ('123-0', {'type': 'Message', 'payload': '{"msg": "first"}'}),
        ('124-0', {'type': 'TaskStatusUpdateEvent', 'payload': '{"state": "working"}'})
    ])

    with pytest.MonkeyPatch().context() as m:
        m.setattr('a2a.utils.stream_write.stream_injector.Redis.from_url', MagicMock(return_value=mock_client))

        await injector.connect()

        # Test get events since
        result = await injector.get_events_since('task456', '122-0')

        assert len(result) == 2
        assert result[0]['id'] == '123-0'
        assert result[1]['id'] == '124-0'

        mock_client.xrange.assert_called_once_with('a2a:task:task456', '122-0', '+')


@pytest.mark.asyncio
async def test_not_connected_error():
    """Test error when not connected."""
    injector = StreamInjector()

    with pytest.raises(RuntimeError, match='Not connected to Redis'):
        await injector.stream_message('ctx', 'task', {})


@pytest.mark.asyncio
async def test_redis_import_error():
    """Test error when redis is not available."""
    with pytest.MonkeyPatch().context() as m:
        m.setattr('a2a.utils.stream_write.stream_injector.Redis', None)

        with pytest.raises(ImportError, match='redis package is required'):
            StreamInjector()
