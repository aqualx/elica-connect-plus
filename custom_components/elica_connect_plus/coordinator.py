"""DataUpdateCoordinator for Elica Connect."""
from __future__ import annotations

import asyncio
import base64
import json
import logging
import time
from datetime import timedelta
from typing import Any

import aiohttp

try:
    import paho.mqtt.client as mqtt
except ImportError:  # pragma: no cover
    mqtt = None

from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util
from homeassistant.util.ssl import client_context

from .const import (
    DOMAIN,
    CAP_LIGHT_BRIGHTNESS,
    SCAN_INTERVAL,
    SCAN_INTERVAL_MQTT,
    API_OAUTH_TOKEN,
    API_DEVICES,
    API_COMMANDS,
    API_DEVICE_STATE,
    COMMAND_TYPE,
    COMMAND_TIMEOUT,
    OAUTH_CLIENT_ID,
    OAUTH_CLIENT_SECRET,
    OAUTH_APP_UUID,
    MQTT_HOST,
    MQTT_PORT,
    MQTT_TOPIC_STATE,
)

_LOGGER = logging.getLogger(__name__)

# Refresh the token this many seconds before its JWT `exp` claim.
TOKEN_EXPIRY_MARGIN = 120

def _decode_jwt(token: str) -> dict:
    """Decode JWT payload (no signature verification)."""
    payload = token.split(".")[1]
    payload += "=" * (-len(payload) % 4)
    return json.loads(base64.urlsafe_b64decode(payload))


def _make_mqtt_client(client_id: str):
    """Create paho-mqtt client, compatible with paho-mqtt 1.x and 2.x."""
    try:
        # paho-mqtt >= 2.0
        return mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION1,
            client_id=client_id,
            protocol=mqtt.MQTTv311,
        )
    except AttributeError:
        # paho-mqtt < 2.0
        return mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv311)


def _mqtt_payload_text(payload: bytes | bytearray | str) -> str:
    """Return MQTT payload as displayable text for UI debug logging."""
    if isinstance(payload, str):
        return payload
    return bytes(payload).decode("utf-8", errors="replace")


def _mqtt_data_model(payload: Any) -> dict | None:
    """Extract a dataModel object from known Elica MQTT payload shapes."""
    if isinstance(payload, dict):
        data_model = payload.get("dataModel")
        return data_model if isinstance(data_model, dict) else None
    if isinstance(payload, list):
        for item in payload:
            data_model = _mqtt_data_model(item)
            if data_model is not None:
                return data_model
    return None


def _is_running_in_loop(loop: asyncio.AbstractEventLoop) -> bool:
    """Return whether the current code is running on the given event loop."""
    try:
        return asyncio.get_running_loop() is loop
    except RuntimeError:
        return False


class InvalidAuth(Exception):
    """Raised when credentials are rejected."""


