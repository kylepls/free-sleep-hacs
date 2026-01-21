
from __future__ import annotations

import asyncio
from typing import Any

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.const import UnitOfTemperature, ATTR_TEMPERATURE
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, API_DEVICE_STATUS
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

    entities = [
        FreeSleepSideClimate(coordinator, entry, side="left", side_name=_resolve_side_name(settings, "left")),
        FreeSleepSideClimate(coordinator, entry, side="right", side_name=_resolve_side_name(settings, "right")),
    ]
    async_add_entities(entities)

class FreeSleepSideClimate(CoordinatorEntity, ClimateEntity):
    _attr_temperature_unit = UnitOfTemperature.FAHRENHEIT
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_hvac_modes = [HVACMode.HEAT_COOL, HVACMode.OFF]
    _attr_icon = "mdi:thermostat"

    def __init__(self, coordinator: FreeSleepCoordinator, entry: ConfigEntry, side: str, side_name: str):
        super().__init__(coordinator)
        self._entry = entry
        self._side = side
        self._side_name = side_name
        self._attr_name = f"{side_name} Climate"
        self._attr_unique_id = f"{entry.entry_id}_{side}_climate"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, f"{self._entry.entry_id}_{self._side}_device")},
            "name": self._side_name,
            "manufacturer": "free-sleep (Unofficial)",
            "via_device": (DOMAIN, f"{self._entry.entry_id}_hub"),
        }

    @property
    def current_temperature(self) -> float | None:
        side = self.coordinator.data["device_status"].get(self._side, {})
        return side.get("currentTemperatureF")

    @property
    def target_temperature(self) -> float | None:
        side = self.coordinator.data["device_status"].get(self._side, {})
        return side.get("targetTemperatureF")

    @property
    def min_temp(self) -> float:
        return 55.0

    @property
    def max_temp(self) -> float:
        return 115.0

    @property
    def target_temperature_step(self) -> float:
        return 1.0

    @property
    def hvac_action(self) -> HVACAction | None:
        side = self.coordinator.data["device_status"].get(self._side, {})
        is_on = side.get("isOn")
        cur = side.get("currentTemperatureF")
        tgt = side.get("targetTemperatureF")
        if not is_on or cur is None or tgt is None:
            return HVACAction.IDLE
        if cur < tgt:
            return HVACAction.HEATING
        if cur > tgt:
            return HVACAction.COOLING
        return HVACAction.IDLE

    @property
    def hvac_mode(self) -> HVACMode:
        side = self.coordinator.data["device_status"].get(self._side, {})
        return HVACMode.HEAT_COOL if side.get("isOn") else HVACMode.OFF

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        is_on = hvac_mode != HVACMode.OFF
        self.coordinator.data["device_status"][self._side]["isOn"] = is_on
        self.async_write_ha_state()
        asyncio.create_task(self.coordinator.client.post(API_DEVICE_STATUS, {self._side: {"isOn": is_on}}))
        self.coordinator.defer_refresh()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        if (temp := kwargs.get(ATTR_TEMPERATURE)) is None:
            return
        self.coordinator.data["device_status"][self._side]["targetTemperatureF"] = temp
        self.async_write_ha_state()
        asyncio.create_task(self.coordinator.client.post(API_DEVICE_STATUS, {self._side: {"targetTemperatureF": temp}}))
        self.coordinator.defer_refresh()