from __future__ import annotations

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .pyhon.appliance import HonAppliance
from .pyhon.parameter.range import HonParameterRange

from .const import DOMAIN
from .descriptions.number import (
    NUMBERS,
    HonConfigNumberEntityDescription,
    HonNumberEntityDescription,
)
from .entity import HonEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    entities = []
    entity: HonNumberEntity | HonConfigNumberEntity
    for device in hass.data[DOMAIN][entry.unique_id]["hon"].appliances:
        for description in NUMBERS.get(device.appliance_type, []):
            if description.key not in device.available_settings:
                continue
            if isinstance(description, HonNumberEntityDescription):
                entity = HonNumberEntity(hass, entry, device, description)
            elif isinstance(description, HonConfigNumberEntityDescription):
                entity = HonConfigNumberEntity(hass, entry, device, description)
            else:
                continue
            entities.append(entity)
    async_add_entities(entities)


class HonNumberEntity(HonEntity, NumberEntity):
    entity_description: HonNumberEntityDescription

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        device: HonAppliance,
        description: HonNumberEntityDescription,
    ) -> None:
        super().__init__(hass, entry, device, description)

        self._data = device.settings[description.key]
        if isinstance(self._data, HonParameterRange):
            self._attr_native_max_value = self._data.max
            self._attr_native_min_value = self._data.min
            self._attr_native_step = self._data.step

    @property
    def native_value(self) -> float | None:
        if value := self._device.get(self.entity_description.key.split(".")[-1]):
            return float(value)
        return None

    async def async_set_native_value(self, value: float) -> None:
        setting = self._device.settings[self.entity_description.key]
        if isinstance(setting, HonParameterRange):
            setting.value = value
        command = self.entity_description.key.split(".")[0]
        await self._device.commands[command].send()
        if command != "settings":
            self._device.sync_command(command, "settings")
        self.coordinator.async_set_updated_data({})

    @callback
    def _handle_coordinator_update(self, update: bool = True) -> None:
        setting = self._device.settings.get(self.entity_description.key)
        if isinstance(setting, HonParameterRange):
            self._attr_native_max_value = setting.max
            self._attr_native_min_value = setting.min
            self._attr_native_step = setting.step
        self._attr_native_value = self.native_value
        if update:
            self.async_write_ha_state()

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            super().available
            and int(self._device.get("remoteCtrValid", 1)) == 1
            and self._device.connection
        )


class HonConfigNumberEntity(HonEntity, NumberEntity):
    entity_description: HonConfigNumberEntityDescription

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        device: HonAppliance,
        description: HonConfigNumberEntityDescription,
    ) -> None:
        super().__init__(hass, entry, device, description)

        self._data = device.settings[description.key]
        if isinstance(self._data, HonParameterRange):
            self._attr_native_max_value = self._data.max
            self._attr_native_min_value = self._data.min
            self._attr_native_step = self._data.step

    @property
    def native_value(self) -> float | None:
        setting = self._device.settings.get(self.entity_description.key)
        if setting is not None and (value := setting.value) != "":
            return float(value)
        return None

    async def async_set_native_value(self, value: float) -> None:
        setting = self._device.settings[self.entity_description.key]
        if isinstance(setting, HonParameterRange):
            setting.value = value
        self.coordinator.async_set_updated_data({})

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return super(NumberEntity, self).available

    @callback
    def _handle_coordinator_update(self, update: bool = True) -> None:
        setting = self._device.settings.get(self.entity_description.key)
        if isinstance(setting, HonParameterRange):
            self._attr_native_max_value = setting.max
            self._attr_native_min_value = setting.min
            self._attr_native_step = setting.step
        self._attr_native_value = self.native_value
        if update:
            self.async_write_ha_state()
