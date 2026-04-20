from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, SIGNAL_STRENGTH_DECIBELS_MILLIWATT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AwtrixCoordinator, AwtrixData


@dataclass(frozen=True)
class AwtrixSensorDescription(SensorEntityDescription):
    value_fn: Callable[[AwtrixData], StateType] = lambda _: None
    extra_attrs_fn: Callable[[AwtrixData], dict] | None = None


SENSORS: tuple[AwtrixSensorDescription, ...] = (
    AwtrixSensorDescription(
        key="apps",
        name="Apps",
        icon="mdi:view-carousel",
        native_unit_of_measurement="apps",
        value_fn=lambda d: len(d.apps),
        extra_attrs_fn=lambda d: {"apps": d.apps},
    ),
    AwtrixSensorDescription(
        key="current_app",
        name="Current app",
        icon="mdi:television-play",
        value_fn=lambda d: d.current_app or None,
    ),
    AwtrixSensorDescription(
        key="battery",
        name="Battery",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.battery,
    ),
    AwtrixSensorDescription(
        key="wifi_signal",
        name="WiFi signal",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.wifi_signal,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: AwtrixCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(AwtrixSensor(coordinator, description) for description in SENSORS)


class AwtrixSensor(CoordinatorEntity[AwtrixCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(
        self, coordinator: AwtrixCoordinator, description: AwtrixSensorDescription
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator._entry_id}_{description.key}"

    @property
    def device_info(self):
        return self.coordinator.device_info

    @property
    def native_value(self) -> StateType:
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict:
        if self.entity_description.extra_attrs_fn:
            return self.entity_description.extra_attrs_fn(self.coordinator.data)
        return {}
