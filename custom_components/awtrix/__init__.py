from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import device_registry as dr

from .const import CONF_HOST, DOMAIN, PLATFORMS
from .coordinator import AwtrixCoordinator

_SERVICES = ("notify", "dismiss", "set_app", "delete_app", "switch_app")


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = AwtrixCoordinator(
        hass, entry.data[CONF_HOST], entry.entry_id, entry.title
    )
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _async_register_services(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]:
            for service in _SERVICES:
                hass.services.async_remove(DOMAIN, service)
    return unloaded


def _get_coordinator(hass: HomeAssistant, device_id: str) -> AwtrixCoordinator | None:
    dev_reg = dr.async_get(hass)
    device = dev_reg.async_get(device_id)
    if not device:
        return None
    for config_entry_id in device.config_entries:
        if coordinator := hass.data.get(DOMAIN, {}).get(config_entry_id):
            return coordinator
    return None


def _async_register_services(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, "notify"):
        return

    async def handle_notify(call: ServiceCall) -> None:
        if coordinator := _get_coordinator(hass, call.data["device_id"]):
            payload = {k: v for k, v in call.data.items() if k != "device_id"}
            await coordinator.async_notify(payload)

    async def handle_dismiss(call: ServiceCall) -> None:
        if coordinator := _get_coordinator(hass, call.data["device_id"]):
            await coordinator.async_dismiss_notification()

    async def handle_set_app(call: ServiceCall) -> None:
        if coordinator := _get_coordinator(hass, call.data["device_id"]):
            name = call.data["name"]
            payload = {k: v for k, v in call.data.items() if k not in ("device_id", "name")}
            await coordinator.async_set_app(name, payload)

    async def handle_delete_app(call: ServiceCall) -> None:
        if coordinator := _get_coordinator(hass, call.data["device_id"]):
            await coordinator.async_delete_app(call.data["name"])

    async def handle_switch_app(call: ServiceCall) -> None:
        if coordinator := _get_coordinator(hass, call.data["device_id"]):
            await coordinator.async_switch_app(call.data["name"])

    hass.services.async_register(DOMAIN, "notify", handle_notify)
    hass.services.async_register(DOMAIN, "dismiss", handle_dismiss)
    hass.services.async_register(DOMAIN, "set_app", handle_set_app)
    hass.services.async_register(DOMAIN, "delete_app", handle_delete_app)
    hass.services.async_register(DOMAIN, "switch_app", handle_switch_app)
