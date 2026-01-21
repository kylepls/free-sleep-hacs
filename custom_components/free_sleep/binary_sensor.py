
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

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
        WaterLevelOKBinary(coordinator, entry),
        IsPrimingBinary(coordinator, entry),
        SideAlarmBinary(coordinator, entry, side="left", side_name=left_name),
        SideAlarmBinary(coordinator, entry, side="right", side_name=right_name),
        SidePresenceBinary(coordinator, entry, side="left", side_name=left_name),
        SidePresenceBinary(coordinator, entry, side="right", side_name=right_name),
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
            "name": "Hub",
            "manufacturer": "free-sleep (Unofficial)",
        }

class WaterLevelOKBinary(HubBaseEntity):
    _attr_name = "Water Level Problem"
    _attr_unique_id_suffix = "water_level_ok"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    @property
    def unique_id(self):
        return f"{self._entry.entry_id}_{self._attr_unique_id_suffix}"

    @property
    def is_on(self) -> bool | None:
        val = self.coordinator.data["device_status"].get("waterLevel")
        ok = _parse_bool(val)
        return not ok

    @property
    def extra_state_attributes(self):
        val = self.coordinator.data["device_status"].get("waterLevel")
        return {"raw_waterLevel": val}

class IsPrimingBinary(HubBaseEntity):
    _attr_name = "Priming"
    _attr_unique_id_suffix = "is_priming"

    @property
    def unique_id(self):
        return f"{self._entry.entry_id}_{self._attr_unique_id_suffix}"

    @property
    def is_on(self) -> bool | None:
        return _parse_bool(self.coordinator.data["device_status"].get("isPriming"))

class SideAlarmBinary(CoordinatorEntity, BinarySensorEntity):
    def __init__(self, coordinator: FreeSleepCoordinator, entry: ConfigEntry, side: str, side_name: str):
        super().__init__(coordinator)
        self._entry = entry
        self._side = side
        self._side_name = side_name
        self._attr_name = f"{side_name} Alarm Active"
        self._attr_unique_id = f"{entry.entry_id}_{side}_alarm"

    @property
    def is_on(self) -> bool | None:
        side = self.coordinator.data["device_status"].get(self._side, {})
        return bool(side.get("isAlarmVibrating"))

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, f"{self._entry.entry_id}_{self._side}_device")},
            "name": self._side_name,
            "manufacturer": "free-sleep (Unofficial)",
            "via_device": (DOMAIN, f"{self._entry.entry_id}_hub"),
        }

class SidePresenceBinary(CoordinatorEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.PRESENCE

    def __init__(self, coordinator: FreeSleepCoordinator, entry: ConfigEntry, side: str, side_name: str):
        super().__init__(coordinator)
        self._entry = entry
        self._side = side
        self._side_name = side_name
        self._attr_name = f"{side_name} Presence"
        self._attr_unique_id = f"{entry.entry_id}_{side}_presence"

    @property
    def is_on(self) -> bool | None:
        return self.coordinator.data["presence"][self._side]["present"]

    @property
    def extra_state_attributes(self):
        return {"last_updated_at": self.coordinator.data["presence"][self._side]["lastUpdatedAt"]}

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, f"{self._entry.entry_id}_{self._side}_device")},
            "name": self._side_name,
            "manufacturer": "free-sleep (Unofficial)",
            "via_device": (DOMAIN, f"{self._entry.entry_id}_hub"),
        }
