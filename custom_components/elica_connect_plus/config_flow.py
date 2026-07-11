"""Config flow for Elica Connect."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from homeassistant.core import callback

from .const import (
    DOMAIN,
    CONF_DEVICE_ID,
    CONF_DEVICE_NAME,
    OPT_CAP_AIR_QUALITY,
    OPT_FAN_AUTO_VALUE,
    OPT_CAP_LIGHT_COLOR,
    OPT_CAP_AMBIENT_BRIGHTNESS,
    OPT_CAP_AMBIENT_COLOR,
    OPT_KEEPALIVE_MINUTES,
    DEFAULT_KEEPALIVE_MINUTES,
    OPT_AGGRESSIVE_KEEPALIVE,
    OPT_CAP_TIMER,
    OPT_MQTT_HOST,
    OPT_MQTT_PORT,
    DEFAULT_MQTT_HOST,
    DEFAULT_MQTT_PORT,
)
from .coordinator import ElicaConnectAPI, InvalidAuth

_LOGGER = logging.getLogger(__name__)

USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class ElicaConnectConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle setup from the HA UI."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> "ElicaConnectOptionsFlow":
        return ElicaConnectOptionsFlow()

    def __init__(self) -> None:
        self._email: str = ""
        self._password: str = ""
        self._api: ElicaConnectAPI | None = None
        self._devices: list[dict] = []

    async def _async_validate_login(self) -> dict[str, str]:
        """Try to log in and fetch devices; return an errors dict."""
        session = async_get_clientsession(self.hass)
        self._api = ElicaConnectAPI(session, self._email, self._password)
        try:
            await self._api.async_login()
            self._devices = await self._api.async_get_devices()
        except InvalidAuth:
            return {"base": "invalid_auth"}
        except aiohttp.ClientError:
            return {"base": "cannot_connect"}
        except Exception:  # noqa: BLE001
            _LOGGER.exception("Unexpected error during login")
            return {"base": "unknown"}
        return {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Step 1: ask for email and password."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._email = user_input[CONF_EMAIL]
            self._password = user_input[CONF_PASSWORD]
            errors = await self._async_validate_login()

            if not errors:
                if len(self._devices) == 0:
                    errors["base"] = "no_devices"
                elif len(self._devices) == 1:
                    return await self._async_create_entry(self._devices[0])
                else:
                    return await self.async_step_select_device()

        return self.async_show_form(
            step_id="user",
            data_schema=USER_SCHEMA,
            errors=errors,
        )

    async def async_step_select_device(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Step 2 (only if multiple devices): pick the hood."""
        if user_input is not None:
            device_id = user_input[CONF_DEVICE_ID]
            device = next(
                (d for d in self._devices if self._device_id(d) == device_id), None
            )
            if device:
                return await self._async_create_entry(device)

        device_options = {
            self._device_id(d): self._device_name(d) for d in self._devices
        }

        return self.async_show_form(
            step_id="select_device",
            data_schema=vol.Schema(
                {vol.Required(CONF_DEVICE_ID): vol.In(device_options)}
            ),
        )

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> config_entries.ConfigFlowResult:
        """Triggered by ConfigEntryAuthFailed: ask for new credentials."""
        self._email = entry_data.get(CONF_EMAIL, "")
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Validate the new password and update the existing entry."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._email = user_input[CONF_EMAIL]
            self._password = user_input[CONF_PASSWORD]
            errors = await self._async_validate_login()

            if not errors:
                entry = self._get_reauth_entry()
                return self.async_update_reload_and_abort(
                    entry,
                    data={
                        **entry.data,
                        CONF_EMAIL: self._email,
                        CONF_PASSWORD: self._password,
                    },
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_EMAIL, default=self._email): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )

    def _get_reauth_entry(self) -> config_entries.ConfigEntry:
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        assert entry is not None
        return entry

    async def _async_create_entry(self, device: dict) -> config_entries.ConfigFlowResult:
        device_id = self._device_id(device)
        device_name = self._device_name(device)

        # One entry per hood: abort if this device is already configured.
        await self.async_set_unique_id(device_id)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=device_name,
            data={
                CONF_EMAIL: self._email,
                CONF_PASSWORD: self._password,
                CONF_DEVICE_ID: device_id,
                CONF_DEVICE_NAME: device_name,
            },
        )

    @staticmethod
    def _device_id(device: dict) -> str:
        return str(
            device.get("id")
            or device.get("deviceId")
            or device.get("serialNumber")
            or device.get("serial")
            or ""
        )

    @staticmethod
    def _device_name(device: dict) -> str:
        return str(
            device.get("name")
            or device.get("deviceName")
            or device.get("alias")
            or device.get("id")
            or "Elica Hood"
        )


