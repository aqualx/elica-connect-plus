"""Tests for the ElicaConnectAPI REST client."""
import time

import pytest
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from custom_components.elica_connect_plus.const import (
    API_DEVICES,
    API_OAUTH_TOKEN,
)
from custom_components.elica_connect_plus.coordinator import (
    ElicaConnectAPI,
    InvalidAuth,
    _decode_jwt,
)

from tests.conftest import make_jwt


def test_decode_jwt_roundtrip():
    token = make_jwt(exp=1234567890.0)
    payload = _decode_jwt(token)
    assert payload["exp"] == 1234567890.0
    assert payload["mqtt_usr"] == "mqtt-user"
    assert payload["mqtt_psw"] == "mqtt-pass"


async def test_login_stores_token_and_expiry(hass, aioclient_mock):
    token = make_jwt(exp=time.time() + 3600)
    aioclient_mock.post(API_OAUTH_TOKEN, json={"access_token": token})

    api = ElicaConnectAPI(async_get_clientsession(hass), "a@b.c", "pw")
    assert await api.async_login() == token
    assert api.token == token
    assert not api._token_expired()


async def test_login_invalid_credentials(hass, aioclient_mock):
    aioclient_mock.post(API_OAUTH_TOKEN, status=401)

    api = ElicaConnectAPI(async_get_clientsession(hass), "a@b.c", "wrong")
    with pytest.raises(InvalidAuth):
        await api.async_login()


async def test_get_devices_parses_list_and_dict(hass, aioclient_mock):
    token = make_jwt()
    aioclient_mock.post(API_OAUTH_TOKEN, json={"access_token": token})
    aioclient_mock.get(API_DEVICES, json=[{"id": "X1"}])

    api = ElicaConnectAPI(async_get_clientsession(hass), "a@b.c", "pw")
    devices = await api.async_get_devices()
    assert devices == [{"id": "X1"}]

    # dict-shaped response
    aioclient_mock.clear_requests()
    aioclient_mock.post(API_OAUTH_TOKEN, json={"access_token": token})
    aioclient_mock.get(API_DEVICES, json={"devices": [{"id": "X2"}]})
    api2 = ElicaConnectAPI(async_get_clientsession(hass), "a@b.c", "pw")
    assert await api2.async_get_devices() == [{"id": "X2"}]


async def test_expired_token_triggers_proactive_relogin(hass, aioclient_mock):
    """A token past its exp claim must be refreshed before the request."""
    expired = make_jwt(exp=time.time() - 10)
    fresh = make_jwt(exp=time.time() + 3600)

    aioclient_mock.post(API_OAUTH_TOKEN, json={"access_token": fresh})
    aioclient_mock.get(API_DEVICES, json=[])

    api = ElicaConnectAPI(async_get_clientsession(hass), "a@b.c", "pw")
    # Simulate a stale session from hours ago
    api._token = expired
    api._token_exp = time.time() - 10

    await api.async_get_devices()

    # One POST to the token endpoint must have happened before the GET
    login_calls = [c for c in aioclient_mock.mock_calls if str(c[1]) == API_OAUTH_TOKEN]
    assert len(login_calls) == 1
    assert api.token == fresh
