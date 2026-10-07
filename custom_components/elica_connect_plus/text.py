"""Text platform for Elica Connect diagnostic payloads."""
from __future__ import annotations

import json
from typing import Any

from homeassistant.components.text import TextEntity, TextMode
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import ElicaConnectCoordinator

PAYLOAD_PREVIEW_LIMIT = 32


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: ElicaConnectCoordinator = entry.runtime_data
    async_add_entities([ElicaLatestRawMqttText(coordinator, entry)])


class ElicaLatestRawMqttText(CoordinatorEntity, TextEntity):
    """Latest raw MQTT payload in a text-oriented entity view."""

    _attr_has_entity_name = True
    _attr_translation_key = "latest_raw_mqtt_payload"
    _attr_icon = "mdi:code-json"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False
    _attr_mode = TextMode.TEXT

    def __init__(self, coordinator: ElicaConnectCoordinator, entry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.data['device_id']}_latest_raw_mqtt_payload"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.data["device_id"])},
            "name": coordinator.device_name,
            "manufacturer": MANUFACTURER,
            "model": "Elica Connect hood (verified: Illusion)",
            "serial_number": entry.data["device_id"],
        }

    async def async_added_to_hass(self) -> None:
        """Subscribe to debug-buffer updates."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, self.coordinator.debug_signal, self._handle_debug_update
            )
        )

    def _handle_debug_update(self) -> None:
        self.schedule_update_ha_state()

    @staticmethod
    def _truncated_text(value: str | None, limit: int) -> str | None:
        if value is None or len(value) <= limit:
            return value
        return f"{value[:limit - 3]}..."

    @property
    def native_value(self) -> str | None:
        return self._truncated_text(self.coordinator.latest_raw_mqtt_payload, 255)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        payload = self.coordinator.latest_raw_mqtt_payload
        try:
            payload_json = json.loads(payload) if payload else None
        except json.JSONDecodeError:
            payload_json = None
        return {
            "enabled": self.coordinator.debug_ui_enabled,
            "timestamp": self.coordinator.latest_raw_mqtt_timestamp,
            "payload": payload,
            "payload_json": payload_json,
            "payload_preview": self._truncated_text(payload, PAYLOAD_PREVIEW_LIMIT),
            "payload_truncated": bool(payload and len(payload) > 255),
        }

    async def async_set_value(self, value: str) -> None:
        """The latest raw MQTT payload is read-only."""
        raise HomeAssistantError("Latest raw MQTT payload is read-only")
