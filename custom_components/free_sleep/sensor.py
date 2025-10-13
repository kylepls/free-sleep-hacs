
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
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
        LastPrimeSensor(coordinator, entry),
        SideSecondsRemaining(coordinator, entry, side="left"),
        SideSecondsRemaining(coordinator, entry, side="right"),
    ]
    async_add_entities(entities)

class LastPrimeSensor(CoordinatorEntity, SensorEntity):
    _attr_name = "Free Sleep Last Prime"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator: FreeSleepCoordinator, entry: ConfigEntry):
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_last_prime"

    @property
    def native_value(self):
        return (self.coordinator.data.get("settings") or {}).get("lastPrime")

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, f"{self._entry.entry_id}_hub")},
            "name": "Free Sleep Hub",
            "manufacturer": "free-sleep (Unofficial)",
        }

class SideSecondsRemaining(CoordinatorEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "s"

    def __init__(self, coordinator: FreeSleepCoordinator, entry: ConfigEntry, side: str):
        super().__init__(coordinator)
        self._entry = entry
        self._side = side
        self._attr_name = f"Free Sleep {side.capitalize()} Seconds Remaining"
        self._attr_unique_id = f"{entry.entry_id}_{side}_seconds_remaining"

    @property
    def native_value(self):
        side = self.coordinator.data["device_status"].get(self._side, {})
        return side.get("secondsRemaining")

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, f"{self._entry.entry_id}_{self._side}_device")},
            "name": f"Free Sleep {self._side.capitalize()}",
            "manufacturer": "free-sleep (Unofficial)",
            "via_device": (DOMAIN, f"{self._entry.entry_id}_hub"),
        }
