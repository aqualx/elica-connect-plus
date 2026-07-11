"""Fan platform for Elica Connect (hood motor)."""
from __future__ import annotations

import logging
import time
from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    MANUFACTURER,
    CAP_FAN_SPEED,
    CAP_FAN_MODE,
    FAN_SPEED_TO_PCT,
    FAN_CMD,
    OPTIMISTIC_TIMEOUT,
    OPT_FAN_AUTO_VALUE,
    PRESET_AUTO,
    FAN_SPEED_PRESETS,
)
from .coordinator import ElicaConnectCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: ElicaConnectCoordinator = entry.runtime_data
    async_add_entities([ElicaHoodFan(coordinator, entry)])


class ElicaHoodFan(CoordinatorEntity, FanEntity):
    """Elica hood fan.

    Speed levels:
      0 = off          → {64:1, 110:0}
      1 = low   (25%)  → {64:1, 110:1}
      2 = medium (50%) → {64:1, 110:2}
      3 = high  (75%)  → {64:1, 110:3}
      4 = boost (100%) → {64:4}
    """

    _attr_has_entity_name = True
    _attr_translation_key = "fan"
    _attr_supported_features = (
        FanEntityFeature.SET_SPEED
        | FanEntityFeature.TURN_ON
        | FanEntityFeature.TURN_OFF
    )

    def __init__(self, coordinator: ElicaConnectCoordinator, entry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.data['device_id']}_fan"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.data["device_id"])},
            "name": coordinator.device_name,
            "manufacturer": MANUFACTURER,
            "model": "Elica Connect hood (verified: Illusion)",
            "serial_number": entry.data["device_id"],
        }
        self._optimistic_speed: int | None = None
        self._optimistic_since: float = 0.0
        # cap-64 value meaning "auto" (0 = feature disabled, see Options)
        self._auto_value: int = entry.options.get(OPT_FAN_AUTO_VALUE, 0)
        self._optimistic_auto: bool | None = None
        # Named speed presets are always available; Auto only if configured
        self._attr_supported_features |= FanEntityFeature.PRESET_MODE
        presets = [PRESET_AUTO] if self._auto_value else []
        self._attr_preset_modes = presets + list(FAN_SPEED_PRESETS)

    def _reported_speed(self) -> int:
        """Speed as reported by the coordinator (ignoring optimistic state)."""
        caps = self.coordinator.data or {}
        if caps.get(CAP_FAN_MODE) == 4:
            return 4  # boost
        return caps.get(CAP_FAN_SPEED, 0)

    def _handle_coordinator_update(self) -> None:
        """Drop optimistic state only once it's confirmed or stale.

        A REST poll that was already in flight when the command was sent can
        deliver *old* data right after the command; unconditionally clearing
        the optimistic value there makes the UI bounce back. Keep it until
        the device echoes the commanded speed (MQTT push) or a timeout passes.
        """
        if self._optimistic_speed is not None and (
            self._reported_speed() == self._optimistic_speed
            or time.monotonic() - self._optimistic_since > OPTIMISTIC_TIMEOUT
        ):
            self._optimistic_speed = None
        if self._optimistic_auto is not None and (
            self._reported_auto() == self._optimistic_auto
            or time.monotonic() - self._optimistic_since > OPTIMISTIC_TIMEOUT
        ):
            self._optimistic_auto = None
        super()._handle_coordinator_update()

    def _reported_auto(self) -> bool:
        caps = self.coordinator.data or {}
        return bool(self._auto_value) and caps.get(CAP_FAN_MODE) == self._auto_value

    @property
    def _is_auto(self) -> bool:
        if self._optimistic_auto is not None:
            return self._optimistic_auto
        return self._reported_auto()

    @property
    def preset_mode(self) -> str | None:
        if self._is_auto:
            return PRESET_AUTO
        speed = self._current_speed
        for name, value in FAN_SPEED_PRESETS.items():
            if value == speed:
                return name
        return None

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        if preset_mode in FAN_SPEED_PRESETS:
            await self._send(FAN_SPEED_PRESETS[preset_mode])
            return
        if preset_mode != PRESET_AUTO or not self._auto_value:
            return
        self._optimistic_auto = True
        self._optimistic_since = time.monotonic()
        self.async_write_ha_state()
        try:
            await self.coordinator.api.async_send_command(
                self.coordinator.device_id, {CAP_FAN_MODE: self._auto_value}
            )
        except Exception:
            self._optimistic_auto = None
            self.async_write_ha_state()
            raise

    @property
    def _current_speed(self) -> int:
        """Return current speed as 0-4 integer."""
        if self._optimistic_speed is not None:
            return self._optimistic_speed
        return self._reported_speed()

    @property
    def is_on(self) -> bool:
        return self._current_speed > 0 or self._is_auto

    @property
    def percentage(self) -> int | None:
        return FAN_SPEED_TO_PCT.get(self._current_speed, 0)

    @property
    def speed_count(self) -> int:
        return 4  # speeds 1–4

    async def async_turn_on(self, percentage: int | None = None, preset_mode: str | None = None, **kwargs: Any) -> None:
        speed = self._pct_to_speed(percentage if percentage is not None else 25)
        await self._send(speed)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._send(0)

    async def async_set_percentage(self, percentage: int) -> None:
        await self._send(self._pct_to_speed(percentage))

    async def _send(self, speed: int) -> None:
        self._optimistic_speed = speed
        self._optimistic_auto = False  # any manual speed command exits auto
        self._optimistic_since = time.monotonic()
        self.async_write_ha_state()
        caps = FAN_CMD[speed]
        try:
            await self.coordinator.api.async_send_command(self.coordinator.device_id, caps)
        except Exception:
            # Command failed: revert the optimistic state instead of lying.
            self._optimistic_speed = None
            self.async_write_ha_state()
            raise

    @staticmethod
    def _pct_to_speed(pct: int) -> int:
        if pct == 0:
            return 0
        if pct <= 25:
            return 1
        if pct <= 50:
            return 2
        if pct <= 75:
            return 3
        return 4
