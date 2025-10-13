
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import FreeSleepCoordinator
from .const import DOMAIN

BIN_SPECS = [
    ("left_presence", "Left In Bed"),
    ("right_presence", "Right In Bed"),
    ("heating_active", "Heating Active"),
    ("cooling_active", "Cooling Active"),
]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: FreeSleepCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[BinarySensorEntity] = [FreeSleepBinary(coordinator, key, name) for key, name in BIN_SPECS]
    async_add_entities(entities)

class FreeSleepBinary(CoordinatorEntity[FreeSleepCoordinator], BinarySensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: FreeSleepCoordinator, key: str, name: str):
        super().__init__(coordinator)
        self._key = key
        self._attr_unique_id = f"{coordinator.host}_{key}"
        self._attr_name = name

    @property
    def is_on(self) -> bool | None:
        data = self.coordinator.data or {}
        status = data.get("deviceStatus") or {}
        key_map = {
            "left_presence": ["left_present", "leftPresent", "presence_left"],
            "right_presence": ["right_present", "rightPresent", "presence_right"],
            "heating_active": ["heating_active", "isHeating", "heating"],
            "cooling_active": ["cooling_active", "isCooling", "cooling"],
        }
        for k in key_map.get(self._key, []):
            if k in status:
                return bool(status.get(k))
        return None

    @property
    def extra_state_attributes(self):
        return {
            "deviceStatus": self.coordinator.data.get("deviceStatus"),
            "source": self.coordinator.base_url,
        }
