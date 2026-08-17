import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, FALLBACK_POLL_INTERVAL
from .pyhon import Hon
from .pyhon.exceptions import HonConnectionError

_LOGGER = logging.getLogger(__name__)


class HonCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, hon: Hon) -> None:
        super().__init__(
            hass, _LOGGER, name=DOMAIN, update_interval=FALLBACK_POLL_INTERVAL
        )
        self._hon = hon
        hon.subscribe_updates(self.async_set_updated_data)

    async def _async_update_data(self) -> dict[str, Any]:
        for appliance in self._hon.appliances:
            try:
                await appliance.update()
            except HonConnectionError:
                _LOGGER.warning(
                    "Fallback poll failed for %s, will retry next cycle",
                    appliance.nick_name,
                )
        return {}
