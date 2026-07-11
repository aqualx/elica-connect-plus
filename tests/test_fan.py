"""Tests for the fan entity: setup + optimistic state behaviour."""
from unittest.mock import patch

from homeassistant.components.fan import (
    ATTR_PERCENTAGE,
    DOMAIN as FAN_DOMAIN,
    SERVICE_SET_PERCENTAGE,
)
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.elica_connect_plus.const import (
    DOMAIN,
    CONF_DEVICE_ID,
    CONF_DEVICE_NAME,
)

COORD = "custom_components.elica_connect_plus.coordinator"

DEVICE_STATE = {
    "cuid": "CUID-1",
    "dataModel": {"64": 1, "110": 0, "96": 0},
    "filters": [{"efficiency": 87, "status": "OK", "type": "grease"}],
}


async def setup_integration(hass, options: dict | None = None) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="HOOD123",
        data={
            CONF_EMAIL: "a@b.c",
            CONF_PASSWORD: "pw",
            CONF_DEVICE_ID: "HOOD123",
            CONF_DEVICE_NAME: "Cappa Cucina",
        },
        options=options or {},
    )
    entry.add_to_hass(hass)
    with patch(f"{COORD}.ElicaConnectAPI.async_login"), patch(
        f"{COORD}.ElicaConnectAPI.async_get_device_state",
        return_value=DEVICE_STATE,
    ), patch(
        f"{COORD}.ElicaConnectCoordinator.async_start_mqtt"
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry


async def test_entities_created(hass):
    await setup_integration(hass)

    fan = hass.states.get("fan.cappa_cucina_fan")
    assert fan is not None
    assert fan.state == "off"

    sensor = hass.states.get("sensor.cappa_cucina_filter")
    assert sensor is not None
    assert sensor.state == "87"


async def test_set_percentage_is_optimistic_and_sends_command(hass):
    await setup_integration(hass)

    with patch(
        f"{COORD}.ElicaConnectAPI.async_send_command"
    ) as mock_cmd:
        await hass.services.async_call(
            FAN_DOMAIN,
            SERVICE_SET_PERCENTAGE,
            {"entity_id": "fan.cappa_cucina_fan", ATTR_PERCENTAGE: 50},
            blocking=True,
        )

    # Command sent with the right capability payload (speed 2 = medium)
    mock_cmd.assert_awaited_once()
    assert mock_cmd.call_args.args[1] == {64: 1, 110: 2}

    # State reflects the command immediately (optimistic), before any poll
    fan = hass.states.get("fan.cappa_cucina_fan")
    assert fan.state == "on"
    assert fan.attributes[ATTR_PERCENTAGE] == 50


async def test_failed_command_reverts_optimistic_state(hass):
    await setup_integration(hass)

    with patch(
        f"{COORD}.ElicaConnectAPI.async_send_command",
        side_effect=RuntimeError("cloud down"),
    ):
        try:
            await hass.services.async_call(
                FAN_DOMAIN,
                SERVICE_SET_PERCENTAGE,
                {"entity_id": "fan.cappa_cucina_fan", ATTR_PERCENTAGE: 75},
                blocking=True,
            )
        except Exception:
            pass

    fan = hass.states.get("fan.cappa_cucina_fan")
    assert fan.state == "off"  # reverted, not lying about speed 3
