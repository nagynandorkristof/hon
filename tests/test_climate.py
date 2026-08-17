"""Regression tests for Phase 5: an out-of-range machMode/windSpeed value must
fall back to a documented default instead of raising KeyError.

Requires `homeassistant` (see requirements_dev.txt) - not runnable in an
environment without Home Assistant installed.
"""

from unittest.mock import MagicMock

import pytest

homeassistant = pytest.importorskip("homeassistant")

from homeassistant.components.climate.const import HVACMode  # noqa: E402
from homeassistant.const import FAN_AUTO  # noqa: E402

from custom_components.hon import climate  # noqa: E402


def _make_ac_entity(
    mach_mode: int | None, wind_speed: int | None
) -> climate.HonACClimateEntity:
    instance = object.__new__(climate.HonACClimateEntity)
    instance._device = MagicMock()
    instance._device.get.side_effect = lambda key, default=None: {
        "machMode": mach_mode,
        "windSpeed": wind_speed,
        "onOffStatus": 1,
    }.get(key, default)
    return instance


def test_hvac_mode_falls_back_on_unmapped_value() -> None:
    entity = _make_ac_entity(mach_mode=999, wind_speed=None)
    assert entity.hvac_mode == HVACMode.OFF


def test_hvac_mode_maps_known_value() -> None:
    entity = _make_ac_entity(mach_mode=1, wind_speed=None)
    assert entity.hvac_mode == HVACMode.COOL


def test_fan_mode_falls_back_on_unmapped_value() -> None:
    entity = _make_ac_entity(mach_mode=None, wind_speed=999)
    assert entity.fan_mode == FAN_AUTO


def test_fan_mode_maps_known_value() -> None:
    entity = _make_ac_entity(mach_mode=None, wind_speed=1)
    assert entity.fan_mode == "high"
