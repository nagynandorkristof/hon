"""Regression tests for Phase 6: wrong credentials must produce a form error
(not an unhandled exception), and the reauth flow must update the existing
config entry rather than requiring delete-and-recreate.

Requires `homeassistant` (see requirements_dev.txt) - not runnable in an
environment without Home Assistant installed.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

homeassistant = pytest.importorskip("homeassistant")

from custom_components.hon.config_flow import HonFlowHandler  # noqa: E402
from custom_components.hon.pyhon.exceptions import (  # noqa: E402
    HonAuthenticationError,
    HonConnectionError,
)


def _make_flow() -> HonFlowHandler:
    flow = HonFlowHandler()
    flow.hass = MagicMock()
    return flow


@pytest.mark.asyncio
async def test_user_step_shows_invalid_auth_error() -> None:
    flow = _make_flow()
    with patch(
        "custom_components.hon.config_flow.Hon.create",
        AsyncMock(side_effect=HonAuthenticationError()),
    ):
        result = await flow.async_step_user({"email": "a@b.com", "password": "wrong"})

    assert result["type"] == "form"
    assert result["errors"]["base"] == "invalid_auth"


@pytest.mark.asyncio
async def test_user_step_shows_cannot_connect_error() -> None:
    flow = _make_flow()
    with patch(
        "custom_components.hon.config_flow.Hon.create",
        AsyncMock(side_effect=HonConnectionError()),
    ):
        result = await flow.async_step_user({"email": "a@b.com", "password": "secret"})

    assert result["type"] == "form"
    assert result["errors"]["base"] == "cannot_connect"


@pytest.mark.asyncio
async def test_reauth_confirm_updates_existing_entry() -> None:
    flow = _make_flow()
    flow._email = "a@b.com"
    reauth_entry = MagicMock()
    reauth_entry.data = {"email": "a@b.com", "password": "old"}
    flow._reauth_entry = reauth_entry
    flow.hass.config_entries.async_reload = AsyncMock()

    with patch(
        "custom_components.hon.config_flow.Hon.create",
        AsyncMock(return_value=MagicMock()),
    ):
        result = await flow.async_step_reauth_confirm({"password": "new"})

    flow.hass.config_entries.async_update_entry.assert_called_once()
    flow.hass.config_entries.async_reload.assert_awaited_once()
    assert result["type"] == "abort"
    assert result["reason"] == "reauth_successful"
