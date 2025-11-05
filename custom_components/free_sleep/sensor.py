
from __future__ import annotations

from datetime import datetime, timezone

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN
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
        LastPrimeSensor(coordinator, entry),
        SideSecondsRemaining(coordinator, entry, side="left", side_name=left_name),
        SideSecondsRemaining(coordinator, entry, side="right", side_name=right_name),
    ]

    metrics = [
        ("avgHeartRate", "Average Heart Rate", "bpm"),
        ("minHeartRate", "Minimum Heart Rate", "bpm"),
        ("maxHeartRate", "Maximum Heart Rate", "bpm"),
        ("avgHRV", "Average HRV", "ms"),
        ("avgBreathingRate", "Average Breathing Rate", "breaths/min"),
    ]
    for side, sname in (("left", left_name), ("right", right_name)):
        for key, label, unit in metrics:
            entities.append(SideVitalsSensor(coordinator, entry, side=side, side_name=sname, key=key, label=label, unit=unit))

    async_add_entities(entities)

class LastPrimeSensor(CoordinatorEntity, SensorEntity):
    _attr_name = "Last Prime"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator: FreeSleepCoordinator, entry: ConfigEntry):
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_last_prime"

    @property
    def native_value(self):
        raw = (self.coordinator.data.get("settings") or {}).get("lastPrime")
        if not raw:
            return None
        dt = dt_util.parse_datetime(raw)
        if dt is None:
            try:
                dt = datetime.fromisoformat(raw.replace('Z', '+00:00'))
            except Exception:
                return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, f"{self._entry.entry_id}_hub")},
            "name": "Hub",
            "manufacturer": "free-sleep (Unofficial)",
            "icon": "mdi:bed",
        }

class SideSecondsRemaining(CoordinatorEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "s"

    def __init__(self, coordinator: FreeSleepCoordinator, entry: ConfigEntry, side: str, side_name: str):
        super().__init__(coordinator)
        self._entry = entry
        self._side = side
        self._side_name = side_name
        self._attr_name = f"{side_name} Seconds Remaining"
        self._attr_unique_id = f"{entry.entry_id}_{side}_seconds_remaining"

    @property
    def native_value(self):
        side = self.coordinator.data["device_status"].get(self._side, {})
        return side.get("secondsRemaining")

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, f"{self._entry.entry_id}_{self._side}_device")},
            "name": self._side_name,
            "manufacturer": "free-sleep (Unofficial)",
            "via_device": (DOMAIN, f"{self._entry.entry_id}_hub"),
        }

class SideVitalsSensor(CoordinatorEntity, SensorEntity):
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: FreeSleepCoordinator, entry: ConfigEntry, side: str, side_name: str, key: str, label: str, unit: str):
        super().__init__(coordinator)
        self._entry = entry
        self._side = side
        self._side_name = side_name
        self._key = key
        self._label = label
        self._unit = unit
        self._attr_name = f"{side_name} {label}"
        self._attr_unique_id = f"{entry.entry_id}_{side}_{key}_vitals"
        self._attr_native_unit_of_measurement = unit

    @property
    def native_value(self):
        vitals = (self.coordinator.data.get("vitals") or {}).get(self._side) or {}
        return vitals.get(self._key)

    @property
    def extra_state_attributes(self):
        return {
            "window_hours": (self.coordinator.data.get("vitals") or {}).get("window_hours"),
        }

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, f"{self._entry.entry_id}_{self._side}_device")},
            "name": self._side_name,
            "manufacturer": "free-sleep (Unofficial)",
            "via_device": (DOMAIN, f"{self._entry.entry_id}_hub"),
        }
