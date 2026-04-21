from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
import logging

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

_TIMEOUT = aiohttp.ClientTimeout(total=10)


@dataclass
class AwtrixData:
    # from /api/loop
    apps: list = field(default_factory=list)
    # from /api/stats
    current_app: str = ""
    battery: int = 0
    wifi_signal: int = 0
    uptime: int = 0
    brightness: int = 128
    matrix_on: bool = True
    version: str = ""
    uid: str = ""
    # from /api/settings
    auto_brightness: bool = False
    auto_transition: bool = True
    app_time: bool = True
    app_date: bool = True
    app_temp: bool = True
    app_hum: bool = True
    app_bat: bool = True


class AwtrixCoordinator(DataUpdateCoordinator[AwtrixData]):
    def __init__(self, hass: HomeAssistant, host: str, entry_id: str, entry_title: str) -> None:
        self.host = host
        self._base_url = f"http://{host}"
        self._entry_id = entry_id
        self._entry_title = entry_title
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{host}",
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name=self._entry_title,
            manufacturer="Blueforcer",
            model="AWTRIX 3",
            sw_version=self.data.version if self.data else None,
        )

    async def _async_update_data(self) -> AwtrixData:
        session = async_get_clientsession(self.hass)
        try:
            async with session.get(f"{self._base_url}/api/loop", timeout=_TIMEOUT) as r:
                r.raise_for_status()
                apps = await r.json()
            async with session.get(f"{self._base_url}/api/stats", timeout=_TIMEOUT) as r:
                r.raise_for_status()
                stats = await r.json()
            async with session.get(f"{self._base_url}/api/settings", timeout=_TIMEOUT) as r:
                r.raise_for_status()
                settings = await r.json()
        except (aiohttp.ClientError, TimeoutError) as err:
            raise UpdateFailed(f"Cannot reach {self.host}: {err}") from err

        # /api/loop returns {"name": position, ...} — normalize to sorted list of names
        if isinstance(apps, dict):
            apps = [name for name, _ in sorted(apps.items(), key=lambda x: x[1])]
        elif not isinstance(apps, list):
            apps = []

        return AwtrixData(
            apps=apps,
            current_app=stats.get("app", ""),
            battery=stats.get("bat", 0),
            wifi_signal=stats.get("wifi_signal", 0),
            uptime=stats.get("uptime", 0),
            brightness=stats.get("bri", 128),
            matrix_on=stats.get("matrix", True),
            version=stats.get("version", ""),
            uid=stats.get("uid", ""),
            auto_brightness=settings.get("ABRI", False),
            auto_transition=settings.get("ATRANS", True),
            app_time=settings.get("TIM", True),
            app_date=settings.get("DAT", True),
            app_temp=settings.get("TEMP", True),
            app_hum=settings.get("HUM", True),
            app_bat=settings.get("BAT", True),
        )

    async def _post(self, path: str, json: dict | None = None) -> None:
        session = async_get_clientsession(self.hass)
        try:
            async with session.post(
                f"{self._base_url}{path}",
                json=json or {},
                timeout=_TIMEOUT,
            ) as r:
                r.raise_for_status()
        except (aiohttp.ClientError, TimeoutError) as err:
            raise HomeAssistantError(f"Cannot reach {self.host}: {err}") from err

    async def _post_custom(self, name: str, json: dict) -> None:
        session = async_get_clientsession(self.hass)
        try:
            async with session.post(
                f"{self._base_url}/api/custom",
                params={"name": name},
                json=json,
                timeout=_TIMEOUT,
            ) as r:
                r.raise_for_status()
        except (aiohttp.ClientError, TimeoutError) as err:
            raise HomeAssistantError(f"Cannot reach {self.host}: {err}") from err

    def _optimistic_update(self, **kwargs: object) -> None:
        if self.data is None:
            return
        for key, value in kwargs.items():
            setattr(self.data, key, value)
        self.async_set_updated_data(self.data)

    async def async_set_power(self, power: bool) -> None:
        await self._post("/api/power", {"power": power})
        self._optimistic_update(matrix_on=power)

    async def async_set_brightness(self, brightness: int) -> None:
        await self._post("/api/settings", {"BRI": brightness, "ABRI": False})
        self._optimistic_update(brightness=brightness)

    async def async_reboot(self) -> None:
        await self._post("/api/reboot")

    async def async_notify(self, payload: dict) -> None:
        await self._post("/api/notify", payload)

    async def async_dismiss_notification(self) -> None:
        await self._post("/api/notify/dismiss")

    async def async_set_app(self, name: str, payload: dict) -> None:
        await self._post_custom(name, payload)

    async def async_delete_app(self, name: str) -> None:
        await self._post_custom(name, {})

    async def async_switch_app(self, name: str) -> None:
        await self._post("/api/switch", {"name": name})

    async def async_next_app(self) -> None:
        await self._post("/api/nextapp")

    async def async_previous_app(self) -> None:
        await self._post("/api/previousapp")

    async def async_set_indicator(
        self,
        number: int,
        color: str,
        blink: int | None = None,
        fade: int | None = None,
    ) -> None:
        if not color:
            payload: dict = {"color": [0, 0, 0]}
        else:
            payload = {"color": color}
            if blink is not None:
                payload["blink"] = blink
            if fade is not None:
                payload["fade"] = fade
        await self._post(f"/api/indicator{number}", payload)

    async def async_set_setting(self, key: str, value: object) -> None:
        await self._post("/api/settings", {key: value})
        field = {
            "ABRI": "auto_brightness",
            "ATRANS": "auto_transition",
            "TIM": "app_time",
            "DAT": "app_date",
            "TEMP": "app_temp",
            "HUM": "app_hum",
            "BAT": "app_bat",
        }.get(key)
        if field:
            self._optimistic_update(**{field: value})
