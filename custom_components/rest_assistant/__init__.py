"""REST Assistant integration."""

from __future__ import annotations

import logging
from datetime import timedelta

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_METHOD,
    CONF_PASSWORD,
    CONF_RESOURCE,
    CONF_TIMEOUT,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_AUTHENTICATION, CONF_SCAN_INTERVAL, DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)


class RestCoordinator(DataUpdateCoordinator[dict | str]):
    """Fetch and share the configured REST response."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self.session = async_get_clientsession(hass)
        super().__init__(
            hass,
            _LOGGER,
            name=entry.title,
            config_entry=entry,
            update_interval=timedelta(seconds=entry.data[CONF_SCAN_INTERVAL]),
        )

    async def _async_update_data(self) -> dict | str:
        data = self.entry.data
        kwargs = {
            "auth": None,
            "timeout": aiohttp.ClientTimeout(total=data[CONF_TIMEOUT]),
        }
        if data.get(CONF_AUTHENTICATION) == "basic":
            kwargs["auth"] = aiohttp.BasicAuth(data[CONF_USERNAME], data[CONF_PASSWORD])
        elif data.get(CONF_AUTHENTICATION) == "digest":
            kwargs["middlewares"] = (
                aiohttp.DigestAuthMiddleware(data[CONF_USERNAME], data[CONF_PASSWORD]),
            )
        request = getattr(self.session, data[CONF_METHOD].lower())
        try:
            async with request(
                data[CONF_RESOURCE],
                data=data.get("payload") if data[CONF_METHOD] == "POST" else None,
                **kwargs,
            ) as response:
                response.raise_for_status()
                try:
                    return await response.json(content_type=None)
                except (aiohttp.ContentTypeError, ValueError):
                    return await response.text()
        except (aiohttp.ClientError, TimeoutError) as err:
            raise UpdateFailed(f"REST request failed ({type(err).__name__})") from err


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a REST sensor entry."""
    coordinator = RestCoordinator(hass, entry)
    try:
        await coordinator.async_config_entry_first_refresh()
    except UpdateFailed as err:
        raise ConfigEntryNotReady from err
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a REST sensor entry."""
    if not await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        return False
    hass.data[DOMAIN].pop(entry.entry_id)
    return True
