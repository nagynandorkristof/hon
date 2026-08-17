"""Regression tests for Phase 3: async_setup_entry must translate pyhon
exceptions into the HA-standard ConfigEntryAuthFailed/ConfigEntryNotReady
instead of letting a raw exception crash setup.

Requires `homeassistant` (see requirements_dev.txt) - not runnable in an
environment without Home Assistant installed.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

homeassistant = pytest.importorskip("homeassistant")

from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady  # noqa: E402

from custom_components import hon  # noqa: E402
from custom_components.hon.pyhon.exceptions import (  # noqa: E402
    HonAuthenticationError,
    HonConnectionError,
)


def _make_hass_and_entry() -> tuple[MagicMock, MagicMock]:
    hass = MagicMock()
    hass.config.config_dir = "/config"
    hass.data = {}
    entry = MagicMock()
    entry.data = {"email": "a@b.com", "password": "secret"}
    entry.unique_id = "a@b.com"
    return hass, entry


@pytest.mark.asyncio
async def test_setup_entry_raises_auth_failed_on_authentication_error() -> None:
    hass, entry = _make_hass_and_entry()
    with patch.object(
        hon.Hon, "create", AsyncMock(side_effect=HonAuthenticationError())
    ):
        with pytest.raises(ConfigEntryAuthFailed):
            await hon.async_setup_entry(hass, entry)


@pytest.mark.asyncio
async def test_setup_entry_raises_not_ready_on_connection_error() -> None:
    hass, entry = _make_hass_and_entry()
    with patch.object(
        hon.Hon, "create", AsyncMock(side_effect=HonConnectionError())
    ):
        with pytest.raises(ConfigEntryNotReady):
            await hon.async_setup_entry(hass, entry)


@pytest.mark.asyncio
async def test_unload_entry_does_not_raise_when_never_set_up() -> None:
    hass = MagicMock()
    hass.data = {}
    entry = MagicMock()
    entry.unique_id = "never-set-up"

    result = await hon.async_unload_entry(hass, entry)

    assert result is True
