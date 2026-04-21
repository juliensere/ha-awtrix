from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AwtrixCoordinator, AwtrixData


@dataclass(frozen=True)
class AwtrixSwitchDescription(SwitchEntityDescription):
    setting_key: str = ""
    value_fn: Callable[[AwtrixData], bool] = lambda _: False


SWITCHES: tuple[AwtrixSwitchDescription, ...] = (
    AwtrixSwitchDescription(
        key="auto_brightness",
        name="Auto brightness",
        icon="mdi:brightness-auto",
        entity_category=EntityCategory.CONFIG,
        setting_key="ABRI",
        value_fn=lambda d: d.auto_brightness,
    ),
    AwtrixSwitchDescription(
        key="auto_transition",
        name="Auto transition",
        icon="mdi:swap-horizontal",
        entity_category=EntityCategory.CONFIG,
        setting_key="ATRANS",
        value_fn=lambda d: d.auto_transition,
    ),
    AwtrixSwitchDescription(
        key="app_time",
        name="Time app",
        icon="mdi:clock-outline",
        entity_category=EntityCategory.CONFIG,
        setting_key="TIM",
        value_fn=lambda d: d.app_time,
    ),
    AwtrixSwitchDescription(
        key="app_date",
        name="Date app",
        icon="mdi:calendar",
        entity_category=EntityCategory.CONFIG,
        setting_key="DAT",
        value_fn=lambda d: d.app_date,
    ),
    AwtrixSwitchDescription(
        key="app_temp",
        name="Temperature app",
        icon="mdi:thermometer",
        entity_category=EntityCategory.CONFIG,
        setting_key="TEMP",
        value_fn=lambda d: d.app_temp,
    ),
    AwtrixSwitchDescription(
        key="app_hum",
        name="Humidity app",
        icon="mdi:water-percent",
        entity_category=EntityCategory.CONFIG,
        setting_key="HUM",
        value_fn=lambda d: d.app_hum,
    ),
    AwtrixSwitchDescription(
        key="app_bat",
        name="Battery app",
        icon="mdi:battery",
        entity_category=EntityCategory.CONFIG,
        setting_key="BAT",
        value_fn=lambda d: d.app_bat,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: AwtrixCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(AwtrixSwitch(coordinator, description) for description in SWITCHES)


class AwtrixSwitch(CoordinatorEntity[AwtrixCoordinator], SwitchEntity):
    _attr_has_entity_name = True

    def __init__(
        self, coordinator: AwtrixCoordinator, description: AwtrixSwitchDescription
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator._entry_id}_{description.key}"

    @property
    def device_info(self):
        return self.coordinator.device_info

    @property
    def is_on(self) -> bool:
        return self.entity_description.value_fn(self.coordinator.data)

    async def async_turn_on(self, **kwargs: object) -> None:
        await self.coordinator.async_set_setting(self.entity_description.setting_key, True)

    async def async_turn_off(self, **kwargs: object) -> None:
        await self.coordinator.async_set_setting(self.entity_description.setting_key, False)
