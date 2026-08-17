import logging
from pathlib import Path

import voluptuous as vol  # type: ignore[import-untyped]
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv, aiohttp_client
from homeassistant.core import HomeAssistant
from .pyhon import Hon
from .pyhon.exceptions import HonAuthenticationError, HonConnectionError

from .const import DOMAIN, PLATFORMS, MOBILE_ID, CONF_REFRESH_TOKEN
from .coordinator import HonCoordinator

_LOGGER = logging.getLogger(__name__)

HON_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
    }
)

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.Schema(vol.All(cv.ensure_list, [HON_SCHEMA]))},
    extra=vol.ALLOW_EXTRA,
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    session = aiohttp_client.async_get_clientsession(hass)
    if (config_dir := hass.config.config_dir) is None:
        raise ValueError("Missing Config Dir")
    try:
        hon = await Hon(
            email=entry.data[CONF_EMAIL],
            password=entry.data[CONF_PASSWORD],
            mobile_id=MOBILE_ID,
            session=session,
            test_data_path=Path(config_dir),
            refresh_token=entry.data.get(CONF_REFRESH_TOKEN, ""),
        ).create()
    except HonAuthenticationError as error:
        raise ConfigEntryAuthFailed from error
    except HonConnectionError as error:
        raise ConfigEntryNotReady from error

    # Save the new refresh token
    hass.config_entries.async_update_entry(
        entry, data={**entry.data, CONF_REFRESH_TOKEN: hon.api.auth.refresh_token}
    )

    coordinator = HonCoordinator(hass, hon)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.unique_id] = {"hon": hon, "coordinator": coordinator}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    entry_data = hass.data.get(DOMAIN, {}).get(entry.unique_id)
    if entry_data is None:
        return True
    refresh_token = entry_data["hon"].api.auth.refresh_token

    hass.config_entries.async_update_entry(
        entry, data={**entry.data, CONF_REFRESH_TOKEN: refresh_token}
    )
    unload = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload:
        await entry_data["hon"].close()
        hass.data[DOMAIN].pop(entry.unique_id, None)
        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN, None)
    return unload
