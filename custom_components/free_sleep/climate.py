
from __future__ import annotations

from typing import Any

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.const import TEMP_FAHRENHEIT, ATTR_TEMPERATURE
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, API_DEVICE_STATUS
from . import FreeSleepCoordinator

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: FreeSleepCoordinator = data["coordinator"]
    entities = [
        FreeSleepSideClimate(coordinator, entry, side="left"),
        FreeSleepSideClimate(coordinator, entry, side="right"),
    ]
    async_add_entities(entities)

class FreeSleepSideClimate(CoordinatorEntity, ClimateEntity):
    _attr_temperature_unit = TEMP_FAHRENHEIT
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_hvac_modes = [HVACMode.HEAT_COOL, HVACMode.OFF]

    def __init__(self, coordinator: FreeSleepCoordinator, entry: ConfigEntry, side: str):
        super().__init__(coordinator)
        self._entry = entry
        self._side = side
        self._attr_name = f"Free Sleep {side.capitalize()} Climate"
        self._attr_unique_id = f"{entry.entry_id}_{side}_climate"

    @property
    def device_info(self):
        # This is a child device of the hub
        return {
            "identifiers": {(DOMAIN, f"{self._entry.entry_id}_{self._side}_device")},
            "name": f"Free Sleep {self._side.capitalize()}",
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

    async def async_set_temperature(self, **kwargs: Any) -> None:
        if (temp := kwargs.get(ATTR_TEMPERATURE)) is None:
            return
        client = self.coordinator.client
        await client.post(API_DEVICE_STATUS, {self._side: {"targetTemperatureF": temp}})
        await self.coordinator.async_request_refresh()
