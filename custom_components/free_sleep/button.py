from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, API_DEVICE_STATUS
from . import FreeSleepCoordinator

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: FreeSleepCoordinator = data["coordinator"]
    entities = [PrimeNowButton(coordinator, entry)]
    async_add_entities(entities)

class PrimeNowButton(CoordinatorEntity, ButtonEntity):
    def __init__(self, coordinator: FreeSleepCoordinator, entry: ConfigEntry):
        super().__init__(coordinator)
        self._entry = entry
        self._attr_name = "Free Sleep Prime Now"
        self._attr_unique_id = f"{entry.entry_id}_prime_button"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, f"{self._entry.entry_id}_hub")},
            "name": "Free Sleep Hub",
            "manufacturer": "free-sleep (Unofficial)",
        }

    async def async_press(self) -> None:
        await self.coordinator.client.post(API_DEVICE_STATUS, {"isPriming": True})
        self.coordinator.defer_refresh()
