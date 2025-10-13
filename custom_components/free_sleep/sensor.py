
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import FreeSleepCoordinator
from .const import DOMAIN

SENSOR_SPECS = [
    ("heart_rate", "Heart Rate", "bpm"),
    ("breath_rate", "Breath Rate", "rpm"),
    ("hrv", "HRV", "ms"),
    ("left_temp_level", "Left Temp Level", None),
    ("right_temp_level", "Right Temp Level", None),
    ("pod_online", "Pod Online", None),
]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: FreeSleepCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = [FreeSleepGenericSensor(coordinator, key, name, unit) for key, name, unit in SENSOR_SPECS]
    async_add_entities(entities)

class FreeSleepGenericSensor(CoordinatorEntity[FreeSleepCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: FreeSleepCoordinator, key: str, name: str, unit: str | None):
        super().__init__(coordinator)
        self._key = key
        self._attr_unique_id = f"{coordinator.host}_{key}"
        self._attr_name = name
        if unit:
            self._attr_native_unit_of_measurement = unit

    @property
    def native_value(self):
        data = self.coordinator.data or {}
        vitals = data.get("vitals")
        status = data.get("deviceStatus") or {}
        # vitals may be a list; grab latest item if so
        if isinstance(vitals, list) and vitals:
            latest = vitals[-1]
        elif isinstance(vitals, dict):
            latest = vitals
        else:
            latest = {}

        # Heuristics for keys (handles different spellings)
        if self._key == "heart_rate":
            return latest.get("heart_rate") or latest.get("hr") or latest.get("heartRate")
        if self._key == "breath_rate":
            return latest.get("breath_rate") or latest.get("br") or latest.get("breathRate")
        if self._key == "hrv":
            return latest.get("hrv")
        if self._key == "left_temp_level":
            return status.get("left_temp_level") or status.get("leftTempLevel") or status.get("left_temp")
        if self._key == "right_temp_level":
            return status.get("right_temp_level") or status.get("rightTempLevel") or status.get("right_temp")
        if self._key == "pod_online":
            return 1 if (status.get("online") or status.get("pod_online") or status.get("isOnline")) else 0
        return None

    @property
    def extra_state_attributes(self):
        # Attach raw payloads for power users
        return {
            "deviceStatus": self.coordinator.data.get("deviceStatus"),
            "settings": self.coordinator.data.get("settings"),
            "vitals_sample": (self.coordinator.data.get("vitals") or [])[-1] if isinstance(self.coordinator.data.get("vitals"), list) and self.coordinator.data.get("vitals") else self.coordinator.data.get("vitals"),
            "source": self.coordinator.base_url,
        }
