"""Smoke tests for AwtrixCoordinator."""
import pytest
from aioresponses import aioresponses

from custom_components.awtrix.coordinator import AwtrixCoordinator

HOST = "192.168.1.100"
ENTRY_ID = "test_entry"
MOCK_LOOP = {"time": 0, "myapp": 1}
MOCK_STATS = {
    "bat": 80,
    "bri": 150,
    "matrix": True,
    "app": "myapp",
    "wifi_signal": -65,
    "uptime": 3600,
    "version": "0.98",
    "uid": "awtrix_abc123",
}
MOCK_SETTINGS = {
    "ABRI": False,
    "ATRANS": True,
    "TIM": True,
    "DAT": True,
    "TEMP": True,
    "HUM": True,
    "BAT": True,
}


def make_coordinator(hass) -> AwtrixCoordinator:
    return AwtrixCoordinator(hass, HOST, ENTRY_ID, "Test AWTRIX")


def mock_full_refresh(m):
    m.get(f"http://{HOST}/api/loop", payload=MOCK_LOOP)
    m.get(f"http://{HOST}/api/stats", payload=MOCK_STATS)
    m.get(f"http://{HOST}/api/settings", payload=MOCK_SETTINGS)


@pytest.mark.asyncio
async def test_coordinator_fetch(hass):
    coordinator = make_coordinator(hass)
    with aioresponses() as m:
        mock_full_refresh(m)
        await coordinator.async_refresh()

    assert coordinator.data.apps == ["time", "myapp"]
    assert coordinator.data.battery == 80
    assert coordinator.data.brightness == 150
    assert coordinator.data.matrix_on is True
    assert coordinator.data.current_app == "myapp"
    assert coordinator.data.wifi_signal == -65
    assert coordinator.data.uptime == 3600
    assert coordinator.data.version == "0.98"
    assert coordinator.data.auto_brightness is False
    assert coordinator.data.auto_transition is True
    assert coordinator.data.app_time is True


@pytest.mark.asyncio
async def test_coordinator_unreachable(hass):
    from aiohttp import ClientConnectionError

    coordinator = make_coordinator(hass)
    with aioresponses() as m:
        m.get(f"http://{HOST}/api/loop", exception=ClientConnectionError())
        await coordinator.async_refresh()

    assert coordinator.last_update_success is False


@pytest.mark.asyncio
async def test_optimistic_brightness(hass):
    coordinator = make_coordinator(hass)
    with aioresponses() as m:
        mock_full_refresh(m)
        await coordinator.async_refresh()

    with aioresponses() as m:
        m.post(f"http://{HOST}/api/settings")
        await coordinator.async_set_brightness(50)

    assert coordinator.data.brightness == 50


@pytest.mark.asyncio
async def test_optimistic_power(hass):
    coordinator = make_coordinator(hass)
    with aioresponses() as m:
        mock_full_refresh(m)
        await coordinator.async_refresh()

    with aioresponses() as m:
        m.post(f"http://{HOST}/api/power")
        await coordinator.async_set_power(False)

    assert coordinator.data.matrix_on is False


@pytest.mark.asyncio
async def test_apps_sorted_by_position(hass):
    coordinator = make_coordinator(hass)
    with aioresponses() as m:
        m.get(f"http://{HOST}/api/loop", payload={"b_app": 1, "a_app": 0})
        m.get(f"http://{HOST}/api/stats", payload=MOCK_STATS)
        m.get(f"http://{HOST}/api/settings", payload=MOCK_SETTINGS)
        await coordinator.async_refresh()

    assert coordinator.data.apps == ["a_app", "b_app"]


@pytest.mark.asyncio
async def test_next_previous_app(hass):
    coordinator = make_coordinator(hass)
    with aioresponses() as m:
        mock_full_refresh(m)
        await coordinator.async_refresh()

    with aioresponses() as m:
        m.post(f"http://{HOST}/api/nextapp")
        await coordinator.async_next_app()

    with aioresponses() as m:
        m.post(f"http://{HOST}/api/previousapp")
        await coordinator.async_previous_app()


@pytest.mark.asyncio
async def test_set_indicator(hass):
    coordinator = make_coordinator(hass)
    with aioresponses() as m:
        mock_full_refresh(m)
        await coordinator.async_refresh()

    with aioresponses() as m:
        m.post(f"http://{HOST}/api/indicator2")
        await coordinator.async_set_indicator(2, "#FF0000", blink=500)

    with aioresponses() as m:
        m.post(f"http://{HOST}/api/indicator1")
        await coordinator.async_set_indicator(1, "")


@pytest.mark.asyncio
async def test_optimistic_setting(hass):
    coordinator = make_coordinator(hass)
    with aioresponses() as m:
        mock_full_refresh(m)
        await coordinator.async_refresh()

    assert coordinator.data.auto_brightness is False

    with aioresponses() as m:
        m.post(f"http://{HOST}/api/settings")
        await coordinator.async_set_setting("ABRI", True)

    assert coordinator.data.auto_brightness is True

    with aioresponses() as m:
        m.post(f"http://{HOST}/api/settings")
        await coordinator.async_set_setting("TIM", False)

    assert coordinator.data.app_time is False
