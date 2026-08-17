from homeassistant.components.lock import LockEntityDescription

LOCKS: dict[str, tuple[LockEntityDescription, ...]] = {
    "AP": (
        LockEntityDescription(
            key="lockStatus",
            name="Lock Status",
            translation_key="mode",
        ),
    ),
}
