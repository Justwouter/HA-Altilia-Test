from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from aiohttp import ClientTimeout

from .const import DEFAULT_PORT, DEFAULT_SCAN_INTERVAL, DOMAIN, INFO_PATH, STATUS_PATH, CONF_SCAN_INTERVAL


class AltiliaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            port = int(user_input.get(CONF_PORT, DEFAULT_PORT))
            base_url = f"http://{host}:{port}"
            session = async_get_clientsession(self.hass)

            try:
                timeout = ClientTimeout(total=8)
                async with session.get(f"{base_url}{STATUS_PATH}", timeout=timeout) as resp:
                    resp.raise_for_status()
                    status = await resp.json(content_type=None)
                if not isinstance(status, dict):
                    raise ValueError("Invalid JSON response")

                info = {}
                try:
                    async with session.get(f"{base_url}{INFO_PATH}", timeout=timeout) as resp:
                        resp.raise_for_status()
                        candidate = await resp.json(content_type=None)
                        if isinstance(candidate, dict):
                            info = candidate
                except Exception:
                    pass

                device_id = info.get("device_id") or host
                await self.async_set_unique_id(str(device_id))
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=info.get("model_name") or info.get("model") or f"Altilia EMS ({host})",
                    data={
                        CONF_HOST: host,
                        CONF_PORT: port,
                    },
                )
            except Exception:
                errors["base"] = "cannot_connect"

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): vol.Coerce(int),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
