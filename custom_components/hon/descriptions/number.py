from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import NumberEntityDescription
from homeassistant.const import UnitOfTime, UnitOfTemperature
from homeassistant.helpers.entity import EntityCategory

from ..util import unique_entities


@dataclass(frozen=True)
class HonConfigNumberEntityDescription(NumberEntityDescription):
    entity_category: EntityCategory = EntityCategory.CONFIG


@dataclass(frozen=True)
class HonNumberEntityDescription(NumberEntityDescription):
    pass


NUMBERS: dict[str, tuple[NumberEntityDescription, ...]] = {
    "WM": (
        HonConfigNumberEntityDescription(
            key="startProgram.delayTime",
            name="Delay Time",
            icon="mdi:timer-plus",
            native_unit_of_measurement=UnitOfTime.MINUTES,
            translation_key="delay_time",
        ),
        HonConfigNumberEntityDescription(
            key="startProgram.rinseIterations",
            name="Rinse Iterations",
            icon="mdi:rotate-right",
            translation_key="rinse_iterations",
        ),
        HonConfigNumberEntityDescription(
            key="startProgram.mainWashTime",
            name="Main Wash Time",
            icon="mdi:clock-start",
            native_unit_of_measurement=UnitOfTime.MINUTES,
            translation_key="wash_time",
        ),
        HonConfigNumberEntityDescription(
            key="startProgram.waterHard",
            name="Water hard",
            icon="mdi:water",
            translation_key="water_hard",
        ),
        HonNumberEntityDescription(
            key="settings.waterHard",
            name="Water hard",
            icon="mdi:water",
            translation_key="water_hard",
        ),
        HonConfigNumberEntityDescription(
            key="startProgram.lang",
            name="lang",
        ),
    ),
    "TD": (
        HonConfigNumberEntityDescription(
            key="startProgram.delayTime",
            name="Delay time",
            icon="mdi:timer-plus",
            native_unit_of_measurement=UnitOfTime.MINUTES,
            translation_key="delay_time",
        ),
        HonConfigNumberEntityDescription(
            key="startProgram.tempLevel",
            name="Temperature level",
            icon="mdi:thermometer",
            translation_key="tumbledryertemplevel",
        ),
        HonConfigNumberEntityDescription(
            key="startProgram.dryTime",
            name="Dry Time",
            translation_key="dry_time",
        ),
    ),
    "OV": (
        HonConfigNumberEntityDescription(
            key="startProgram.delayTime",
            name="Delay time",
            icon="mdi:timer-plus",
            native_unit_of_measurement=UnitOfTime.MINUTES,
            translation_key="delay_time",
        ),
        HonConfigNumberEntityDescription(
            key="startProgram.tempSel",
            name="Target Temperature",
            icon="mdi:thermometer",
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            translation_key="target_temperature",
        ),
        HonConfigNumberEntityDescription(
            key="startProgram.prTime",
            name="Program Duration",
            icon="mdi:timelapse",
            native_unit_of_measurement=UnitOfTime.MINUTES,
            translation_key="program_duration",
        ),
    ),
    "IH": (
        HonConfigNumberEntityDescription(
            key="startProgram.temp",
            name="Temperature",
            icon="mdi:thermometer",
            translation_key="temperature",
        ),
        HonConfigNumberEntityDescription(
            key="startProgram.powerManagement",
            name="Power Management",
            icon="mdi:timelapse",
            translation_key="power_management",
        ),
    ),
    "DW": (
        HonConfigNumberEntityDescription(
            key="startProgram.delayTime",
            name="Delay time",
            icon="mdi:timer-plus",
            native_unit_of_measurement=UnitOfTime.MINUTES,
            translation_key="delay_time",
        ),
        HonConfigNumberEntityDescription(
            key="startProgram.waterHard",
            name="Water hard",
            icon="mdi:water",
            translation_key="water_hard",
        ),
        HonNumberEntityDescription(
            key="settings.waterHard",
            name="Water hard",
            icon="mdi:water",
            translation_key="water_hard",
        ),
    ),
    "AC": (
        HonNumberEntityDescription(
            key="settings.tempSel",
            name="Target Temperature",
            icon="mdi:thermometer",
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            translation_key="target_temperature",
        ),
    ),
    "REF": (
        HonNumberEntityDescription(
            key="settings.tempSelZ1",
            name="Fridge Temperature",
            icon="mdi:thermometer",
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            translation_key="fridge_temp_sel",
        ),
        HonNumberEntityDescription(
            key="settings.tempSelZ2",
            name="Freezer Temperature",
            icon="mdi:thermometer",
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            translation_key="freezer_temp_sel",
        ),
        HonNumberEntityDescription(
            key="settings.tempSelZ3",
            name="MyZone Temperature",
            icon="mdi:thermometer",
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            translation_key="my_zone_temp_sel",
        ),
    ),
    "AP": (
        HonNumberEntityDescription(
            key="settings.aromaTimeOn",
            name="Aroma Time On",
            icon="mdi:scent",
            native_unit_of_measurement=UnitOfTime.SECONDS,
            translation_key="aroma_time_on",
        ),
        HonNumberEntityDescription(
            key="settings.aromaTimeOff",
            name="Aroma Time Off",
            icon="mdi:scent-off",
            native_unit_of_measurement=UnitOfTime.SECONDS,
            translation_key="aroma_time_off",
        ),
        HonNumberEntityDescription(
            key="settings.pollenLevel",
            name="Pollen Level",
            icon="mdi:flower-pollen",
            translation_key="pollen_level",
        ),
    ),
}

NUMBERS["WD"] = unique_entities(NUMBERS["WM"], NUMBERS["TD"])