class ElicaConnectAPI:
    """Low-level REST client for cloudprod.elica.com/eiot-api/v1."""

    def __init__(self, session: aiohttp.ClientSession, email: str, password: str) -> None:
        self._session = session
        self._email = email
        self._password = password
        self._token: str | None = None
        self._token_exp: float = 0.0

    async def async_login(self) -> str:
        """Authenticate via OAuth2 password grant and return the Bearer token."""
        payload = {
            "grant_type": "password",
            "username": self._email,
            "password": self._password,
            "scope": "default",
            "app_uuid": OAUTH_APP_UUID,
        }
        async with self._session.post(
            API_OAUTH_TOKEN,
            data=payload,
            auth=aiohttp.BasicAuth(OAUTH_CLIENT_ID, OAUTH_CLIENT_SECRET),
        ) as resp:
            if resp.status in (400, 401, 403):
                raise InvalidAuth("Invalid credentials")
            resp.raise_for_status()
            data = await resp.json()

        token = data.get("access_token")
        if not token:
            raise InvalidAuth(f"Token not found in login response: {list(data.keys())}")

        self._token = token
        # Track expiry so we can refresh proactively instead of eating a 401.
        try:
            self._token_exp = float(_decode_jwt(token).get("exp", 0))
        except Exception:  # noqa: BLE001 - malformed JWT: fall back to reactive 401 handling
            self._token_exp = 0.0
        return token

    @property
    def token(self) -> str | None:
        return self._token

    def _token_expired(self) -> bool:
        return bool(self._token_exp) and time.time() >= self._token_exp - TOKEN_EXPIRY_MARGIN

    @property
    def _auth_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

    async def _ensure_token(self) -> None:
        if not self._token or self._token_expired():
            await self.async_login()

    async def _request(
        self,
        method: str,
        url: str,
        *,
        json_payload: dict | None = None,
        expect_json: bool = True,
    ) -> Any:
        """Perform an authenticated request with a single re-login retry on 401."""
        await self._ensure_token()
        for attempt in (0, 1):
            async with self._session.request(
                method, url, json=json_payload, headers=self._auth_headers
            ) as resp:
                if resp.status == 401 and attempt == 0:
                    _LOGGER.debug("Got 401 on %s %s, re-authenticating", method, url)
                    await self.async_login()
                    continue
                resp.raise_for_status()
                if expect_json:
                    return await resp.json()
                return None
        return None  # unreachable, keeps type checkers happy

    async def async_get_devices(self) -> list[dict]:
        """Return list of devices associated to the account."""
        data = await self._request("GET", API_DEVICES)
        if isinstance(data, list):
            return data
        return data.get("devices") or data.get("data") or []

    async def async_get_device_state(self, device_id: str) -> dict:
        """Return full device JSON (includes dataModel and filters)."""
        return await self._request("GET", API_DEVICE_STATE.format(device_id=device_id))

    async def async_send_command(self, device_id: str, capabilities: dict) -> None:
        """Send a capability command to the device."""
        payload = {
            "async": True,
            "capabilities": {str(k): v for k, v in capabilities.items()},
            "name": "capabilities",
            "timeout": COMMAND_TIMEOUT,
            "type": COMMAND_TYPE,
        }
        _LOGGER.debug("Sending command to %s: %s", device_id, capabilities)
        await self._request(
            "POST",
            API_COMMANDS.format(device_id=device_id),
            json_payload=payload,
            expect_json=False,
        )


