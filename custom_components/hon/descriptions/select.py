from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.select import SelectEntityDescription
from homeassistant.const import UnitOfTemperature, UnitOfTime, REVOLUTIONS_PER_MINUTE
from homeassistant.helpers.entity import EntityCategory

from ..util import unique_entities

DIRTY_LEVEL: dict[int, str] = {
    0: "unknown",
    1: "little",
    2: "normal",
    3: "very",
}

STEAM_LEVEL: dict[int, str] = {
    0: "no_steam",
    1: "cotton",
    2: "delicate",
    3: "synthetic",
}

TUMBLE_DRYER_DRY_LEVEL: dict[int, str] = {
    0: "no_dry",
    1: "iron_dry",
    2: "no_dry_iron",
    3: "cupboard_dry",
    4: "extra_dry",
    11: "no_dry",
    12: "iron_dry",
    13: "cupboard_dry",
    14: "ready_to_wear",
    15: "extra_dry",
}

AC_HUMAN_SENSE: dict[int, str] = {
    0: "touch_off",
    1: "avoid_touch",
    2: "follow_touch",
    3: "unknown",
}

AP_MACH_MODE: dict[int, str] = {
    0: "standby",
    1: "sleep",
    2: "auto",
    3: "allergens",
    4: "max",
}

AP_DIFFUSER_LEVEL: dict[int, str] = {
    0: "off",
    1: "soft",
    2: "mid",
    3: "h_biotics",
    4: "custom",
}

AC_POSITION_HORIZONTAL = {
    0: "position_1",
    3: "position_2",
    4: "position_3",
    5: "position_4",
    6: "position_5",
    7: "swing",
}

AC_POSITION_VERTICAL = {
    2: "position_1",
    4: "position_2",
    5: "position_3",
    6: "position_4",
    7: "position_5",
    8: "swing",
}


@dataclass(frozen=True)
class HonSelectEntityDescription(SelectEntityDescription):
    option_list: dict[int, str] | None = None


@dataclass(frozen=True)
class HonConfigSelectEntityDescription(SelectEntityDescription):
    entity_category: EntityCategory = EntityCategory.CONFIG
    option_list: dict[int, str] | None = None


SELECTS: dict[str, tuple[SelectEntityDescription, ...]] = {
    "WM": (
        HonConfigSelectEntityDescription(
            key="startProgram.spinSpeed",
            name="Spin speed",
            icon="mdi:numeric",
            unit_of_measurement=REVOLUTIONS_PER_MINUTE,
            translation_key="spin_speed",
        ),
        HonConfigSelectEntityDescription(
            key="startProgram.temp",
            name="Temperature",
            icon="mdi:thermometer",
            unit_of_measurement=UnitOfTemperature.CELSIUS,
            translation_key="temperature",
        ),
        HonConfigSelectEntityDescription(
            key="startProgram.program",
            name="Program",
            translation_key="programs_wm",
        ),
        HonConfigSelectEntityDescription(
            key="startProgram.steamLevel",
            name="Steam level",
            icon="mdi:weather-dust",
            translation_key="steam_level",
            option_list=STEAM_LEVEL,
        ),
        HonConfigSelectEntityDescription(
            key="startProgram.dirtyLevel",
            name="Dirty level",
            icon="mdi:liquid-spot",
            translation_key="dirt_level",
            option_list=DIRTY_LEVEL,
        ),
        HonConfigSelectEntityDescription(
            key="startProgram.extendedStainType",
            name="Stain Type",
            icon="mdi:liquid-spot",
            translation_key="stain_type",
        ),
    ),
    "TD": (
        HonConfigSelectEntityDescription(
            key="startProgram.program",
            name="Program",
            translation_key="programs_td",
        ),
        HonConfigSelectEntityDescription(
            key="startProgram.dryTimeMM",
            name="Dry Time",
            icon="mdi:timer",
            unit_of_measurement=UnitOfTime.MINUTES,
            translation_key="dry_time",
        ),
        HonConfigSelectEntityDescription(
            key="startProgram.dryLevel",
            name="Dry level",
            icon="mdi:hair-dryer",
            translation_key="dry_levels",
            option_list=TUMBLE_DRYER_DRY_LEVEL,
        ),
    ),
    "OV": (
        HonConfigSelectEntityDescription(
            key="startProgram.program",
            name="Program",
            translation_key="programs_ov",
        ),
    ),
    "IH": (
        HonConfigSelectEntityDescription(
            key="startProgram.program",
            name="Program",
            translation_key="programs_ih",
        ),
    ),
    "DW": (
        HonConfigSelectEntityDescription(
            key="startProgram.program",
            name="Program",
            translation_key="programs_dw",
        ),
        HonConfigSelectEntityDescription(
            key="startProgram.temp",
            name="Temperature",
            icon="mdi:thermometer",
            unit_of_measurement=UnitOfTemperature.CELSIUS,
            translation_key="temperature",
        ),
        HonConfigSelectEntityDescription(
            key="startProgram.remainingTime",
            name="Remaining Time",
            icon="mdi:timer",
            unit_of_measurement=UnitOfTime.MINUTES,
            translation_key="remaining_time",
        ),
    ),
    "AC": (
        HonSelectEntityDescription(
            key="startProgram.program",
            name="Program",
            translation_key="programs_ac",
        ),
        HonSelectEntityDescription(
            key="settings.humanSensingStatus",
            name="Eco Pilot",
            icon="mdi:run",
            translation_key="eco_pilot",
            option_list=AC_HUMAN_SENSE,
        ),
        HonSelectEntityDescription(
            key="settings.windDirectionHorizontal",
            name="Fan Direction Horizontal",
            icon="mdi:fan",
            translation_key="fan_horizontal",
            option_list=AC_POSITION_HORIZONTAL,
        ),
        HonSelectEntityDescription(
            key="settings.windDirectionVertical",
            name="Fan Direction Vertical",
            icon="mdi:fan",
            translation_key="fan_vertical",
            option_list=AC_POSITION_VERTICAL,
        ),
    ),
    "REF": (
        HonConfigSelectEntityDescription(
            key="startProgram.program",
            name="Program",
            translation_key="programs_ref",
        ),
        HonConfigSelectEntityDescription(
            key="startProgram.zone",
            name="Zone",
            icon="mdi:radiobox-marked",
            translation_key="ref_zones",
        ),
    ),
    "AP": (
        HonSelectEntityDescription(
            key="settings.aromaStatus",
            name="Diffuser Level",
            option_list=AP_DIFFUSER_LEVEL,
            translation_key="diffuser",
            icon="mdi:air-purifier",
        ),
        HonSelectEntityDescription(
            key="settings.machMode",
            name="Mode",
            icon="mdi:play",
            option_list=AP_MACH_MODE,
            translation_key="mode",
        ),
    ),
    "FRE": (
        HonConfigSelectEntityDescription(
            key="startProgram.program",
            name="Program",
            translation_key="programs_ref",
        ),
        HonConfigSelectEntityDescription(
            key="startProgram.zone",
            name="Zone",
            icon="mdi:radiobox-marked",
            translation_key="ref_zones",
        ),
        HonSelectEntityDescription(
            key="settings.tempSelZ3",
            name="Temperature",
            icon="mdi:thermometer",
            unit_of_measurement=UnitOfTemperature.CELSIUS,
            translation_key="temperature",
        ),
    ),
}

SELECTS["WD"] = unique_entities(SELECTS["WM"], SELECTS["TD"])
