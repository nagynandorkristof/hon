"""Regression tests for Phase 4: HonEntity.available must reflect device
connectivity for every platform, including sensor/binary_sensor/climate which
previously had no availability handling at all and were always-available.

Requires `homeassistant` (see requirements_dev.txt) - not runnable in an
environment without Home Assistant installed.
"""

from unittest.mock import MagicMock

import pytest

homeassistant = pytest.importorskip("homeassistant")

from custom_components.hon import binary_sensor, climate, entity, sensor  # noqa: E402


class _FakeCoordinator:
    last_update_success = True


def _make_entity(entity_cls: type, connection: bool) -> entity.HonEntity:
    instance = object.__new__(entity_cls)
    instance.coordinator = _FakeCoordinator()
    instance._device = MagicMock(connection=connection, unique_id="abc")
    return instance


@pytest.mark.parametrize(
    "entity_cls",
    [
        entity.HonEntity,
        sensor.HonSensorEntity,
        binary_sensor.HonBinarySensorEntity,
        climate.HonClimateEntity,
    ],
)
def test_available_reflects_device_connection(entity_cls: type) -> None:
    assert _make_entity(entity_cls, True).available is True
    assert _make_entity(entity_cls, False).available is False
