"""Tests for the AWTRIX config flow."""
import pytest
from aioresponses import aioresponses
from homeassistant import config_entries

from custom_components.awtrix.const import CONF_HOST, DOMAIN

HOST = "192.168.1.50"
MOCK_STATS = {"uid": "awtrix_deadbe", "version": "0.98", "bat": 100}


@pytest.mark.asyncio
async def test_config_flow_uses_uid_as_title(hass):
    """Device name should be the uid returned by /api/stats, not the IP."""
    with aioresponses() as m:
        m.get(f"http://{HOST}/api/stats", payload=MOCK_STATS)
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] == "form"

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_HOST: HOST}
        )

    assert result2["type"] == "create_entry"
    assert result2["title"] == "awtrix_deadbe"
    assert result2["data"] == {CONF_HOST: HOST}


@pytest.mark.asyncio
async def test_config_flow_uid_is_unique_id(hass):
    """unique_id should be the device uid, not the IP address."""
    with aioresponses() as m:
        m.get(f"http://{HOST}/api/stats", payload=MOCK_STATS)
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_HOST: HOST}
        )

    entry = hass.config_entries.async_get_entry(result2["result"].entry_id)
    assert entry.unique_id == "awtrix_deadbe"


@pytest.mark.asyncio
async def test_config_flow_fallback_to_host_when_no_uid(hass):
    """If uid is missing from stats, fall back to host as title."""
    with aioresponses() as m:
        m.get(f"http://{HOST}/api/stats", payload={"version": "0.98"})
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_HOST: HOST}
        )

    assert result2["type"] == "create_entry"
    assert result2["title"] == HOST


@pytest.mark.asyncio
async def test_config_flow_cannot_connect(hass):
    """Connection error should show 'cannot_connect' error."""
    from aiohttp import ClientConnectionError

    with aioresponses() as m:
        m.get(f"http://{HOST}/api/stats", exception=ClientConnectionError())
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_HOST: HOST}
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "cannot_connect"}


@pytest.mark.asyncio
async def test_config_flow_duplicate_aborts(hass):
    """Adding the same device twice should abort."""
    with aioresponses() as m:
        m.get(f"http://{HOST}/api/stats", payload=MOCK_STATS)
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_HOST: HOST}
        )

    with aioresponses() as m:
        m.get(f"http://{HOST}/api/stats", payload=MOCK_STATS)
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_HOST: HOST}
        )

    assert result2["type"] == "abort"
    assert result2["reason"] == "already_configured"
