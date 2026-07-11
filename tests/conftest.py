"""Shared fixtures for Elica Connect tests."""
import base64
import json
import time

import pytest

# pycares (aiohttp's async DNS resolver) lazily spawns a daemon thread the
# first time a ClientSession is created. Spawn it up-front so the plugin's
# lingering-thread check doesn't blame the first test that touches aiohttp.
try:
    import pycares

    pycares._shutdown_manager.start()
except Exception:  # pragma: no cover
    pass


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading custom integrations in all tests."""
    yield


def make_jwt(
    exp: float | None = None,
    mqtt_usr: str = "mqtt-user",
    mqtt_psw: str = "mqtt-pass",
) -> str:
    """Build an unsigned JWT like the Elica cloud returns."""
    if exp is None:
        exp = time.time() + 3600
    payload = {"exp": exp, "mqtt_usr": mqtt_usr, "mqtt_psw": mqtt_psw}
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    return f"eyJhbGciOiJIUzI1NiJ9.{body}.signature"
