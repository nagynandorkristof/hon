import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .descriptions.sensor import (
    SENSORS,
    HonConfigSensorEntityDescription,
    HonSensorEntityDescription,
)
from .entity import HonEntity
from .util import get_readable

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    entities = []
    entity: HonSensorEntity | HonConfigSensorEntity
    for device in hass.data[DOMAIN][entry.unique_id]["hon"].appliances:
        for description in SENSORS.get(device.appliance_type, []):
            if isinstance(description, HonSensorEntityDescription):
                if device.get(description.key) is None:
                    continue
                entity = HonSensorEntity(hass, entry, device, description)
            elif isinstance(description, HonConfigSensorEntityDescription):
                if description.key not in device.available_settings:
                    continue
                entity = HonConfigSensorEntity(hass, entry, device, description)
            else:
                continue
            entities.append(entity)

    async_add_entities(entities)


class HonSensorEntity(HonEntity, SensorEntity):
    entity_description: HonSensorEntityDescription

    @callback
    def _handle_coordinator_update(self, update: bool = True) -> None:
        value = self._device.get(self.entity_description.key, "")
        if self.entity_description.key == "programName":
            if not (options := self._device.settings.get("startProgram.program")):
                _LOGGER.debug("startProgram.program missing, keeping previous options")
                if update:
                    self.async_write_ha_state()
                return
            self._attr_options = options.values + ["No Program"]
        elif self.entity_description.option_list is not None:
            self._attr_options = list(self.entity_description.option_list.values())
            value = str(get_readable(self.entity_description, value))
        if not value and self.entity_description.state_class is not None:
            self._attr_native_value = 0
        self._attr_native_value = value
        if update:
            self.async_write_ha_state()


class HonConfigSensorEntity(HonEntity, SensorEntity):
    entity_description: HonConfigSensorEntityDescription

    @callback
    def _handle_coordinator_update(self, update: bool = True) -> None:
        sensor = self._device.settings.get(self.entity_description.key, None)
        value: float | str
        if self.entity_description.state_class is not None:
            if sensor and sensor.value:
                value = (
                    float(sensor.value)
                    if "." in str(sensor.value)
                    else int(sensor.value)
                )
            else:
                value = 0
        elif sensor is not None:
            value = sensor.value
        else:
            value = 0
        if self.entity_description.option_list is not None and not value == 0:
            self._attr_options = list(self.entity_description.option_list.values())
            value = get_readable(self.entity_description, value)
        self._attr_native_value = value
        if update:
            self.async_write_ha_state()
