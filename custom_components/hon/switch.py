import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .pyhon.parameter.base import HonParameter
from .pyhon.parameter.range import HonParameterRange

from .const import DOMAIN
from .descriptions.switch import (
    SWITCHES,
    HonConfigSwitchEntityDescription,
    HonControlSwitchEntityDescription,
    HonSwitchEntityDescription,
)
from .entity import HonEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    entities = []
    entity: HonConfigSwitchEntity | HonControlSwitchEntity | HonSwitchEntity
    for device in hass.data[DOMAIN][entry.unique_id]["hon"].appliances:
        for description in SWITCHES.get(device.appliance_type, []):
            if isinstance(description, HonConfigSwitchEntityDescription):
                if description.key not in device.available_settings:
                    continue
                entity = HonConfigSwitchEntity(hass, entry, device, description)
            elif isinstance(description, HonControlSwitchEntityDescription):
                if not (
                    device.get(description.key) is not None
                    or description.turn_on_key in list(device.commands)
                    or description.turn_off_key in list(device.commands)
                ):
                    continue
                entity = HonControlSwitchEntity(hass, entry, device, description)
            elif isinstance(description, HonSwitchEntityDescription):
                if f"settings.{description.key}" not in device.available_settings:
                    continue
                entity = HonSwitchEntity(hass, entry, device, description)
            else:
                continue
            entities.append(entity)

    async_add_entities(entities)


class HonSwitchEntity(HonEntity, SwitchEntity):
    entity_description: HonSwitchEntityDescription

    @property
    def is_on(self) -> bool | None:
        """Return True if entity is on."""
        return self._device.get(self.entity_description.key, 0) == 1

    async def async_turn_on(self, **kwargs: Any) -> None:
        setting = self._device.settings[f"settings.{self.entity_description.key}"]
        if type(setting) == HonParameter:
            return
        setting.value = setting.max if isinstance(setting, HonParameterRange) else 1
        self.async_write_ha_state()
        await self._device.commands["settings"].send()
        self.coordinator.async_set_updated_data({})

    async def async_turn_off(self, **kwargs: Any) -> None:
        setting = self._device.settings[f"settings.{self.entity_description.key}"]
        if type(setting) == HonParameter:
            return
        setting.value = setting.min if isinstance(setting, HonParameterRange) else 0
        self.async_write_ha_state()
        await self._device.commands["settings"].send()
        self.coordinator.async_set_updated_data({})

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        if not super().available:
            return False
        if not self._device.get("remoteCtrValid", 1) == 1:
            return False
        if self._device.get("attributes.lastConnEvent.category") == "DISCONNECTED":
            return False
        setting = self._device.settings.get(f"settings.{self.entity_description.key}")
        if isinstance(setting, HonParameterRange) and len(setting.values) < 2:
            return False
        return True

    @callback
    def _handle_coordinator_update(self, update: bool = True) -> None:
        self._attr_is_on = self.is_on
        if update:
            self.async_write_ha_state()


class HonControlSwitchEntity(HonEntity, SwitchEntity):
    entity_description: HonControlSwitchEntityDescription

    @property
    def is_on(self) -> bool | None:
        """Return True if entity is on."""
        return self._device.get(self.entity_description.key, False)

    async def async_turn_on(self, **kwargs: Any) -> None:
        self._device.sync_command(self.entity_description.turn_on_key, "settings")
        self.coordinator.async_set_updated_data({})
        await self._device.commands[self.entity_description.turn_on_key].send()
        self._device.attributes[self.entity_description.key] = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        self._device.sync_command(self.entity_description.turn_off_key, "settings")
        self.coordinator.async_set_updated_data({})
        await self._device.commands[self.entity_description.turn_off_key].send()
        self._device.attributes[self.entity_description.key] = False
        self.async_write_ha_state()

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            super().available
            and int(self._device.get("remoteCtrValid", 1)) == 1
            and self._device.connection
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the optional state attributes."""
        result = {}
        if remaining_time := self._device.get("remainingTimeMM", 0):
            delay_time = self._device.get("delayTime", 0)
            result["start_time"] = datetime.now() + timedelta(minutes=delay_time)
            result["end_time"] = datetime.now() + timedelta(
                minutes=delay_time + remaining_time
            )
        return result


class HonConfigSwitchEntity(HonEntity, SwitchEntity):
    entity_description: HonConfigSwitchEntityDescription

    @property
    def is_on(self) -> bool | None:
        """Return True if entity is on."""
        setting = self._device.settings[self.entity_description.key]
        return (
            setting.value != setting.min
            if hasattr(setting, "min")
            else setting.value == "1"
        )

    async def async_turn_on(self, **kwargs: Any) -> None:
        setting = self._device.settings[self.entity_description.key]
        if type(setting) == HonParameter:
            return
        setting.value = setting.max if isinstance(setting, HonParameterRange) else "1"
        self.coordinator.async_set_updated_data({})
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        setting = self._device.settings[self.entity_description.key]
        if type(setting) == HonParameter:
            return
        setting.value = setting.min if isinstance(setting, HonParameterRange) else "0"
        self.coordinator.async_set_updated_data({})
        self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self, update: bool = True) -> None:
        self._attr_is_on = self.is_on
        if update:
            self.async_write_ha_state()