# HA >= 2025.8 provides OptionsFlowWithReload, which reloads the config
# entry automatically after options are saved. Using it (instead of a manual
# update listener) is required going forward: combining an update listener
# with config-flow reloading methods is deprecated since HA 2026.6 and
# becomes an error in 2026.12. On older HA we fall back to plain
# OptionsFlow + the listener registered in __init__.py.
HAS_OPTIONS_FLOW_WITH_RELOAD = hasattr(config_entries, "OptionsFlowWithReload")
_OptionsFlowBase = (
    config_entries.OptionsFlowWithReload
    if HAS_OPTIONS_FLOW_WITH_RELOAD
    else config_entries.OptionsFlow
)


class ElicaConnectOptionsFlow(_OptionsFlowBase):
    """Advanced options: capability codes for features not yet mapped.

    All fields default to 0 = disabled. Enter the dataModel codes discovered
    with the procedure in DISCOVERY.md to enable the corresponding feature.
    """

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        opts = self.config_entry.options
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        OPT_CAP_AIR_QUALITY,
                        default=opts.get(OPT_CAP_AIR_QUALITY, 0),
                    ): vol.All(vol.Coerce(int), vol.Range(min=0, max=999)),
                    vol.Optional(
                        OPT_FAN_AUTO_VALUE,
                        default=opts.get(OPT_FAN_AUTO_VALUE, 0),
                    ): vol.All(vol.Coerce(int), vol.Range(min=0, max=999)),
                    vol.Optional(
                        OPT_CAP_LIGHT_COLOR,
                        default=opts.get(OPT_CAP_LIGHT_COLOR, 0),
                    ): vol.All(vol.Coerce(int), vol.Range(min=0, max=999)),
                    vol.Optional(
                        OPT_CAP_AMBIENT_BRIGHTNESS,
                        default=opts.get(OPT_CAP_AMBIENT_BRIGHTNESS, 0),
                    ): vol.All(vol.Coerce(int), vol.Range(min=0, max=999)),
                    vol.Optional(
                        OPT_CAP_AMBIENT_COLOR,
                        default=opts.get(OPT_CAP_AMBIENT_COLOR, 0),
                    ): vol.All(vol.Coerce(int), vol.Range(min=0, max=999)),
                    vol.Optional(
                        OPT_CAP_TIMER,
                        default=opts.get(OPT_CAP_TIMER, 0),
                    ): vol.All(vol.Coerce(int), vol.Range(min=0, max=999)),
                    vol.Optional(
                        OPT_KEEPALIVE_MINUTES,
                        default=opts.get(
                            OPT_KEEPALIVE_MINUTES, DEFAULT_KEEPALIVE_MINUTES
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=60)),
                    vol.Optional(
                        OPT_AGGRESSIVE_KEEPALIVE,
                        default=opts.get(OPT_AGGRESSIVE_KEEPALIVE, False),
                    ): bool,
                    vol.Optional(
                        OPT_MQTT_HOST,
                        default=opts.get(OPT_MQTT_HOST, DEFAULT_MQTT_HOST),
                    ): str,
                    vol.Optional(
                        OPT_MQTT_PORT,
                        default=opts.get(OPT_MQTT_PORT, DEFAULT_MQTT_PORT),
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=65535)),
                }
            ),
        )
