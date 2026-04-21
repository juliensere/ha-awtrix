from __future__ import annotations

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_HOST, DOMAIN

_SCHEMA = vol.Schema({vol.Required(CONF_HOST): str})
_TIMEOUT = aiohttp.ClientTimeout(total=10)


class AwtrixConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            session = async_get_clientsession(self.hass)
            try:
                async with session.get(
                    f"http://{host}/api/stats", timeout=_TIMEOUT
                ) as r:
                    r.raise_for_status()
                    stats = await r.json()
            except (aiohttp.ClientError, TimeoutError):
                errors["base"] = "cannot_connect"
            else:
                uid = stats.get("uid") or host
                await self.async_set_unique_id(uid)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=uid, data={CONF_HOST: host})

        return self.async_show_form(
            step_id="user",
            data_schema=_SCHEMA,
            errors=errors,
        )
