
from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from . import FreeSleepCoordinator

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: FreeSleepCoordinator = data["coordinator"]
    entities = [
        # Hub-level
        WaterLevelOKBinary(coordinator, entry),
        IsPrimingBinary(coordinator, entry),
        # Sides
        SideAlarmBinary(coordinator, entry, side="left"),
        SideAlarmBinary(coordinator, entry, side="right"),
    ]
    async_add_entities(entities)

def _parse_bool(val) -> bool:
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.lower() == "true"
    return bool(val)

class HubBaseEntity(CoordinatorEntity, BinarySensorEntity):
    def __init__(self, coordinator: FreeSleepCoordinator, entry: ConfigEntry):
        super().__init__(coordinator)
        self._entry = entry

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, f"{self._entry.entry_id}_hub")},
            "name": "Free Sleep Hub",
            "manufacturer": "free-sleep (Unofficial)",
        }

class WaterLevelOKBinary(HubBaseEntity):
    _attr_name = "Free Sleep Water Level OK"
    _attr_unique_id_suffix = "water_level_ok"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    @property
    def unique_id(self):
        return f"{self._entry.entry_id}_{self._attr_unique_id_suffix}"

    @property
    def is_on(self) -> bool | None:
        # Problem class: on = problem. We invert so that on=True means problem.
        val = self.coordinator.data["device_status"].get("waterLevel")
        ok = _parse_bool(val)
        return not ok  # True = problem

    @property
    def extra_state_attributes(self):
        val = self.coordinator.data["device_status"].get("waterLevel")
        return {"raw_waterLevel": val}

class IsPrimingBinary(HubBaseEntity):
    _attr_name = "Free Sleep Priming"
    _attr_unique_id_suffix = "is_priming"

    @property
    def unique_id(self):
        return f"{self._entry.entry_id}_{self._attr_unique_id_suffix}"

    @property
    def is_on(self) -> bool | None:
        return _parse_bool(self.coordinator.data["device_status"].get("isPriming"))

class SideAlarmBinary(CoordinatorEntity, BinarySensorEntity):
    def __init__(self, coordinator: FreeSleepCoordinator, entry: ConfigEntry, side: str):
        super().__init__(coordinator)
        self._entry = entry
        self._side = side
        self._attr_name = f"Free Sleep {side.capitalize()} Alarm Active"
        self._attr_unique_id = f"{entry.entry_id}_{side}_alarm"

    @property
    def is_on(self) -> bool | None:
        side = self.coordinator.data["device_status"].get(self._side, {})
        return bool(side.get("isAlarmVibrating"))

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, f"{self._entry.entry_id}_{self._side}_device")},
            "name": f"Free Sleep {self._side.capitalize()}",
            "manufacturer": "free-sleep (Unofficial)",
            "via_device": (DOMAIN, f"{self._entry.entry_id}_hub"),
        }
