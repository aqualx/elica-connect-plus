"""Tests for the Elica Connect config flow."""
from unittest.mock import patch

from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.elica_connect_plus.const import (
    DOMAIN,
    CONF_DEVICE_ID,
    CONF_DEVICE_NAME,
)
from custom_components.elica_connect_plus.coordinator import InvalidAuth

DEVICE = {"id": "HOOD123", "name": "Cappa Cucina"}
USER_INPUT = {CONF_EMAIL: "a@b.c", CONF_PASSWORD: "pw"}

API = "custom_components.elica_connect_plus.config_flow.ElicaConnectAPI"


async def test_user_flow_single_device_creates_entry(hass):
    with patch(f"{API}.async_login"), patch(
        f"{API}.async_get_devices", return_value=[DEVICE]
    ), patch(
        "custom_components.elica_connect_plus.async_setup_entry", return_value=True
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] == "form"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )

    assert result["type"] == "create_entry"
    assert result["title"] == "Cappa Cucina"
    assert result["data"][CONF_DEVICE_ID] == "HOOD123"
    assert result["result"].unique_id == "HOOD123"


async def test_user_flow_invalid_auth_shows_error(hass):
    with patch(f"{API}.async_login", side_effect=InvalidAuth):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )

    assert result["type"] == "form"
    assert result["errors"] == {"base": "invalid_auth"}


async def test_user_flow_multiple_devices_shows_picker(hass):
    devices = [DEVICE, {"id": "HOOD456", "name": "Cappa Taverna"}]
    with patch(f"{API}.async_login"), patch(
        f"{API}.async_get_devices", return_value=devices
    ), patch(
        "custom_components.elica_connect_plus.async_setup_entry", return_value=True
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )
        assert result["type"] == "form"
        assert result["step_id"] == "select_device"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_DEVICE_ID: "HOOD456"}
        )

    assert result["type"] == "create_entry"
    assert result["data"][CONF_DEVICE_NAME] == "Cappa Taverna"


async def test_duplicate_device_aborts(hass):
    MockConfigEntry(
        domain=DOMAIN,
        unique_id="HOOD123",
        data={**USER_INPUT, CONF_DEVICE_ID: "HOOD123", CONF_DEVICE_NAME: "Cappa"},
    ).add_to_hass(hass)

    with patch(f"{API}.async_login"), patch(
        f"{API}.async_get_devices", return_value=[DEVICE]
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )

    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"


async def test_reauth_flow_updates_credentials(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="HOOD123",
        data={**USER_INPUT, CONF_DEVICE_ID: "HOOD123", CONF_DEVICE_NAME: "Cappa"},
    )
    entry.add_to_hass(hass)

    entry.async_start_reauth(hass)
    await hass.async_block_till_done()

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1
    assert flows[0]["step_id"] == "reauth_confirm"

    with patch(f"{API}.async_login"), patch(
        f"{API}.async_get_devices", return_value=[DEVICE]
    ), patch(
        "custom_components.elica_connect_plus.async_setup_entry", return_value=True
    ):
        result = await hass.config_entries.flow.async_configure(
            flows[0]["flow_id"],
            {CONF_EMAIL: "a@b.c", CONF_PASSWORD: "new-pw"},
        )

    assert result["type"] == "abort"
    assert result["reason"] == "reauth_successful"
    assert entry.data[CONF_PASSWORD] == "new-pw"
