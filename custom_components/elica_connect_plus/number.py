"""Number platform for Elica Connect Plus: native auto-off timer."""
from __future__ import annotations

import logging
import time

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    MANUFACTURER,
    OPT_CAP_TIMER,
    TIMER_MAX_MINUTES,
    OPTIMISTIC_TIMEOUT,
)
from .coordinator import ElicaConnectCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: ElicaConnectCoordinator = entry.runtime_data
    timer_cap = entry.options.get(OPT_CAP_TIMER, 0)
    if timer_cap:
        async_add_entities([ElicaTimerNumber(coordinator, entry, timer_cap)])


class ElicaTimerNumber(CoordinatorEntity, NumberEntity):
    """Auto-off timer in minutes.

    Writing a value starts a firmware countdown; the device reports the
    remaining minutes back on the same capability, so this entity doubles as
    the live countdown. 0 = timer off. Enabled only when the timer capability
    code is configured in Options.
    """

    _attr_has_entity_name = True
    _attr_translation_key = "timer"
    _attr_native_min_value = 0
    _attr_native_max_value = TIMER_MAX_MINUTES
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:timer-outline"

    def __init__(
        self, coordinator: ElicaConnectCoordinator, entry, timer_cap: int
    ) -> None:
        super().__init__(coordinator)
        self._cap = timer_cap
        self._attr_unique_id = f"{entry.data['device_id']}_timer"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.data["device_id"])},
            "name": coordinator.device_name,
            "manufacturer": MANUFACTURER,
            "model": "Elica Connect hood (verified: Illusion)",
            "serial_number": entry.data["device_id"],
        }
        self._optimistic: int | None = None
        self._optimistic_since: float = 0.0

    def _reported(self) -> int:
        return (self.coordinator.data or {}).get(self._cap, 0)

    def _handle_coordinator_update(self) -> None:
        # Drop the optimistic value once the device confirms it, or after a
        # timeout. Note: the firmware then counts the value down on its own,
        # which arrives as normal coordinator updates.
        if self._optimistic is not None and (
            self._reported() == self._optimistic
            or time.monotonic() - self._optimistic_since > OPTIMISTIC_TIMEOUT
        ):
            self._optimistic = None
        super()._handle_coordinator_update()

    @property
    def native_value(self) -> int:
        if self._optimistic is not None:
            return self._optimistic
        return self._reported()

    async def async_set_native_value(self, value: float) -> None:
        minutes = max(0, min(int(value), TIMER_MAX_MINUTES))
        self._optimistic = minutes
        self._optimistic_since = time.monotonic()
        self.async_write_ha_state()
        try:
            await self.coordinator.api.async_send_command(
                self.coordinator.device_id, {self._cap: minutes}
            )
        except Exception:
            self._optimistic = None
            self.async_write_ha_state()
            raise
