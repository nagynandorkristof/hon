import logging
from typing import Any

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    SWING_OFF,
    SWING_BOTH,
    SWING_VERTICAL,
    SWING_HORIZONTAL,
    FAN_LOW,
    FAN_MEDIUM,
    FAN_HIGH,
    FAN_AUTO,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_TEMPERATURE,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .pyhon.appliance import HonAppliance
from .pyhon.parameter.range import HonParameterRange

from .const import DOMAIN
from .descriptions.climate import (
    CLIMATES,
    HonACClimateEntityDescription,
    HonClimateEntityDescription,
)
from .entity import HonEntity

_LOGGER = logging.getLogger(__name__)

HON_HVAC_MODE: dict[int, HVACMode] = {
    0: HVACMode.AUTO,
    1: HVACMode.COOL,
    2: HVACMode.DRY,
    3: HVACMode.DRY,
    4: HVACMode.HEAT,
    5: HVACMode.FAN_ONLY,
    6: HVACMode.FAN_ONLY,
}

HON_HVAC_PROGRAM: dict[str, str] = {
    HVACMode.AUTO: "iot_auto",
    HVACMode.COOL: "iot_cool",
    HVACMode.DRY: "iot_dry",
    HVACMode.HEAT: "iot_heat",
    HVACMode.FAN_ONLY: "iot_fan",
}

