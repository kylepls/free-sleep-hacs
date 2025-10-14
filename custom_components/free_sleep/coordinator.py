
from __future__ import annotations

import logging
from typing import Any
from datetime import datetime, timezone, timedelta

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_BASE_URL,
    CONF_PORT,
    DEFAULT_PORT,
    API_VITALS_SUMMARY,
)

_LOGGER = logging.getLogger(__name__)

def path_join(base: str, *parts: str) -> str:
    base = base.rstrip("/")
    tail = "/".join(p.lstrip("/") for p in parts)
    return f"{base}/{tail}"

def iso_z(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

class FreeSleepClient:
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry | None, *, base_url: str | None=None, port: int | None=None):
        self._hass = hass
        if entry:
            data = entry.data
            self.base_url = f"{data[CONF_BASE_URL].rstrip('/')}:{data.get(CONF_PORT, DEFAULT_PORT)}"
        else:
            self.base_url = f"{base_url.rstrip('/')}:{port or DEFAULT_PORT}"
        # Use HA's shared aiohttp session (HA manages lifecycle)
        self._session = async_get_clientsession(hass)

    async def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        url = path_join(self.base_url, path)
        async with self._session.get(url, timeout=10, params=params) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def post(self, path: str, payload: dict) -> Any:
        url = path_join(self.base_url, path)
        async with self._session.post(url, json=payload, timeout=10) as resp:
            resp.raise_for_status()
            try:
                return await resp.json()
            except Exception:
                return None

    async def get_vitals_summary(self, side: str, window_hours: int) -> dict[str, Any] | None:
        now = datetime.now(timezone.utc)
        start = now - timedelta(hours=window_hours)
        params = {
            "startTime": iso_z(start),
            "endTime": iso_z(now),
            "side": side,
        }
        try:
            return await self.get(API_VITALS_SUMMARY, params=params)
        except Exception as e:
            _LOGGER.debug("Vitals fetch failed for %s: %s", side, e)
            return None
