import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from pyhon.connection.mqtt import MQTTClient


def _make_client() -> MQTTClient:
    client = object.__new__(MQTTClient)
    client._hon = MagicMock(appliances=[])
    client._connection = False
    return client


@pytest.mark.asyncio
async def test_watchdog_survives_failed_restart(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failed reconnect attempt must be logged and retried on the next
    tick, not silently end the watchdog task (Phase 1 task 5)."""
    client = _make_client()
    client._start = AsyncMock(side_effect=RuntimeError("boom"))  # type: ignore[method-assign]
    client._subscribe_appliances = MagicMock()  # type: ignore[method-assign]

    call_count = 0

    async def fake_sleep(_delay: float) -> None:
        nonlocal call_count
        call_count += 1
        if call_count >= 2:
            raise asyncio.CancelledError()

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    with pytest.raises(asyncio.CancelledError):
        await client._watchdog()

    assert client._start.await_count == 1
    assert call_count == 2


def test_on_publish_received_swallows_malformed_payload() -> None:
    """A malformed publish payload must not raise out of the mqtt callback
    (Phase 1 task 6)."""
    client = _make_client()
    data = MagicMock()
    data.publish_packet.payload = b"{not valid json"

    client._on_publish_received(data)  # should not raise


def test_on_publish_received_ignores_unknown_appliance() -> None:
    """A topic that doesn't match any known appliance must be ignored
    instead of raising StopIteration (Phase 1 task 6)."""
    client = _make_client()
    data = MagicMock()
    data.publish_packet.payload = b'{"parameters": []}'
    data.publish_packet.topic = "unknown/topic"

    client._on_publish_received(data)  # should not raise
