from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import AltiliaCoordinator
from .const import DOMAIN


@dataclass(frozen=True)
class Description:
    key: str
    name: str
    unit: str | None
    device_class: SensorDeviceClass | None
    state_class: str | None
    value_fn: Callable[[dict], Any]
    entity_category: EntityCategory | None = None
    enabled_by_default: bool = True


def get(data: dict, *path: str, default=None):
    cur = data
    for part in path:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(part, default)
    return cur


DESCRIPTIONS = [
    Description("battery_power", "Battery power", UnitOfPower.WATT, SensorDeviceClass.POWER, "measurement", lambda d: get(d, "battery", "power_w")),
    Description("battery_soc", "Battery state of charge", PERCENTAGE, SensorDeviceClass.BATTERY, "measurement", lambda d: get(d, "battery", "soc_pct")),
    Description("battery_voltage", "Battery voltage", UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, "measurement", lambda d: get(d, "battery", "voltage_v")),
    Description("battery_current", "Battery current", UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, "measurement", lambda d: get(d, "battery", "current_a")),
    Description("battery_temperature", "Battery temperature", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, "measurement", lambda d: get(d, "battery", "temperature_c")),
    Description("solar_power", "Solar power", UnitOfPower.WATT, SensorDeviceClass.POWER, "measurement", lambda d: get(d, "solar", "power_w")),
    Description("grid_power", "Grid power", UnitOfPower.WATT, SensorDeviceClass.POWER, "measurement", lambda d: get(d, "grid", "power_w")),
    Description("grid_frequency", "Grid frequency", UnitOfFrequency.HERTZ, SensorDeviceClass.FREQUENCY, "measurement", lambda d: get(d, "grid", "frequency_hz")),
    Description("load_power", "Load power", UnitOfPower.WATT, SensorDeviceClass.POWER, "measurement", lambda d: get(d, "load", "power_w")),
    Description("inverter_power", "Inverter power", UnitOfPower.WATT, SensorDeviceClass.POWER, "measurement", lambda d: get(d, "inverter", "power_w")),
    Description("inverter_temperature", "Inverter temperature", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, "measurement", lambda d: get(d, "inverter", "temperature_c")),
    Description("grid_import_total", "Grid import total", UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, "total_increasing", lambda d: get(d, "energy_total_kwh", "grid_import")),
    Description("grid_export_total", "Grid export total", UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, "total_increasing", lambda d: get(d, "energy_total_kwh", "grid_export")),
    Description("solar_total", "Solar energy total", UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, "total_increasing", lambda d: get(d, "energy_total_kwh", "solar")),
    Description("load_total", "Load energy total", UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, "total_increasing", lambda d: get(d, "energy_total_kwh", "load")),
    Description("inverter_total", "Inverter energy total", UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, "total_increasing", lambda d: get(d, "energy_total_kwh", "inverter")),
    Description("uptime", "Uptime", "s",None, "measurement", lambda d: get(d, "uptime_s"), entity_category=EntityCategory.DIAGNOSTIC),
    Description("active_faults", "Active faults", None, None, "measurement", lambda d: get(d, "faults", "count", default=0), entity_category=EntityCategory.DIAGNOSTIC),
    Description("battery_state", "Battery state", None, None, None, lambda d: get(d, "battery", "state")),
    Description("inverter_run_state", "Inverter run state", None, None, None, lambda d: get(d, "inverter", "run_state")),
    Description("ems_mode", "EMS mode", None, None, None, lambda d: get(d, "inverter", "ems_mode")),
]


class AltiliaSensor(CoordinatorEntity[AltiliaCoordinator], SensorEntity):
    def __init__(self, coordinator, description: Description, device_id: str):
        super().__init__(coordinator)
        self.entity_description = SensorEntityDescription(
            key=description.key,
            name=description.name,
            native_unit_of_measurement=description.unit,
            device_class=description.device_class,
            state_class=description.state_class,
            entity_category=description.entity_category,
            entity_registry_enabled_default=description.enabled_by_default,
        )
        self._description = description
        self._attr_unique_id = f"{device_id}_{description.key}"
        self._attr_has_entity_name = True
        self._attr_name = description.name
        self._attr_native_unit_of_measurement = description.unit
        self._attr_device_class = description.device_class
        self._attr_state_class = description.state_class
        self._attr_entity_category = description.entity_category
        self._attr_entity_registry_enabled_default = description.enabled_by_default

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
    def native_value(self):
        value = self._description.value_fn(self.coordinator.data)
        return value


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    info = coordinator.info
    device_id = str(info.get("device_id", coordinator.host))
    async_add_entities(
        [AltiliaSensor(coordinator, desc, device_id) for desc in DESCRIPTIONS]
    )
