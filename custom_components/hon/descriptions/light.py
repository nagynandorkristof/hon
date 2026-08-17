from homeassistant.components.light import LightEntityDescription

LIGHTS: dict[str, tuple[LightEntityDescription, ...]] = {
    "WC": (
        LightEntityDescription(
            key="settings.lightStatus",
            name="Light",
            translation_key="light",
        ),
    ),
    "HO": (
        LightEntityDescription(
            key="settings.lightStatus",
            name="Light status",
            translation_key="light",
        ),
    ),
    "AP": (
        LightEntityDescription(
            key="settings.lightStatus",
            name="Light status",
            translation_key="light",
        ),
    ),
    "DW": (
        LightEntityDescription(
            key="settings.lightStatus",
            name="Light status",
            translation_key="light",
        ),
    ),
}
