
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, API_DEVICE_STATUS, API_SETTINGS, PLATFORMS, UPDATE_INTERVAL_SECS
from .coordinator import FreeSleepClient

_LOGGER = logging.getLogger(__name__)

type FreeSleepData = dict[str, any]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    client = FreeSleepClient(hass, entry)
    coordinator = FreeSleepCoordinator(hass, client)

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok

class FreeSleepCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, client: FreeSleepClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="Free Sleep Coordinator",
            update_interval=timedelta(seconds=UPDATE_INTERVAL_SECS),
        )
        self.client = client
        self.data = {}

    async def _async_update_data(self):
        try:
            device_status = await self.client.get(API_DEVICE_STATUS)
            settings = await self.client.get(API_SETTINGS)
            return {"device_status": device_status, "settings": settings}
        except Exception as e:
            raise UpdateFailed(str(e)) from e
