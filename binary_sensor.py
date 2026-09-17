from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import (
    EntityCategory,
)
from . import AltiliaCoordinator
from .const import DOMAIN


@dataclass(frozen=True)
class BinaryDescription:
    key: str
    name: str
    device_class: BinarySensorDeviceClass | None
    value_fn: Callable[[dict], Any]
    entity_category: EntityCategory | None = None


def get(data: dict, *path: str, default=None):
    cur = data
    for part in path:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(part, default)
    return cur


DESCRIPTIONS = [
    BinaryDescription("battery_charging", "Battery charging", BinarySensorDeviceClass.BATTERY_CHARGING, lambda d: get(d, "battery", "charging")),
    BinaryDescription("battery_discharging", "Battery discharging", None, lambda d: get(d, "battery", "discharging")),
    BinaryDescription("battery_floor_tripped", "Battery SOC floor tripped", None, lambda d: get(d, "battery", "floor_tripped"), EntityCategory.DIAGNOSTIC),
    BinaryDescription("inverter_fault", "Inverter fault", BinarySensorDeviceClass.PROBLEM, lambda d: get(d, "inverter", "fault"), EntityCategory.DIAGNOSTIC),
    BinaryDescription("fault", "Active fault", BinarySensorDeviceClass.PROBLEM, lambda d: get(d, "faults", "any"), EntityCategory.DIAGNOSTIC),
    BinaryDescription("modbus_online", "Modbus online", BinarySensorDeviceClass.CONNECTIVITY, lambda d: get(d, "online", "modbus"), EntityCategory.DIAGNOSTIC),
    BinaryDescription("server_online", "Server online", BinarySensorDeviceClass.CONNECTIVITY, lambda d: get(d, "online", "server"), EntityCategory.DIAGNOSTIC),
]


class AltiliaBinarySensor(CoordinatorEntity[AltiliaCoordinator], BinarySensorEntity):
    def __init__(self, coordinator, description: BinaryDescription, device_id: str):
        super().__init__(coordinator)
        self._description = description
        self._attr_unique_id = f"{device_id}_{description.key}"
        self._attr_has_entity_name = True
        self._attr_name = description.name
        self._attr_device_class = description.device_class
        self._attr_entity_category = (
            EntityCategory(description.entity_category)
            if description.entity_category is not None
            else None
        )

    @property
    def device_info(self) -> DeviceInfo:
        info = self.coordinator.info
        device_id = str(info.get("device_id", self.coordinator.host))
        return DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=info.get("model_name") or info.get("model") or "Altilia EMS",
            manufacturer="Altilia",
            model=info.get("model"),
            sw_version=info.get("firmware"),
            configuration_url=f"{self.coordinator.base_url}/",
        )

    @property
    def is_on(self):
        value = self._description.value_fn(self.coordinator.data)
        return bool(value) if value is not None else None


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    info = coordinator.info
    device_id = str(info.get("device_id", coordinator.host))
    async_add_entities(
        [AltiliaBinarySensor(coordinator, desc, device_id) for desc in DESCRIPTIONS]
    )
