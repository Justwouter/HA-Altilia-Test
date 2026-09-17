from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from aiohttp import ClientTimeout

from .const import (
    CONF_SCAN_INTERVAL,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    INFO_PATH,
    STATUS_PATH,
)

_LOGGER = logging.getLogger(__name__)

class AltiliaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    def async_get_options_flow(config_entry):
        return AltiliaOptionsFlowHandler()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            port = user_input[CONF_PORT]
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
                    title=str(
                        info.get("model_name")
                        or info.get("model")
                        or f"Altilia EMS ({host})"
                    ),
                    data={
                        CONF_HOST: host,
                        CONF_PORT: port,
                    },
                )
            except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as err:
                errors["base"] = "cannot_connect"
                _LOGGER.debug("Unable to connect to Altilia at %s: %s", base_url, err)

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): vol.All(str, vol.Length(min=1)),
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=65535)
                ),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)


class AltiliaOptionsFlowHandler(config_entries.OptionsFlowWithReload):
    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SCAN_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=5, max=3600)),
                }
            ),
        )
