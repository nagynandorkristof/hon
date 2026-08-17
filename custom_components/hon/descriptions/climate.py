from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.climate import ClimateEntityDescription
from homeassistant.components.climate.const import HVACMode


@dataclass(frozen=True)
class HonACClimateEntityDescription(ClimateEntityDescription):
    pass


@dataclass(frozen=True)
class HonClimateEntityDescription(ClimateEntityDescription):
    mode: HVACMode = HVACMode.AUTO


CLIMATES: dict[
    str, tuple[HonACClimateEntityDescription | HonClimateEntityDescription, ...]
] = {
    "AC": (
        HonACClimateEntityDescription(
            key="settings",
            name="Air Conditioner",
            icon="mdi:air-conditioner",
            translation_key="air_conditioner",
        ),
    ),
    "REF": (
        HonClimateEntityDescription(
            key="settings.tempSelZ1",
            mode=HVACMode.COOL,
            name="Fridge",
            icon="mdi:thermometer",
            translation_key="fridge",
        ),
        HonClimateEntityDescription(
            key="settings.tempSelZ2",
            mode=HVACMode.COOL,
            name="Freezer",
            icon="mdi:snowflake-thermometer",
            translation_key="freezer",
        ),
        HonClimateEntityDescription(
            key="settings.tempSelZ3",
            mode=HVACMode.COOL,
            name="MyZone",
            icon="mdi:thermometer",
            translation_key="my_zone",
        ),
    ),
    "OV": (
        HonClimateEntityDescription(
            key="settings.tempSel",
            mode=HVACMode.HEAT,
            name="Oven",
            icon="mdi:thermometer",
            translation_key="oven",
        ),
    ),
    "WC": (
        HonClimateEntityDescription(
            key="settings.tempSel",
            mode=HVACMode.COOL,
            name="Wine Cellar",
            icon="mdi:thermometer",
            translation_key="wine",
        ),
        HonClimateEntityDescription(
            key="settings.tempSelZ2",
            mode=HVACMode.COOL,
            name="Wine Cellar",
            icon="mdi:thermometer",
            translation_key="wine",
        ),
    ),
}
