from __future__ import annotations
import asyncio
import logging
from datetime import timedelta
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from .const import (
    DOMAIN, API_DEVICE_STATUS, API_SETTINGS, API_METRICS_PRESENCE, PLATFORMS,
    UPDATE_INTERVAL_SECS_DEFAULT, PRESENCE_UPDATE_INTERVAL_SECS,
    CONF_VITALS_WINDOW_HOURS, DEFAULT_VITALS_WINDOW_HOURS,
)
from .coordinator import FreeSleepClient

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    client = FreeSleepClient(hass, entry)
    coordinator = FreeSleepCoordinator(hass, client, entry)
    presence_coordinator = FreeSleepPresenceCoordinator(hass, client)
    await coordinator.async_config_entry_first_refresh()
    await presence_coordinator.async_config_entry_first_refresh()
    coordinator.start_polling()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
        "presence_coordinator": presence_coordinator,
    }
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator: FreeSleepCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    presence_coordinator: FreeSleepPresenceCoordinator = hass.data[DOMAIN][entry.entry_id]["presence_coordinator"]
    coordinator.stop_polling()
    await presence_coordinator.async_shutdown()
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok

class FreeSleepCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, client: FreeSleepClient, entry: ConfigEntry) -> None:
        self.client = client
        self.entry = entry
        self.data = {}
        self._poll_interval_seconds = int(UPDATE_INTERVAL_SECS_DEFAULT)
        self._scheduled_refresh_task: asyncio.Task | None = None
        super().__init__(hass, _LOGGER, name="Free Sleep Coordinator", update_interval=None)

    def start_polling(self) -> None:
        self._schedule_delayed_refresh(self._poll_interval_seconds)

    def stop_polling(self) -> None:
        if self._scheduled_refresh_task and not self._scheduled_refresh_task.done():
            self._scheduled_refresh_task.cancel()

    def defer_refresh(self) -> None:
        self._schedule_delayed_refresh(self._poll_interval_seconds)

    def _schedule_delayed_refresh(self, delay_seconds: int) -> None:
        if self._scheduled_refresh_task and not self._scheduled_refresh_task.done():
            self._scheduled_refresh_task.cancel()
        self._scheduled_refresh_task = self.hass.async_create_task(self._delayed_refresh(delay_seconds))
        self._scheduled_refresh_task.add_done_callback(self._handle_scheduled_done)

    async def _delayed_refresh(self, delay_seconds: int) -> None:
        await asyncio.sleep(delay_seconds)
        await super().async_refresh()
        self._schedule_delayed_refresh(self._poll_interval_seconds)

    def _handle_scheduled_done(self, task: asyncio.Task) -> None:
        if task.cancelled():
            return
        task.result()

    async def _async_update_data(self):
        device_status = await self.client.get(API_DEVICE_STATUS)
        settings = await self.client.get(API_SETTINGS)
        hours = int(self.entry.options.get(CONF_VITALS_WINDOW_HOURS, DEFAULT_VITALS_WINDOW_HOURS))
        v_left = await self.client.get_vitals_summary("left", hours)
        v_right = await self.client.get_vitals_summary("right", hours)
        return {
            "device_status": device_status,
            "settings": settings,
            "vitals": {"left": v_left, "right": v_right, "window_hours": hours},
        }

class FreeSleepPresenceCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, client: FreeSleepClient) -> None:
        self.client = client
        self.data = {}
        super().__init__(
            hass,
            _LOGGER,
            name="Free Sleep Presence Coordinator",
            update_interval=timedelta(seconds=PRESENCE_UPDATE_INTERVAL_SECS),
        )

    async def _async_update_data(self):
        return await self.client.get(API_METRICS_PRESENCE)
