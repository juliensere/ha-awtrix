from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AwtrixCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: AwtrixCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AwtrixRebootButton(coordinator)])


class AwtrixRebootButton(CoordinatorEntity[AwtrixCoordinator], ButtonEntity):
    _attr_has_entity_name = True
    _attr_name = "Reboot"
    _attr_icon = "mdi:restart"

    def __init__(self, coordinator: AwtrixCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._entry_id}_reboot"

    @property
    def device_info(self):
        return self.coordinator.device_info

    async def async_press(self) -> None:
        await self.coordinator.async_reboot()
