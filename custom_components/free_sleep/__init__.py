
from __future__ import annotations

import logging
from datetime import timedelta, datetime, timezone

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    API_DEVICE_STATUS,
    API_SETTINGS,
    PLATFORMS,
    UPDATE_INTERVAL_SECS_DEFAULT,
    CONF_UPDATE_INTERVAL_SECS,
    CONF_VITALS_WINDOW_HOURS,
    DEFAULT_VITALS_WINDOW_HOURS,
    CONF_VITALS_MODE,
    VITALS_MODE_NIGHTLY,
    VITALS_MODE_POLLING,
    CONF_VITALS_NIGHTLY_TIME,
    CONF_VITALS_POLL_SECS,
    VITALS_POLL_SECS_DEFAULT,
)
from .coordinator import FreeSleepClient

_LOGGER = logging.getLogger(__name__)

type FreeSleepData = dict[str, any]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    client = FreeSleepClient(hass, entry)
    coordinator = FreeSleepCoordinator(hass, client, entry)

    await coordinator.async_config_entry_first_refresh()
    await coordinator.async_setup_vitals_scheduler()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    data = hass.data[DOMAIN].get(entry.entry_id)
    if data and "coordinator" in data:
        await data["coordinator"].async_teardown_vitals_scheduler()
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok

class FreeSleepCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, client: FreeSleepClient, entry: ConfigEntry) -> None:
        self.client = client
        self.entry = entry
        self.data = {}
        self._vitals_cache = {"left": {}, "right": {}, "window_hours": DEFAULT_VITALS_WINDOW_HOURS}
        self._unsub_vitals = None

        interval = entry.options.get(CONF_UPDATE_INTERVAL_SECS, UPDATE_INTERVAL_SECS_DEFAULT)
        super().__init__(
            hass,
            _LOGGER,
            name="Free Sleep Coordinator",
            update_interval=timedelta(seconds=int(interval)),
        )

    async def async_setup_vitals_scheduler(self):
        # Nightly scheduler setup if enabled
        mode = self.entry.options.get(CONF_VITALS_MODE, VITALS_MODE_POLLING)
        if mode != VITALS_MODE_NIGHTLY:
            return
        time_str = self.entry.options.get(CONF_VITALS_NIGHTLY_TIME, "02:00")
        try:
            hh, mm = [int(x) for x in time_str.split(":")]
        except Exception:
            hh, mm = 2, 0  # fallback

        async def _nightly_cb(now):
            await self._refresh_vitals_cache()

        # Schedule daily at hh:mm local time
        from homeassistant.helpers.event import async_track_time_change
        self._unsub_vitals = async_track_time_change(self.hass, _nightly_cb, hour=hh, minute=mm, second=0)

    async def async_teardown_vitals_scheduler(self):
        if self._unsub_vitals:
            self._unsub_vitals()
            self._unsub_vitals = None

    async def _refresh_vitals_cache(self):
        window_hours = int(self.entry.options.get(CONF_VITALS_WINDOW_HOURS, DEFAULT_VITALS_WINDOW_HOURS))
        left = await self.client.get_vitals_summary("left", window_hours)
        right = await self.client.get_vitals_summary("right", window_hours)
        self._vitals_cache = {"left": left or {}, "right": right or {}, "window_hours": window_hours}
        # Push update to listeners
        if self.data:
            merged = dict(self.data)
            merged["vitals"] = dict(self._vitals_cache)
            self.async_set_updated_data(merged)

    async def _async_update_data(self):
        try:
            device_status = await self.client.get(API_DEVICE_STATUS)
            settings = await self.client.get(API_SETTINGS)

            # Handle vitals by mode
            mode = self.entry.options.get(CONF_VITALS_MODE, VITALS_MODE_POLLING)
            window_hours = int(self.entry.options.get(CONF_VITALS_WINDOW_HOURS, DEFAULT_VITALS_WINDOW_HOURS))

            vitals = dict(self._vitals_cache)
            if mode == VITALS_MODE_POLLING:
                # Poll if stale
                poll_secs = int(self.entry.options.get(CONF_VITALS_POLL_SECS, VITALS_POLL_SECS_DEFAULT))
                last_ts = self.data.get("_vitals_ts")
                now = datetime.now(timezone.utc).timestamp()
                if (last_ts is None) or (now - last_ts > poll_secs) or vitals.get("window_hours") != window_hours:
                    left = await self.client.get_vitals_summary("left", window_hours)
                    right = await self.client.get_vitals_summary("right", window_hours)
                    vitals = {"left": left or {}, "right": right or {}, "window_hours": window_hours}
                    self.data["_vitals_ts"] = now
            else:
                # Nightly mode: ensure cache has correct window_hours
                if vitals.get("window_hours") != window_hours:
                    await self._refresh_vitals_cache()
                    vitals = dict(self._vitals_cache)

            return {
                "device_status": device_status,
                "settings": settings,
                "vitals": vitals,
                "_vitals_ts": self.data.get("_vitals_ts"),
            }
        except Exception as e:
            raise UpdateFailed(str(e)) from e
