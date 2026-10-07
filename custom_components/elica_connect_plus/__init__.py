"""Elica Connect integration for Home Assistant.

Protocol analysis:
  - Device: ESP32-C6, hostname ELC-HOOD-ESP32C6-F0F5BD02CF3D
  - Cloud MQTT broker: cloudprodmqtt.elica.com:8883 (TLS)
  - Backend: AWS ELB eu-central-1 (Reply S.p.A. eiot platform)
  - REST API: https://cloudprod.elica.com/eiot-api/v1/
  - No local API available
"""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DOMAIN,
    CONF_DEVICE_ID,
    CONF_DEVICE_NAME,
    OPT_KEEPALIVE_MINUTES,
    OPT_AGGRESSIVE_KEEPALIVE,
    OPT_MQTT_HOST,
    OPT_MQTT_PORT,
    DEFAULT_MQTT_HOST,
    DEFAULT_MQTT_PORT,
)
from .coordinator import ElicaConnectAPI, ElicaConnectCoordinator, InvalidAuth

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.FAN,
    Platform.LIGHT,
    Platform.NUMBER,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.TEXT,
]

type ElicaConfigEntry = ConfigEntry[ElicaConnectCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: ElicaConfigEntry) -> bool:
    """Set up Elica Connect from a config entry."""
    session = async_get_clientsession(hass)
    api = ElicaConnectAPI(
        session,
        entry.data[CONF_EMAIL],
        entry.data[CONF_PASSWORD],
    )

    # Validate credentials up-front so a wrong password triggers the
    # reauth flow instead of an endless setup-retry loop.
    try:
        await api.async_login()
    except InvalidAuth as err:
        raise ConfigEntryAuthFailed("Elica credentials rejected") from err

    coordinator = ElicaConnectCoordinator(
        hass,
        entry,
        api,
        device_id=entry.data[CONF_DEVICE_ID],
        device_name=entry.data[CONF_DEVICE_NAME],
        keepalive_minutes=entry.options.get(OPT_KEEPALIVE_MINUTES, 0),
        aggressive_keepalive=entry.options.get(OPT_AGGRESSIVE_KEEPALIVE, False),
        mqtt_host=entry.options.get(OPT_MQTT_HOST, DEFAULT_MQTT_HOST),
        mqtt_port=entry.options.get(OPT_MQTT_PORT, DEFAULT_MQTT_PORT),
    )

    await coordinator.async_config_entry_first_refresh()

    # Start MQTT push updates (cuid is now available from first REST poll)
    coordinator.async_start_mqtt()

    entry.runtime_data = coordinator

    # On HA >= 2025.8 the options flow subclasses OptionsFlowWithReload and
    # reloads the entry by itself; the manual listener (deprecated in HA
    # 2026.6, removed in 2026.12) is only registered on older versions.
    from .config_flow import HAS_OPTIONS_FLOW_WITH_RELOAD

    if not HAS_OPTIONS_FLOW_WITH_RELOAD:
        entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ElicaConfigEntry) -> bool:
    """Unload a config entry."""
    if unloaded := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        entry.runtime_data.stop_mqtt()
    return unloaded


async def _async_update_listener(hass: HomeAssistant, entry: ElicaConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)
