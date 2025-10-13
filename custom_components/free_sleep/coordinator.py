
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import CONF_BASE_URL, CONF_PORT, DEFAULT_PORT

_LOGGER = logging.getLogger(__name__)

def path_join(base: str, *parts: str) -> str:
    base = base.rstrip("/")
    tail = "/".join(p.lstrip("/") for p in parts)
    return f"{base}/{tail}"

class FreeSleepClient:
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry | None, *, base_url: str | None=None, port: int | None=None):
        if entry:
            data = entry.data
            self.base_url = f"{data[CONF_BASE_URL].rstrip('/')}:{data.get(CONF_PORT, DEFAULT_PORT)}"
        else:
            self.base_url = f"{base_url.rstrip('/')}:{port or DEFAULT_PORT}"
        self._session: aiohttp.ClientSession = aiohttp.ClientSession()

    async def close(self):
        await self._session.close()

    async def get(self, path: str) -> Any:
        url = path_join(self.base_url, path)
        async with self._session.get(url, timeout=10) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def post(self, path: str, payload: dict) -> Any:
        url = path_join(self.base_url, path)
        async with self._session.post(url, json=payload, timeout=10) as resp:
            resp.raise_for_status()
            # Some endpoints may return 200 without body
            try:
                return await resp.json()
            except Exception:
                return None
