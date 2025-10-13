
from __future__ import annotations

from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, DEFAULT_PORT, DEFAULT_SCAN_INTERVAL
import asyncio
import async_timeout
import logging
import aiohttp

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["sensor", "binary_sensor"]

class FreeSleepCoordinator(DataUpdateCoordinator[dict]):
    def __init__(self, hass: HomeAssistant, host: str, port: int, scan_interval: int) -> None:
        self.host = host
        self.port = port
        self._session = async_get_clientsession(hass)
        super().__init__(
            hass,
            _LOGGER,
            name="Free Sleep Coordinator",
            update_interval=timedelta(seconds=scan_interval),
        )

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    async def _fetch(self, path: str) -> dict | list | None:
        url = f"{self.base_url}{path}"
        try:
            async with async_timeout.timeout(10):
                async with self._session.get(url) as resp:
                    if resp.status != 200:
                        raise UpdateFailed(f"HTTP {resp.status} for {url}")
                    ct = resp.headers.get("Content-Type","")
                    if "application/json" in ct or path.endswith(".json"):
                        return await resp.json(content_type=None)
                    # fall back to text if needed
                    return await resp.text()
        except (asyncio.TimeoutError, aiohttp.ClientError) as err:
            raise UpdateFailed(f"Error fetching {url}: {err}") from err

    async def _async_update_data(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        # Try a few known endpoints. Not all will exist on every build.
        endpoints = {
            "deviceStatus": "/api/deviceStatus",
            "settings": "/api/settings",
            "schedules": "/api/schedules",
            "execute": "/api/execute/state",
            "vitals": "/api/metrics/vitals",
        }
        for key, path in endpoints.items():
            try:
                data[key] = await self._fetch(path)
            except UpdateFailed as err:
                _LOGGER.debug("Skipping %s due to fetch error: %s", key, err)
        return data

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    host = entry.data.get("host")
    port = entry.data.get("port", DEFAULT_PORT)
    scan_interval = entry.data.get("scan_interval", DEFAULT_SCAN_INTERVAL)

    coordinator = FreeSleepCoordinator(hass, host, port, scan_interval)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
