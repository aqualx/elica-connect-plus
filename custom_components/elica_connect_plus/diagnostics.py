"""Diagnostics support for Elica Connect."""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant

from .const import CONF_DEVICE_ID

# Anything that identifies the account or the physical device.
TO_REDACT = {
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_DEVICE_ID,
    "id",
    "deviceId",
    "serialNumber",
    "serial",
    "cuid",
    "macAddress",
    "mac",
    "hostname",
    "owner",
    "ownerEmail",
    "latitude",
    "longitude",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data
    return {
        "entry_data": async_redact_data(dict(entry.data), TO_REDACT),
        "device_raw": async_redact_data(coordinator.device_raw, TO_REDACT),
        # dataModel capability cache: {capability_code: value}
        "state_cache": {str(k): v for k, v in (coordinator.data or {}).items()},
        "mqtt_active": coordinator.mqtt_active,
        "update_interval_seconds": coordinator.update_interval.total_seconds()
        if coordinator.update_interval
        else None,
        "last_update_success": coordinator.last_update_success,
    }
