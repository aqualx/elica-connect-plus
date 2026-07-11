"""Sensor platform for Elica Connect (filter efficiency)."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, OPT_CAP_AIR_QUALITY, AIR_QUALITY_LEVELS
from .coordinator import ElicaConnectCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: ElicaConnectCoordinator = entry.runtime_data
    entities: list[SensorEntity] = [ElicaFilterSensor(coordinator, entry)]
    if entry.options.get(OPT_CAP_AIR_QUALITY, 0):
        entities.append(ElicaAirQualitySensor(coordinator, entry))
    async_add_entities(entities)


class ElicaFilterSensor(CoordinatorEntity, SensorEntity):
    """Filter efficiency sensor — 100% = clean, lower = needs cleaning.

    Data comes from device JSON filters[0].efficiency (not a dataModel capability).
    """

    _attr_has_entity_name = True
    _attr_translation_key = "filter"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:air-filter"

    def __init__(self, coordinator: ElicaConnectCoordinator, entry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.data['device_id']}_filter"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.data["device_id"])},
            "name": coordinator.device_name,
            "manufacturer": MANUFACTURER,
            "model": "Elica Connect hood (verified: Illusion)",
            "serial_number": entry.data["device_id"],
        }

    def _filter(self) -> dict | None:
        filters = self.coordinator.device_raw.get("filters") or []
        return filters[0] if filters else None

    @property
    def native_value(self) -> int | None:
        f = self._filter()
        return f.get("efficiency") if f else None

    @property
    def available(self) -> bool:
        # Keep CoordinatorEntity's cloud-reachability check AND require data.
        f = self._filter()
        return super().available and bool(f and f.get("efficiency") is not None)

    @property
    def extra_state_attributes(self) -> dict:
        f = self._filter()
        if not f:
            return {}
        return {
            "status": f.get("status"),
            "filter_type": f.get("type"),
            "last_reset": f.get("lastReset"),
        }


class ElicaAirQualitySensor(CoordinatorEntity, SensorEntity):
    """Air quality level reported by the hood's onboard sensor.

    Enabled only when the dataModel capability code is configured in the
    integration Options. Capability 112 (dataModelIdx 8) uses a 1–5 scale
    matching the Elica app labels Ottima/Buona/Media/Scarsa/Pessima; the
    raw number is kept in the `level` attribute for numeric automations.
    """

    _attr_has_entity_name = True
    _attr_translation_key = "air_quality"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = list(AIR_QUALITY_LEVELS.values())
    _attr_icon = "mdi:weather-windy"

    def __init__(self, coordinator: ElicaConnectCoordinator, entry) -> None:
        super().__init__(coordinator)
        self._cap: int = entry.options[OPT_CAP_AIR_QUALITY]
        self._attr_unique_id = f"{entry.data['device_id']}_air_quality"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.data["device_id"])},
            "name": coordinator.device_name,
            "manufacturer": MANUFACTURER,
            "model": "Elica Connect hood (verified: Illusion)",
            "serial_number": entry.data["device_id"],
        }

    @property
    def _raw(self) -> int | None:
        return (self.coordinator.data or {}).get(self._cap)

    @property
    def native_value(self) -> str | None:
        return AIR_QUALITY_LEVELS.get(self._raw)

    @property
    def extra_state_attributes(self) -> dict:
        return {"level": self._raw}

    @property
    def available(self) -> bool:
        # Cap 112 is published only while the sensor is active (auto mode):
        # stay unavailable after a restart until the first value arrives,
        # and if the cloud reports an out-of-scale value.
        return super().available and AIR_QUALITY_LEVELS.get(self._raw) is not None
