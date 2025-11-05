from __future__ import annotations
import logging
from datetime import timedelta
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import (
    DOMAIN, API_DEVICE_STATUS, API_SETTINGS, PLATFORMS,
    UPDATE_INTERVAL_SECS_DEFAULT, CONF_VITALS_WINDOW_HOURS, DEFAULT_VITALS_WINDOW_HOURS,
)
from .coordinator import FreeSleepClient

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    client = FreeSleepClient(hass, entry)
    coordinator = FreeSleepCoordinator(hass, client, entry)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {"client": client, "coordinator": coordinator}
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok

class FreeSleepCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, client: FreeSleepClient, entry: ConfigEntry) -> None:
        self.client = client
        self.entry = entry
        self.data = {}
        super().__init__(hass, _LOGGER, name="Free Sleep Coordinator",
                         update_interval=timedelta(seconds=int(UPDATE_INTERVAL_SECS_DEFAULT)))

    async def _async_update_data(self):
        try:
            device_status = await self.client.get(API_DEVICE_STATUS)
            settings = await self.client.get(API_SETTINGS)
            hours = int(self.entry.options.get(CONF_VITALS_WINDOW_HOURS, DEFAULT_VITALS_WINDOW_HOURS))
            v_left = await self.client.get_vitals_summary("left", hours)
            v_right = await self.client.get_vitals_summary("right", hours)
            return {"device_status": device_status, "settings": settings,
                    "vitals": {"left": v_left or {}, "right": v_right or {}, "window_hours": hours}}
        except Exception as e:
            _LOGGER.exception("Coordinator update failed")
            raise UpdateFailed(str(e)) from e