HON_FAN: dict[int, str] = {
    1: FAN_HIGH,
    2: FAN_MEDIUM,
    3: FAN_LOW,
    4: FAN_AUTO,
    5: FAN_AUTO,
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    entities = []
    entity: HonClimateEntity | HonACClimateEntity
    for device in hass.data[DOMAIN][entry.unique_id]["hon"].appliances:
        for description in CLIMATES.get(device.appliance_type, []):
            if isinstance(description, HonACClimateEntityDescription):
                if description.key not in list(device.commands):
                    continue
                entity = HonACClimateEntity(hass, entry, device, description)
            elif isinstance(description, HonClimateEntityDescription):
                if description.key not in device.available_settings:
                    continue
                entity = HonClimateEntity(hass, entry, device, description)
            else:
                continue  # type: ignore[unreachable]
            entities.append(entity)
    async_add_entities(entities)


class HonACClimateEntity(HonEntity, ClimateEntity):
    entity_description: HonACClimateEntityDescription
    _enable_turn_on_off_backwards_compatibility = False

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        device: HonAppliance,
        description: HonACClimateEntityDescription,
    ) -> None:
        super().__init__(hass, entry, device, description)

        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._set_temperature_bound()

        self._attr_hvac_modes = [HVACMode.OFF]
        for mode in device.settings["settings.machMode"].values:
            self._attr_hvac_modes.append(HON_HVAC_MODE[int(mode)])
        self._attr_preset_modes = []
        for mode in device.settings["startProgram.program"].values:
            self._attr_preset_modes.append(mode)
        self._attr_swing_modes = [
            SWING_OFF,
            SWING_VERTICAL,
            SWING_HORIZONTAL,
            SWING_BOTH,
        ]
        self._attr_supported_features = (
            ClimateEntityFeature.TURN_ON
            | ClimateEntityFeature.TURN_OFF
            | ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.FAN_MODE
            | ClimateEntityFeature.SWING_MODE
            | ClimateEntityFeature.PRESET_MODE
        )

        self._handle_coordinator_update(update=False)

    def _set_temperature_bound(self) -> None:
        temperature = self._device.settings["settings.tempSel"]
        if not isinstance(temperature, HonParameterRange):
            raise ValueError
        self._attr_max_temp = temperature.max
        self._attr_target_temperature_step = temperature.step
        self._attr_min_temp = temperature.min

    @property
    def target_temperature(self) -> float | None:
        """Return the temperature we try to reach."""
        return self._device.get("tempSel", 0.0)

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        return self._device.get("tempIndoor", 0.0)

    async def async_set_temperature(self, **kwargs: Any) -> None:
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is None:
            return
        self._device.settings["settings.tempSel"].value = str(int(temperature))
        await self._device.commands["settings"].send()
        self.async_write_ha_state()

    @property
    def hvac_mode(self) -> HVACMode:
        if self._device.get("onOffStatus") == 0:
            return HVACMode.OFF
        mode = self._device.get("machMode")
        if mode not in HON_HVAC_MODE:
            _LOGGER.warning("Unmapped machMode value %s, falling back to OFF", mode)
        return HON_HVAC_MODE.get(mode, HVACMode.OFF)

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        self._attr_hvac_mode = hvac_mode
        if hvac_mode == HVACMode.OFF:
            await self._device.commands["stopProgram"].send()
            # Only carry over the power state - stopProgram's other mandatory
            # parameters (machMode, tempSel, ...) are generic defaults, not
            # the user's actual settings, and would otherwise clobber them.
            self._device.sync_command("stopProgram", "settings", ["onOffStatus"])
        else:
            self._device.settings["settings.onOffStatus"].value = "1"
            setting = self._device.settings["settings.machMode"]
            modes = {HON_HVAC_MODE[int(number)]: number for number in setting.values}
            if hvac_mode in modes:
                setting.value = modes[hvac_mode]
            else:
                await self.async_set_preset_mode(HON_HVAC_PROGRAM[hvac_mode])
                return
            await self._device.commands["settings"].send()
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._device.commands["startProgram"].send()
        self._device.sync_command("startProgram", "settings", ["onOffStatus"])

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._device.commands["stopProgram"].send()
        self._device.sync_command("stopProgram", "settings", ["onOffStatus"])

    @property
    def preset_mode(self) -> str | None:
        """Return the current Preset for this channel."""
        return None

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the new preset mode."""
        if program := self._device.settings.get("startProgram.program"):
            program.value = preset_mode
        self._device.sync_command("startProgram", "settings")
        self._set_temperature_bound()
        self._handle_coordinator_update(update=False)
        self.coordinator.async_set_updated_data({})
        self._attr_preset_mode = preset_mode
        await self._device.commands["startProgram"].send()
        self.async_write_ha_state()

    @property
    def fan_modes(self) -> list[str]:
        """Return the list of available fan modes."""
        fan_modes = []
        for mode in reversed(self._device.settings["settings.windSpeed"].values):
            fan_modes.append(HON_FAN[int(mode)])
        return fan_modes

    @property
    def fan_mode(self) -> str | None:
        """Return the fan setting."""
        speed = self._device.get("windSpeed")
        if speed not in HON_FAN:
            _LOGGER.warning("Unmapped windSpeed value %s, falling back to auto", speed)
        return HON_FAN.get(speed, FAN_AUTO)

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        fan_modes = {}
        for mode in reversed(self._device.settings["settings.windSpeed"].values):
            fan_modes[HON_FAN[int(mode)]] = mode
        self._device.settings["settings.windSpeed"].value = str(fan_modes[fan_mode])
        self._attr_fan_mode = fan_mode
        await self._device.commands["settings"].send()
        self.async_write_ha_state()

    @property
    def swing_mode(self) -> str | None:
        """Return the swing setting."""
        horizontal = self._device.get("windDirectionHorizontal")
        vertical = self._device.get("windDirectionVertical")
        if horizontal == 7 and vertical == 8:
            return SWING_BOTH
        if horizontal == 7:
            return SWING_HORIZONTAL
        if vertical == 8:
            return SWING_VERTICAL
        return SWING_OFF

    async def async_set_swing_mode(self, swing_mode: str) -> None:
        horizontal = self._device.settings["settings.windDirectionHorizontal"]
        vertical = self._device.settings["settings.windDirectionVertical"]
        if swing_mode in [SWING_BOTH, SWING_HORIZONTAL]:
            horizontal.value = "7"
        if swing_mode in [SWING_BOTH, SWING_VERTICAL]:
            vertical.value = "8"
        if swing_mode in [SWING_OFF, SWING_HORIZONTAL] and vertical.value == "8":
            vertical.value = "5"
        if swing_mode in [SWING_OFF, SWING_VERTICAL] and horizontal.value == "7":
            horizontal.value = "0"
        self._attr_swing_mode = swing_mode
        await self._device.commands["settings"].send()
        self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self, update: bool = True) -> None:
        if update:
            self.async_write_ha_state()


class HonClimateEntity(HonEntity, ClimateEntity):
    entity_description: HonClimateEntityDescription
    _enable_turn_on_off_backwards_compatibility = False

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        device: HonAppliance,
        description: HonClimateEntityDescription,
    ) -> None:
        super().__init__(hass, entry, device, description)

        self._attr_supported_features = (
            ClimateEntityFeature.TURN_ON | ClimateEntityFeature.TARGET_TEMPERATURE
        )

        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._set_temperature_bound()

        self._attr_hvac_modes = [description.mode]
        if "stopProgram" in device.commands:
            self._attr_supported_features |= ClimateEntityFeature.TURN_OFF
            self._attr_hvac_modes += [HVACMode.OFF]
            modes = []
        else:
            modes = ["no_mode"]

        for mode, data in device.commands["startProgram"].categories.items():
            if mode not in data.parameters["program"].values:
                continue
            if (zone := data.parameters.get("zone")) and isinstance(
                self.entity_description.name, str
            ):
                if self.entity_description.name.lower() in zone.values:
                    modes.append(mode)
            else:
                modes.append(mode)

        if modes:
            self._attr_supported_features |= ClimateEntityFeature.PRESET_MODE
            self._attr_preset_modes = modes

        self._handle_coordinator_update(update=False)

    @property
    def target_temperature(self) -> float | None:
        """Return the temperature we try to reach."""
        return self._device.get(self.entity_description.key, 0.0)

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        temp_key = self.entity_description.key.split(".")[-1].replace("Sel", "")
        return self._device.get(temp_key, 0.0)

    async def async_set_temperature(self, **kwargs: Any) -> None:
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is None:
            return
        self._device.settings[self.entity_description.key].value = str(int(temperature))
        await self._device.commands["settings"].send()
        self.async_write_ha_state()

    @property
    def hvac_mode(self) -> HVACMode:
        if self._device.get("onOffStatus") == 0:
            return HVACMode.OFF
        else:
            return self.entity_description.mode

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        if len(self.hvac_modes) <= 1:
            return
        if hvac_mode == HVACMode.OFF:
            await self._device.commands["stopProgram"].send()
        else:
            await self._device.commands["startProgram"].send()
        self._attr_hvac_mode = hvac_mode
        self.async_write_ha_state()

    async def async_turn_on(self) -> None:
        """Set the HVAC State to on."""
        await self._device.commands["startProgram"].send()

    async def async_turn_off(self) -> None:
        """Set the HVAC State to off."""
        await self._device.commands["stopProgram"].send()

    @property
    def preset_mode(self) -> str | None:
        """Return the current Preset for this channel."""
        if self._device.get("onOffStatus") is not None:
            return self._device.get("programName", "")
        else:
            return self._device.get(
                f"mode{self.entity_description.key[-2:]}", "no_mode"
            )

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the new preset mode."""
        if preset_mode == "no_mode" and HVACMode.OFF in self.hvac_modes:
            command = "stopProgram"
        elif preset_mode == "no_mode":
            command = "settings"
            self._device.commands["settings"].reset()
        else:
            command = "startProgram"
        if program := self._device.settings.get(f"{command}.program"):
            program.value = preset_mode
        zone = self._device.settings.get(f"{command}.zone")
        if zone and isinstance(self.entity_description.name, str):
            zone.value = self.entity_description.name.lower()
        self._device.sync_command(command, "settings")
        self._set_temperature_bound()
        self._attr_preset_mode = preset_mode
        self.coordinator.async_set_updated_data({})
        await self._device.commands[command].send()
        self.async_write_ha_state()

    def _set_temperature_bound(self) -> None:
        temperature = self._device.settings[self.entity_description.key]
        if not isinstance(temperature, HonParameterRange):
            raise ValueError
        self._attr_max_temp = temperature.max
        self._attr_target_temperature_step = temperature.step
        self._attr_min_temp = temperature.min

    @callback
    def _handle_coordinator_update(self, update: bool = True) -> None:
        if update:
            self.async_write_ha_state()
