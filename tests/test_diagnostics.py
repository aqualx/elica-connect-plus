"""Smoke test for the diagnostics module (redaction + shape)."""
from custom_components.elica_connect_plus.diagnostics import (
    async_get_config_entry_diagnostics,
)

from tests.test_fan import setup_integration


async def test_diagnostics_redacts_secrets(hass):
    entry = await setup_integration(hass)

    diag = await async_get_config_entry_diagnostics(hass, entry)

    assert diag["entry_data"]["email"] == "**REDACTED**"
    assert diag["entry_data"]["password"] == "**REDACTED**"
    assert diag["entry_data"]["device_id"] == "**REDACTED**"
    assert diag["device_raw"]["cuid"] == "**REDACTED**"
    # Non-sensitive payload survives
    assert diag["state_cache"]["110"] == 0
    assert diag["last_update_success"] is True
    assert diag["mqtt_active"] is False  # patched out in setup_integration
