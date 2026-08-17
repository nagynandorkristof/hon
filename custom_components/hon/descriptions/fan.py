from homeassistant.components.fan import FanEntityDescription

FANS: dict[str, tuple[FanEntityDescription, ...]] = {
    "HO": (
        FanEntityDescription(
            key="settings.windSpeed",
            name="Wind Speed",
            translation_key="air_extraction",
        ),
    ),
}
