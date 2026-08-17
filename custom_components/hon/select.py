from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .descriptions.select import (
    SELECTS,
    HonConfigSelectEntityDescription,
    HonSelectEntityDescription,
)
from .entity import HonEntity
from .util import get_readable

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    entities = []
    entity: HonSelectEntity | HonConfigSelectEntity
    for device in hass.data[DOMAIN][entry.unique_id]["hon"].appliances:
        for description in SELECTS.get(device.appliance_type, []):
            if description.key not in device.available_settings:
                continue
            if isinstance(description, HonSelectEntityDescription):
                entity = HonSelectEntity(hass, entry, device, description)
            elif isinstance(description, HonConfigSelectEntityDescription):
                entity = HonConfigSelectEntity(hass, entry, device, description)
            else:
                continue
            entities.append(entity)
    async_add_entities(entities)


class HonConfigSelectEntity(HonEntity, SelectEntity):
    entity_description: HonConfigSelectEntityDescription

    @property
    def current_option(self) -> str | None:
        if not (setting := self._device.settings.get(self.entity_description.key)):
            return None
        value = get_readable(self.entity_description, setting.value)
        if value not in self._attr_options:
            return None
        return str(value)

    @property
    def options(self) -> list[str]:
        setting = self._device.settings.get(self.entity_description.key)
        if setting is None:
            return []
        return [
            str(get_readable(self.entity_description, key)) for key in setting.values
        ]

    def _option_to_number(self, option: str, values: list[str]) -> str:
        if (options := self.entity_description.option_list) is not None:
            return str(
                next(
                    (k for k, v in options.items() if str(k) in values and v == option),
                    option,
                )
            )
        return option

    async def async_select_option(self, option: str) -> None:
        setting = self._device.settings[self.entity_description.key]
        setting.value = self._option_to_number(option, setting.values)
        self.coordinator.async_set_updated_data({})

    @callback
    def _handle_coordinator_update(self, update: bool = True) -> None:
        self._attr_available = self.available
        self._attr_options = self.options
        self._attr_current_option = self.current_option
        if update:
            self.async_write_ha_state()

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._device.settings.get(self.entity_description.key) is not None


class HonSelectEntity(HonEntity, SelectEntity):
    entity_description: HonSelectEntityDescription

    @property
    def current_option(self) -> str | None:
        if not (setting := self._device.settings.get(self.entity_description.key)):
            return None
        value = get_readable(self.entity_description, setting.value)
        if value not in self._attr_options:
            return None
        return str(value)

    @property
    def options(self) -> list[str]:
        setting = self._device.settings.get(self.entity_description.key)
        if setting is None:
            return []
        return [
            str(get_readable(self.entity_description, key)) for key in setting.values
        ]

    def _option_to_number(self, option: str, values: list[str]) -> str:
        if (options := self.entity_description.option_list) is not None:
            return str(
                next(
                    (k for k, v in options.items() if str(k) in values and v == option),
                    option,
                )
            )
        return option

    async def async_select_option(self, option: str) -> None:
        setting = self._device.settings[self.entity_description.key]
        setting.value = self._option_to_number(option, setting.values)
        command = self.entity_description.key.split(".")[0]
        await self._device.commands[command].send()
        if command != "settings":
            self._device.sync_command(command, "settings")
        self.coordinator.async_set_updated_data({})

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            super().available
            and int(self._device.get("remoteCtrValid", 1)) == 1
            and self._device.connection
        )

    @callback
    def _handle_coordinator_update(self, update: bool = True) -> None:
        self._attr_available = self.available
        self._attr_options = self.options
        self._attr_current_option = self.current_option
        if update:
            self.async_write_ha_state()
