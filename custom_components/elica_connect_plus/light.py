"""Light platform for Elica Connect Plus.

Two lights share the same implementation:
- Main light: brightness cap 96 (fixed), optional color cap from Options
- Ambient light: brightness + color caps entirely from Options (entity is
  created only when the brightness cap is configured)
"""
from __future__ import annotations

import logging
import time
from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_EFFECT,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    MANUFACTURER,
    CAP_LIGHT_BRIGHTNESS,
    LIGHT_BRIGHTNESS_MAX_HA,
    LIGHT_BRIGHTNESS_MAX_ELICA,
    OPTIMISTIC_TIMEOUT,
    OPT_CAP_LIGHT_COLOR,
    OPT_CAP_AMBIENT_BRIGHTNESS,
    OPT_CAP_AMBIENT_COLOR,
    LIGHT_COLOR_MIN_KELVIN,
    LIGHT_COLOR_MAX_KELVIN,
    LIGHT_EFFECTS,
)
from .coordinator import ElicaConnectCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: ElicaConnectCoordinator = entry.runtime_data

    entities = [
        ElicaLight(
            coordinator,
            entry,
            translation_key="light",
            brightness_cap=CAP_LIGHT_BRIGHTNESS,
            color_cap=entry.options.get(OPT_CAP_LIGHT_COLOR, 0),
        )
    ]

    ambient_brightness = entry.options.get(OPT_CAP_AMBIENT_BRIGHTNESS, 0)
    if ambient_brightness:
        entities.append(
            ElicaLight(
                coordinator,
                entry,
                translation_key="ambient_light",
                brightness_cap=ambient_brightness,
                color_cap=entry.options.get(OPT_CAP_AMBIENT_COLOR, 0),
            )
        )

    async_add_entities(entities)


class ElicaLight(CoordinatorEntity, LightEntity):
    """A hood light: brightness 0–100, optional tunable-white color 0–100.

    Optimistic state is kept until the device confirms the commanded value
    (MQTT echo) or a timeout elapses, and rolled back on cloud errors.
    """

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ElicaConnectCoordinator,
        entry,
        *,
        translation_key: str,
        brightness_cap: int,
        color_cap: int,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._brightness_cap = brightness_cap
        self._color_cap = color_cap
        self._attr_translation_key = translation_key
        self._attr_unique_id = f"{entry.data['device_id']}_{translation_key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.data["device_id"])},
            "name": coordinator.device_name,
            "manufacturer": MANUFACTURER,
            "model": "Elica Connect hood (verified: Illusion)",
            "serial_number": entry.data["device_id"],
        }
        self._optimistic_brightness: int | None = None
        self._optimistic_color: int | None = None
        self._optimistic_since: float = 0.0

        if self._color_cap:
            self._attr_color_mode = ColorMode.COLOR_TEMP
            self._attr_supported_color_modes = {ColorMode.COLOR_TEMP}
            self._attr_min_color_temp_kelvin = LIGHT_COLOR_MIN_KELVIN
            self._attr_max_color_temp_kelvin = LIGHT_COLOR_MAX_KELVIN
            # Named warm→cold presets, exposed as effects
            self._attr_supported_features = LightEntityFeature.EFFECT
            self._attr_effect_list = list(LIGHT_EFFECTS)
        else:
            self._attr_color_mode = ColorMode.BRIGHTNESS
            self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}

    # ------------------------------------------------------------- state

    def _reported_brightness(self) -> int:
        return (self.coordinator.data or {}).get(self._brightness_cap, 0)

    def _reported_color_pct(self) -> int:
        return (self.coordinator.data or {}).get(self._color_cap, 0)

    def _handle_coordinator_update(self) -> None:
        """Clear optimistic state only when confirmed by the device or stale."""
        if self._optimistic_brightness is not None and (
            self._reported_brightness() == self._optimistic_brightness
            or time.monotonic() - self._optimistic_since > OPTIMISTIC_TIMEOUT
        ):
            self._optimistic_brightness = None
        if self._optimistic_color is not None and (
            self._reported_color_pct() == self._optimistic_color
            or time.monotonic() - self._optimistic_since > OPTIMISTIC_TIMEOUT
        ):
            self._optimistic_color = None
        super()._handle_coordinator_update()

    @property
    def _brightness_elica(self) -> int:
        if self._optimistic_brightness is not None:
            return self._optimistic_brightness
        return self._reported_brightness()

    def _color_pct(self) -> int:
        if self._optimistic_color is not None:
            return self._optimistic_color
        return self._reported_color_pct()

    @property
    def is_on(self) -> bool:
        return self._brightness_elica > 0

    @property
    def brightness(self) -> int | None:
        return round(
            self._brightness_elica * LIGHT_BRIGHTNESS_MAX_HA / LIGHT_BRIGHTNESS_MAX_ELICA
        )

    @property
    def effect(self) -> str | None:
        if not self._color_cap:
            return None
        pct = self._color_pct()
        for name, value in LIGHT_EFFECTS.items():
            if value == pct:
                return name
        return None

    @property
    def color_temp_kelvin(self) -> int | None:
        if not self._color_cap:
            return None
        span = LIGHT_COLOR_MAX_KELVIN - LIGHT_COLOR_MIN_KELVIN
        return round(LIGHT_COLOR_MIN_KELVIN + self._color_pct() * span / 100)

    @staticmethod
    def _kelvin_to_pct(kelvin: int) -> int:
        span = LIGHT_COLOR_MAX_KELVIN - LIGHT_COLOR_MIN_KELVIN
        pct = round((kelvin - LIGHT_COLOR_MIN_KELVIN) * 100 / span)
        return max(0, min(100, pct))

    # ---------------------------------------------------------- commands

    async def async_turn_on(self, **kwargs: Any) -> None:
        brightness_ha = kwargs.get(ATTR_BRIGHTNESS)
        if brightness_ha is not None:
            elica_val = round(
                brightness_ha * LIGHT_BRIGHTNESS_MAX_ELICA / LIGHT_BRIGHTNESS_MAX_HA
            )
            elica_val = max(1, min(elica_val, LIGHT_BRIGHTNESS_MAX_ELICA))
        else:
            current = self._brightness_elica
            elica_val = current if current > 0 else LIGHT_BRIGHTNESS_MAX_ELICA

        caps: dict[int, int] = {self._brightness_cap: elica_val}

        color_pct: int | None = None
        effect = kwargs.get(ATTR_EFFECT)
        if effect in LIGHT_EFFECTS and self._color_cap:
            color_pct = LIGHT_EFFECTS[effect]
        else:
            kelvin = kwargs.get(ATTR_COLOR_TEMP_KELVIN)
            if kelvin is not None and self._color_cap:
                color_pct = self._kelvin_to_pct(int(kelvin))

        if color_pct is not None:
            caps[self._color_cap] = color_pct
            self._optimistic_color = color_pct

        await self._send_caps(caps, elica_val)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._send_caps({self._brightness_cap: 0}, 0)

    async def _send_caps(self, caps: dict[int, int], elica_val: int) -> None:
        self._optimistic_brightness = elica_val
        self._optimistic_since = time.monotonic()
        self.async_write_ha_state()
        try:
            await self.coordinator.api.async_send_command(
                self.coordinator.device_id, caps
            )
        except Exception:
            self._optimistic_brightness = None
            self._optimistic_color = None
            self.async_write_ha_state()
            raise
