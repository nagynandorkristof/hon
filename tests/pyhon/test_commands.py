from unittest.mock import AsyncMock, MagicMock

import pytest

from pyhon.commands import HonCommand
from pyhon.exceptions import ApiError, HonConnectionError


def _make_command() -> tuple[HonCommand, MagicMock]:
    appliance = MagicMock()
    command = HonCommand("settings", {}, appliance)
    api = MagicMock()
    api.send_command = AsyncMock()
    command._api = api
    return command, api


@pytest.mark.asyncio
async def test_send_parameters_returns_false_on_connection_error() -> None:
    """HonConnectionError is what api.send_command raises once the network
    layer (Phase 1) wraps aiohttp.ClientError/TimeoutError; send_parameters
    must swallow it and return False, same contract as NoAuthenticationException."""
    command, api = _make_command()
    api.send_command.side_effect = HonConnectionError("boom")

    result = await command.send_parameters({})

    assert result is False


@pytest.mark.asyncio
async def test_send_parameters_reraises_api_error() -> None:
    command, api = _make_command()
    api.send_command.return_value = False

    with pytest.raises(ApiError):
        await command.send_parameters({})
