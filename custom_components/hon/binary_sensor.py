import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .descriptions.binary_sensor import BINARY_SENSORS, HonBinarySensorEntityDescription
from .entity import HonEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    entities = []
    for device in hass.data[DOMAIN][entry.unique_id]["hon"].appliances:
        for description in BINARY_SENSORS.get(device.appliance_type, []):
            if device.get(description.key) is None:
                continue
            entity = HonBinarySensorEntity(hass, entry, device, description)
            entities.append(entity)
    async_add_entities(entities)


class HonBinarySensorEntity(HonEntity, BinarySensorEntity):
    entity_description: HonBinarySensorEntityDescription

    @property
    def is_on(self) -> bool:
        return bool(
            self._device.get(self.entity_description.key, "")
            == self.entity_description.on_value
        )

    @callback
    def _handle_coordinator_update(self, update: bool = True) -> None:
        self._attr_native_value = (
            self._device.get(self.entity_description.key, "")
            == self.entity_description.on_value
        )
        if update:
            self.async_write_ha_state()
