from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, API_SETTINGS
from . import FreeSleepCoordinator

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: FreeSleepCoordinator = data["coordinator"]
    entities = [
        LinkBothSidesSwitch(coordinator, entry),
        SideAwayModeSwitch(coordinator, entry, side="left"),
        SideAwayModeSwitch(coordinator, entry, side="right"),
    ]
    async_add_entities(entities)

class LinkBothSidesSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator: FreeSleepCoordinator, entry: ConfigEntry):
        super().__init__(coordinator)
        self._entry = entry
        self._attr_name = "Free Sleep Link Both Sides"
        self._attr_unique_id = f"{entry.entry_id}_link_both_sides"

    @property
    def is_on(self) -> bool | None:
        settings = self.coordinator.data.get("settings") or {}
        return bool(settings.get("linkBothSides"))

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, f"{self._entry.entry_id}_hub")},
            "name": "Free Sleep Hub",
            "manufacturer": "free-sleep (Unofficial)",
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.client.post(API_SETTINGS, {"linkBothSides": True})
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.client.post(API_SETTINGS, {"linkBothSides": False})
        await self.coordinator.async_request_refresh()

class SideAwayModeSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator: FreeSleepCoordinator, entry: ConfigEntry, side: str):
        super().__init__(coordinator)
        self._entry = entry
        self._side = side
        self._attr_name = f"Free Sleep {side.capitalize()} Away Mode"
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
            "name": f"Free Sleep {self._side.capitalize()}",
            "manufacturer": "free-sleep (Unofficial)",
            "via_device": (DOMAIN, f"{self._entry.entry_id}_hub"),
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.client.post(API_SETTINGS, {self._side: {"awayMode": True}})
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.client.post(API_SETTINGS, {self._side: {"awayMode": False}})
        await self.coordinator.async_request_refresh()
