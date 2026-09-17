from __future__ import annotations

from datetime import timedelta
import logging

from aiohttp import ClientTimeout
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_HOST,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    INFO_PATH,
    PLATFORMS,
    STATUS_PATH,
)

_LOGGER = logging.getLogger(__name__)


class AltiliaCoordinator(DataUpdateCoordinator[dict]):
    def __init__(self, hass: HomeAssistant, host: str, port: int, interval: int) -> None:
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.info: dict = {}
        session = async_get_clientsession(hass)
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=interval),
        )
        self._session = session

    async def _async_update_data(self) -> dict:
        try:
            timeout = ClientTimeout(total=8)
            async with self._session.get(
                f"{self.base_url}{STATUS_PATH}", timeout=timeout
            ) as response:
                response.raise_for_status()
                data = await response.json(content_type=None)

            if not isinstance(data, dict):
                raise UpdateFailed("Status response is not a JSON object")

            # /info is comparatively static, so refresh it only when needed.
            if not self.info:
                try:
                    async with self._session.get(
                        f"{self.base_url}{INFO_PATH}", timeout=timeout
                    ) as response:
                        response.raise_for_status()
                        info = await response.json(content_type=None)
                        if isinstance(info, dict):
                            self.info = info
                except Exception as err:
                    _LOGGER.debug("Unable to read Altilia info endpoint: %s", err)

            return data

        except Exception as err:
            raise UpdateFailed(f"Unable to fetch Altilia EMS: {err}") from err


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = AltiliaCoordinator(
        hass,
        entry.data[CONF_HOST],
        entry.data[CONF_PORT],
        entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unloaded
