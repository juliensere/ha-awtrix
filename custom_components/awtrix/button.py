from __future__ import annotations

from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AwtrixCoordinator


@dataclass(frozen=True)
class AwtrixButtonDescription(ButtonEntityDescription):
    press_fn: Callable[[AwtrixCoordinator], Coroutine[Any, Any, None]] = lambda _: None


BUTTONS: tuple[AwtrixButtonDescription, ...] = (
    AwtrixButtonDescription(
        key="reboot",
        name="Reboot",
        icon="mdi:restart",
        press_fn=lambda c: c.async_reboot(),
    ),
    AwtrixButtonDescription(
        key="next_app",
        name="Next app",
        icon="mdi:skip-next",
        press_fn=lambda c: c.async_next_app(),
    ),
    AwtrixButtonDescription(
        key="previous_app",
        name="Previous app",
        icon="mdi:skip-previous",
        press_fn=lambda c: c.async_previous_app(),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: AwtrixCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(AwtrixButton(coordinator, description) for description in BUTTONS)


class AwtrixButton(CoordinatorEntity[AwtrixCoordinator], ButtonEntity):
    _attr_has_entity_name = True

    def __init__(
        self, coordinator: AwtrixCoordinator, description: AwtrixButtonDescription
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator._entry_id}_{description.key}"

    @property
    def device_info(self):
        return self.coordinator.device_info

    async def async_press(self) -> None:
        await self.entity_description.press_fn(self.coordinator)
