
from __future__ import annotations

import asyncio
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, API_SETTINGS
from . import FreeSleepCoordinator

def _resolve_side_name(settings: dict, side: str) -> str:
    try:
        name = (settings or {}).get(side, {}).get("name")
        if isinstance(name, str) and name.strip():
            return name.strip()
    except Exception:
        pass
    return side.capitalize()


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: FreeSleepCoordinator = data["coordinator"]
    settings = coordinator.data.get("settings") or {}
    left_name = _resolve_side_name(settings, "left")
    right_name = _resolve_side_name(settings, "right")
    entities = [
        LinkBothSidesSwitch(coordinator, entry),
        SideAwayModeSwitch(coordinator, entry, side="left", side_name=left_name),
        SideAwayModeSwitch(coordinator, entry, side="right", side_name=right_name),
    ]
    async_add_entities(entities)

class LinkBothSidesSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator: FreeSleepCoordinator, entry: ConfigEntry):
        super().__init__(coordinator)
        self._entry = entry
        self._attr_name = "Link Both Sides"
        self._attr_unique_id = f"{entry.entry_id}_link_both_sides"

    @property
    def is_on(self) -> bool | None:
        settings = self.coordinator.data.get("settings") or {}
        return bool(settings.get("linkBothSides"))

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, f"{self._entry.entry_id}_hub")},
            "name": "Hub",
            "manufacturer": "free-sleep (Unofficial)",
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        if "settings" not in self.coordinator.data:
            self.coordinator.data["settings"] = {}
        self.coordinator.data["settings"]["linkBothSides"] = True
        self.async_write_ha_state()
        asyncio.create_task(self.coordinator.client.post(API_SETTINGS, {"linkBothSides": True}))

    async def async_turn_off(self, **kwargs: Any) -> None:
        if "settings" not in self.coordinator.data:
            self.coordinator.data["settings"] = {}
        self.coordinator.data["settings"]["linkBothSides"] = False
        self.async_write_ha_state()
        asyncio.create_task(self.coordinator.client.post(API_SETTINGS, {"linkBothSides": False}))

class SideAwayModeSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator: FreeSleepCoordinator, entry: ConfigEntry, side: str, side_name: str):
        super().__init__(coordinator)
        self._entry = entry
        self._side = side
        self._side_name = side_name
        self._attr_name = f"{side_name} Away Mode"
        self._attr_unique_id = f"{entry.entry_id}_{side}_away_mode"

    @property
    def is_on(self) -> bool | None:
        settings = self.coordinator.data.get("settings") or {}
        side_settings = settings.get(self._side) or {}
        return bool(side_settings.get("awayMode"))

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, f"{self._entry.entry_id}_{self._side}_device")},
            "name": self._side_name,
            "manufacturer": "free-sleep (Unofficial)",
            "via_device": (DOMAIN, f"{self._entry.entry_id}_hub"),
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        if "settings" not in self.coordinator.data:
            self.coordinator.data["settings"] = {}
        if self._side not in self.coordinator.data["settings"]:
            self.coordinator.data["settings"][self._side] = {}
        self.coordinator.data["settings"][self._side]["awayMode"] = True
        self.async_write_ha_state()
        asyncio.create_task(self.coordinator.client.post(API_SETTINGS, {self._side: {"awayMode": True}}))

    async def async_turn_off(self, **kwargs: Any) -> None:
        if "settings" not in self.coordinator.data:
            self.coordinator.data["settings"] = {}
        if self._side not in self.coordinator.data["settings"]:
            self.coordinator.data["settings"][self._side] = {}
        self.coordinator.data["settings"][self._side]["awayMode"] = False
        self.async_write_ha_state()
        asyncio.create_task(self.coordinator.client.post(API_SETTINGS, {self._side: {"awayMode": False}}))
