from __future__ import annotations

from homeassistant.components.light import ATTR_BRIGHTNESS, ColorMode, LightEntity
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
    async_add_entities([AwtrixLight(coordinator)])


class AwtrixLight(CoordinatorEntity[AwtrixCoordinator], LightEntity):
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}
    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_has_entity_name = True
    _attr_name = None

    def __init__(self, coordinator: AwtrixCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._entry_id}_light"

    @property
    def device_info(self):
        return self.coordinator.device_info

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.matrix_on

    @property
    def brightness(self) -> int:
        return self.coordinator.data.brightness

    async def async_turn_on(self, **kwargs) -> None:
        if ATTR_BRIGHTNESS in kwargs:
            await self.coordinator.async_set_brightness(kwargs[ATTR_BRIGHTNESS])
        await self.coordinator.async_set_power(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_set_power(False)
