# AGENTS.md — Guidelines for AI agents working on this repository

## Project overview

Home Assistant custom integration for AWTRIX 3 LED matrix displays (local polling over HTTP).

```
custom_components/awtrix/   ← integration source (HACS-compatible)
tests/                      ← pytest smoke tests
```

## Architecture

| File | Role |
|------|------|
| `coordinator.py` | `DataUpdateCoordinator` — polls `GET /api/loop` + `GET /api/settings` every 30 s, exposes `AwtrixData` (apps list, brightness, matrix_on) and async write helpers |
| `light.py` | `LightEntity` — on/off via `/api/power`, brightness via `BRI` setting; writing brightness auto-disables `ABRI` |
| `button.py` | `ButtonEntity` — reboot via `POST /api/reboot` |
| `sensor.py` | `SensorEntity` — state = app count, attribute `apps` = full `/api/loop` list |
| `config_flow.py` | Single `user` step: host input + `/api/loop` reachability check; host used as unique_id |
| `__init__.py` | Entry setup/unload + 5 domain services (notify, dismiss, set_app, delete_app, switch_app) |
| `services.yaml` | Service field definitions with device selectors |
| `const.py` | `DOMAIN`, `CONF_HOST`, `UPDATE_INTERVAL`, `PLATFORMS` |

## Services

All services accept a `device_id` field (device selector targeting an AWTRIX device):

| Service | Key fields |
|---------|-----------|
| `awtrix.notify` | text, icon, duration, hold, color, progress, bar |
| `awtrix.dismiss` | — |
| `awtrix.set_app` | name, text, icon, duration, lifetime, save, color, progress, bar |
| `awtrix.delete_app` | name |
| `awtrix.switch_app` | name |

## Running tests

```bash
pip install -r requirements-dev.txt
python3 -m pytest tests/ -v
```

Tests use `pytest-homeassistant-custom-component` for HA fixtures and `aioresponses` for HTTP mocking.

## Commit conventions

Use **Conventional Commits** with a single subject line, no body:

```
feat: add weekly token-count sensor
fix: handle empty /api/loop response
chore: bump pytest-homeassistant-custom-component
```

Types: `feat`, `fix`, `chore`, `test`, `docs`, `refactor`, `ci`.

## Key constraints

- `async_get_clientsession(hass)` — always use the shared HA session, never create an `aiohttp.ClientSession` directly.
- Optimistic state updates after write commands — call `coordinator.async_set_updated_data()` immediately after a successful POST so entities reflect the change without waiting for the next poll.
- `MATP` setting key controls matrix power state in `/api/settings`; setting brightness must also send `ABRI: false` to disable auto-brightness mode.
- `save: true` on custom apps writes to ESP flash — warn users against using it for high-frequency updates (flash wear).