class ElicaConnectCoordinator(DataUpdateCoordinator):
    """Coordinator: MQTT push updates + REST fallback poll."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry,
        api: ElicaConnectAPI,
        device_id: str,
        device_name: str,
        keepalive_minutes: int = 0,
        aggressive_keepalive: bool = False,
        mqtt_host: str = MQTT_HOST,
        mqtt_port: int = MQTT_PORT,
    ) -> None:
        # config_entry passed explicitly: the implicit context lookup is
        # deprecated and removed in HA 2026.8.
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=timedelta(seconds=SCAN_INTERVAL),
        )
        # REST poll cadence once MQTT push is active: acts as a keep-alive
        # against the hood's Wi-Fi power management. 0 = default fallback.
        self._mqtt_update_interval = (
            timedelta(minutes=keepalive_minutes)
            if keepalive_minutes > 0
            else timedelta(seconds=SCAN_INTERVAL_MQTT)
        )
        self._aggressive_keepalive = aggressive_keepalive
        self._mqtt_host = mqtt_host or MQTT_HOST
        self._mqtt_port = mqtt_port or MQTT_PORT
        self.api = api
        self.device_id = device_id
        self.device_name = device_name
        self._device_raw: dict = {}
        # cuid extracted from REST API response (needed for MQTT topic)
        self._cuid: str | None = None
        # Full merged state (REST full state + MQTT deltas)
        self._state_cache: dict[int, int] = {}
        # paho-mqtt client (paho manages its own network thread via loop_start)
        self._mqtt_client = None
        # Set when the broker rejects our (expired) credentials; the next
        # REST poll refreshes the token and pushes new credentials to paho.
        self._mqtt_needs_reauth = False
        self._debug_ui_enabled = False
        self._latest_raw_mqtt_payload: str | None = None
        self._latest_raw_mqtt_timestamp: str | None = None
        self._debug_signal = f"{DOMAIN}_debug_updated_{entry.entry_id}"

    @property
    def device_raw(self) -> dict:
        return self._device_raw

    @property
    def mqtt_active(self) -> bool:
        """Whether the MQTT push client has been started."""
        return self._mqtt_client is not None

    @property
    def debug_signal(self) -> str:
        """Dispatcher signal for UI debug log updates."""
        return self._debug_signal

    @property
    def debug_ui_enabled(self) -> bool:
        """Whether UI debug logging is enabled."""
        return self._debug_ui_enabled

    @property
    def latest_raw_mqtt_payload(self) -> str | None:
        """Return the latest raw MQTT payload captured while debugging is enabled."""
        return self._latest_raw_mqtt_payload

    @property
    def latest_raw_mqtt_timestamp(self) -> str | None:
        """Return the timestamp for the latest captured raw MQTT payload."""
        return self._latest_raw_mqtt_timestamp

    def set_debug_ui_enabled(self, enabled: bool) -> None:
        """Enable/disable UI debug logging from the switch entity."""
        enabled = bool(enabled)
        if self._debug_ui_enabled == enabled:
            return
        self._debug_ui_enabled = enabled
        if not _is_running_in_loop(self.hass.loop):
            self.hass.loop.call_soon_threadsafe(
                async_dispatcher_send, self.hass, self._debug_signal
            )
            return
        async_dispatcher_send(self.hass, self._debug_signal)

    def update_latest_raw_mqtt_payload(self, payload: str) -> None:
        """Capture the latest raw MQTT payload when UI debugging is enabled."""
        if not self._debug_ui_enabled:
            return
        if not _is_running_in_loop(self.hass.loop):
            self.hass.loop.call_soon_threadsafe(
                self._update_latest_raw_mqtt_payload_on_loop, payload
            )
            return
        self._update_latest_raw_mqtt_payload_on_loop(payload)

    def _update_latest_raw_mqtt_payload_on_loop(self, payload: str) -> None:
        """Update raw MQTT payload state from the Home Assistant event loop."""
        self._latest_raw_mqtt_payload = payload
        self._latest_raw_mqtt_timestamp = dt_util.utcnow().isoformat()
        async_dispatcher_send(self.hass, self._debug_signal)

    async def _async_update_data(self) -> dict:
        """Fetch device state from REST API (fallback/sanity check)."""
        try:
            raw = await self.api.async_get_device_state(self.device_id)
        except InvalidAuth as err:
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except aiohttp.ClientResponseError as err:
            raise UpdateFailed(f"API error {err.status}: {err.message}") from err
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Network error: {err}") from err

        self._device_raw = raw

        # Extract cuid for MQTT (available after first REST call)
        if not self._cuid:
            self._cuid = raw.get("cuid") or raw.get("serialNumber")

        # If the broker kicked us out because the JWT expired, the login that
        # just happened (or the still-valid token) carries fresh MQTT creds:
        # push them into paho so its auto-reconnect can succeed.
        if self._mqtt_needs_reauth:
            self._refresh_mqtt_credentials()

        data_model = raw.get("dataModel") or {}
        new_state = {int(k): v for k, v in data_model.items()}
        # Merge REST data into cache (REST is authoritative for full state)
        self._state_cache.update(new_state)

        # Aggressive keep-alive: echo the current light brightness back to
        # the hood as a no-op command. Unlike the REST poll (cloud only),
        # a command forces a full cloud→MQTT→device round-trip, keeping the
        # hood's Wi-Fi awake. Fire-and-forget so the poll isn't delayed.
        if self._aggressive_keepalive and self._mqtt_client is not None:
            value = self._state_cache.get(CAP_LIGHT_BRIGHTNESS)
            if value is not None:
                self.hass.async_create_task(self._async_keepalive_ping(value))

        return dict(self._state_cache)

    # ------------------------------------------------------------------ MQTT

    def _mqtt_credentials(self) -> tuple[str, str] | None:
        """Extract MQTT username/password from the current OAuth JWT."""
        token = self.api.token
        if not token:
            return None
        try:
            jwt = _decode_jwt(token)
        except Exception as ex:  # noqa: BLE001
            _LOGGER.warning("Elica MQTT: JWT decode failed: %s", ex)
            return None
        usr, psw = jwt.get("mqtt_usr"), jwt.get("mqtt_psw")
        if not usr or not psw:
            return None
        return usr, psw

    def _refresh_mqtt_credentials(self) -> None:
        """Feed fresh credentials to the running paho client."""
        creds = self._mqtt_credentials()
        if not creds or not self._mqtt_client:
            return
        self._mqtt_client.username_pw_set(*creds)
        self._mqtt_needs_reauth = False
        _LOGGER.debug("Elica MQTT: credentials refreshed, reconnect will retry")

    def async_start_mqtt(self) -> None:
        """Start MQTT subscription for real-time push updates.

        Called from the HA event loop after first_refresh succeeds.
        paho-mqtt runs its own network thread (loop_start) with built-in
        reconnect/backoff, so a broker outage at startup is recovered
        automatically.
        """
        if mqtt is None:
            _LOGGER.warning("Elica MQTT: paho-mqtt not available, push updates disabled")
            return
        if not self._cuid:
            _LOGGER.warning("Elica MQTT: cuid not available, skipping MQTT setup")
            return

        creds = self._mqtt_credentials()
        if not creds:
            _LOGGER.warning("Elica MQTT: credentials not in JWT, skipping MQTT setup")
            return

        topic = MQTT_TOPIC_STATE.format(cuid=self._cuid)
        _LOGGER.debug("Elica MQTT: subscribing to %s", topic)

        # Switch to the keep-alive REST poll now that MQTT is active
        self.update_interval = self._mqtt_update_interval
        _LOGGER.debug(
            "Elica keep-alive poll every %s", self._mqtt_update_interval
        )

        def on_connect(client, userdata, flags, rc):
            rc_val = rc if isinstance(rc, int) else getattr(rc, "value", 0)
            if rc_val == 0:
                self._mqtt_needs_reauth = False
                client.subscribe(topic, qos=1)
                _LOGGER.debug("Elica MQTT: connected and subscribed to %s", topic)
            elif rc_val in (4, 5):  # bad user/password, not authorized
                # JWT expired: flag it and force an early REST poll, which
                # re-logins and pushes fresh credentials (see _async_update_data).
                self._mqtt_needs_reauth = True
                _LOGGER.info(
                    "Elica MQTT: auth rejected (rc=%s), refreshing token", rc_val
                )
                self.hass.loop.call_soon_threadsafe(
                    lambda: self.hass.async_create_task(self.async_request_refresh())
                )
            else:
                _LOGGER.warning("Elica MQTT: connection refused rc=%s", rc_val)

        def on_disconnect(client, userdata, rc):
            _LOGGER.debug("Elica MQTT: disconnected rc=%s", rc)

        def on_message(client, userdata, msg):
            raw_payload = _mqtt_payload_text(msg.payload)
            self.update_latest_raw_mqtt_payload(raw_payload)
            try:
                payload = json.loads(raw_payload)
                # State payload: [{"dataModel": {"64": 1, "110": 0, ...}}]
                data_model = _mqtt_data_model(payload)
                if data_model is None:
                    _LOGGER.debug("Elica MQTT: message without dataModel: %s", payload)
                    return
                self._state_cache.update({int(k): v for k, v in data_model.items()})
                new_data = dict(self._state_cache)
                # Push update to HA entities from the MQTT thread
                self.hass.loop.call_soon_threadsafe(
                    self.async_set_updated_data, new_data
                )
                _LOGGER.debug("Elica MQTT: state update %s", data_model)
            except Exception as ex:  # noqa: BLE001
                _LOGGER.debug("Elica MQTT: message parse error: %s", ex)

        client = _make_mqtt_client(creds[0])
        client.username_pw_set(*creds)
        # HA's cached client context: created off-loop, avoids the blocking
        # load_default_certs/set_default_verify_paths call in the event loop.
        client.tls_set_context(client_context())
        client.reconnect_delay_set(min_delay=1, max_delay=120)
        client.on_connect = on_connect
        client.on_disconnect = on_disconnect
        client.on_message = on_message
        self._mqtt_client = client

        # connect_async + loop_start: non-blocking, retries forever with
        # backoff even if the first connection attempt fails.
        client.connect_async(self._mqtt_host, self._mqtt_port, keepalive=60)
        client.loop_start()
        _LOGGER.debug(
            "Elica MQTT: network loop started for cuid=%s on %s:%s",
            self._cuid, self._mqtt_host, self._mqtt_port,
        )

    def stop_mqtt(self) -> None:
        """Disconnect MQTT client (called on integration unload)."""
        if self._mqtt_client:
            try:
                self._mqtt_client.disconnect()
                self._mqtt_client.loop_stop()
            except Exception:  # noqa: BLE001
                pass
            self._mqtt_client = None

    async def _async_keepalive_ping(self, light_value: int) -> None:
        """Send a no-op command (current light brightness) to wake the hood."""
        try:
            await self.api.async_send_command(
                self.device_id, {CAP_LIGHT_BRIGHTNESS: light_value}
            )
            _LOGGER.debug("Elica keep-alive ping sent ({%s: %s})",
                          CAP_LIGHT_BRIGHTNESS, light_value)
        except Exception as ex:  # noqa: BLE001 - keep-alive must never break polling
            _LOGGER.debug("Elica keep-alive ping failed: %s", ex)
