"""Switch platform for Elica Connect UI debug logging."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import ElicaConnectCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: ElicaConnectCoordinator = entry.runtime_data
    async_add_entities([ElicaDebugLoggingSwitch(coordinator, entry)])


class ElicaDebugLoggingSwitch(CoordinatorEntity, SwitchEntity):
    """Enable/disable capture of the latest raw MQTT payload."""

    _attr_has_entity_name = True
    _attr_translation_key = "debug_logging"
    _attr_icon = "mdi:bug-outline"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator: ElicaConnectCoordinator, entry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.data['device_id']}_debug_logging"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.data["device_id"])},
            "name": coordinator.device_name,
            "manufacturer": MANUFACTURER,
            "model": "Elica Connect hood (verified: Illusion)",
            "serial_number": entry.data["device_id"],
        }

    async def async_added_to_hass(self) -> None:
        """Restore switch state and subscribe to coordinator debug updates."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, self.coordinator.debug_signal, self._handle_debug_update
            )
        )

    def _handle_debug_update(self) -> None:
        self.schedule_update_ha_state()

    @property
    def is_on(self) -> bool:
        return self.coordinator.debug_ui_enabled

    async def async_turn_on(self, **kwargs) -> None:
        self.coordinator.set_debug_ui_enabled(True)

    async def async_turn_off(self, **kwargs) -> None:
        self.coordinator.set_debug_ui_enabled(False)
