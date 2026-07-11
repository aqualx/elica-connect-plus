"""Tests for the options flow and the option-gated features."""
from unittest.mock import patch

from homeassistant.components.fan import (
    ATTR_PRESET_MODE,
    DOMAIN as FAN_DOMAIN,
    SERVICE_SET_PRESET_MODE,
)

from custom_components.elica_connect_plus.const import (
    OPT_CAP_AIR_QUALITY,
    OPT_FAN_AUTO_VALUE,
    OPT_CAP_LIGHT_COLOR,
)

from tests.test_fan import setup_integration, COORD, DEVICE_STATE


async def test_options_flow_saves_codes(hass):
    entry = await setup_integration(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == "form"
    assert result["step_id"] == "init"

    with patch(f"{COORD}.ElicaConnectAPI.async_login"), patch(
        f"{COORD}.ElicaConnectAPI.async_get_device_state",
        return_value=DEVICE_STATE,
    ), patch(f"{COORD}.ElicaConnectCoordinator.async_start_mqtt"):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {OPT_CAP_AIR_QUALITY: 111, OPT_FAN_AUTO_VALUE: 2, OPT_CAP_LIGHT_COLOR: 97},
        )
        await hass.async_block_till_done()

    assert result["type"] == "create_entry"
    assert entry.options[OPT_CAP_AIR_QUALITY] == 111


async def test_air_quality_sensor_created_when_configured(hass):
    state = {**DEVICE_STATE, "dataModel": {**DEVICE_STATE["dataModel"], "112": 3}}
    with patch.dict(DEVICE_STATE, state, clear=True):
        await setup_integration(hass, options={OPT_CAP_AIR_QUALITY: 112})

    sensor = hass.states.get("sensor.cappa_cucina_air_quality")
    assert sensor is not None
    assert sensor.state == "fair"  # 3 → fair (enum 1-5)
    assert sensor.attributes["level"] == 3
    assert sensor.attributes["options"] == [
        "excellent", "good", "fair", "poor", "very_poor"
    ]


async def test_air_quality_sensor_unavailable_when_not_published(hass):
    # cap 112 not in the dataModel (sensor inactive): entity must be unavailable
    await setup_integration(hass, options={OPT_CAP_AIR_QUALITY: 112})
    sensor = hass.states.get("sensor.cappa_cucina_air_quality")
    assert sensor.state == "unavailable"


async def test_air_quality_sensor_absent_by_default(hass):
    await setup_integration(hass)
    assert hass.states.get("sensor.cappa_cucina_air_quality") is None


async def test_fan_auto_preset(hass):
    await setup_integration(hass, options={OPT_FAN_AUTO_VALUE: 2})

    fan = hass.states.get("fan.cappa_cucina_fan")
    assert fan.attributes.get("preset_modes") == [
        "auto", "low", "medium", "high", "boost"
    ]

    with patch(f"{COORD}.ElicaConnectAPI.async_send_command") as mock_cmd:
        await hass.services.async_call(
            FAN_DOMAIN,
            SERVICE_SET_PRESET_MODE,
            {"entity_id": "fan.cappa_cucina_fan", ATTR_PRESET_MODE: "auto"},
            blocking=True,
        )

    mock_cmd.assert_awaited_once()
    assert mock_cmd.call_args.args[1] == {64: 2}

    fan = hass.states.get("fan.cappa_cucina_fan")
    assert fan.state == "on"
    assert fan.attributes[ATTR_PRESET_MODE] == "auto"


async def test_fan_speed_presets_always_available(hass):
    await setup_integration(hass)
    fan = hass.states.get("fan.cappa_cucina_fan")
    # No Auto (option not set), but named speed presets are there
    assert fan.attributes.get("preset_modes") == ["low", "medium", "high", "boost"]

    with patch(f"{COORD}.ElicaConnectAPI.async_send_command") as mock_cmd:
        await hass.services.async_call(
            FAN_DOMAIN,
            SERVICE_SET_PRESET_MODE,
            {"entity_id": "fan.cappa_cucina_fan", ATTR_PRESET_MODE: "medium"},
            blocking=True,
        )

    mock_cmd.assert_awaited_once()
    assert mock_cmd.call_args.args[1] == {64: 1, 110: 2}

    fan = hass.states.get("fan.cappa_cucina_fan")
    assert fan.state == "on"
    assert fan.attributes[ATTR_PRESET_MODE] == "medium"
    assert fan.attributes["percentage"] == 50


async def test_light_color_temp_when_configured(hass):
    state = {**DEVICE_STATE, "dataModel": {**DEVICE_STATE["dataModel"], "96": 50, "97": 100}}
    with patch.dict(DEVICE_STATE, state, clear=True):
        await setup_integration(hass, options={OPT_CAP_LIGHT_COLOR: 97})

    light = hass.states.get("light.cappa_cucina_light")
    assert light is not None
    assert "color_temp" in light.attributes.get("supported_color_modes", [])
    # cap 97 = 100 → max kelvin (6500)
    assert light.attributes["color_temp_kelvin"] == 6500

    with patch(f"{COORD}.ElicaConnectAPI.async_send_command") as mock_cmd:
        await hass.services.async_call(
            "light",
            "turn_on",
            {
                "entity_id": "light.cappa_cucina_light",
                "color_temp_kelvin": 2700,
            },
            blocking=True,
        )

    mock_cmd.assert_awaited_once()
    sent = mock_cmd.call_args.args[1]
    assert sent[97] == 0  # 2700 K = warm end = 0%


async def test_light_effects_presets(hass):
    state = {**DEVICE_STATE, "dataModel": {**DEVICE_STATE["dataModel"], "96": 50, "97": 50}}
    with patch.dict(DEVICE_STATE, state, clear=True):
        await setup_integration(hass, options={OPT_CAP_LIGHT_COLOR: 97})

    light = hass.states.get("light.cappa_cucina_light")
    assert light.attributes["effect_list"] == [
        "very_warm", "warm", "neutral", "cool", "very_cool"
    ]
    # cap 97 = 50 → the current effect is reported as "neutral" (4600 K)
    assert light.attributes["effect"] == "neutral"
    assert light.attributes["color_temp_kelvin"] == 4600

    with patch(f"{COORD}.ElicaConnectAPI.async_send_command") as mock_cmd:
        await hass.services.async_call(
            "light",
            "turn_on",
            {"entity_id": "light.cappa_cucina_light", "effect": "very_warm"},
            blocking=True,
        )

    sent = mock_cmd.call_args.args[1]
    assert sent[97] == 0  # very_warm = warm end


async def test_light_no_effects_without_color_cap(hass):
    await setup_integration(hass)
    light = hass.states.get("light.cappa_cucina_light")
    assert light.attributes.get("effect_list") is None


async def test_ambient_light_created_when_configured(hass):
    from custom_components.elica_connect_plus.const import (
        OPT_CAP_AMBIENT_BRIGHTNESS,
        OPT_CAP_AMBIENT_COLOR,
    )

    state = {
        **DEVICE_STATE,
        "dataModel": {**DEVICE_STATE["dataModel"], "128": 19, "129": 50},
    }
    with patch.dict(DEVICE_STATE, state, clear=True):
        await setup_integration(
            hass,
            options={OPT_CAP_AMBIENT_BRIGHTNESS: 128, OPT_CAP_AMBIENT_COLOR: 129},
        )

    # Main light untouched
    assert hass.states.get("light.cappa_cucina_light") is not None

    ambient = hass.states.get("light.cappa_cucina_ambient_light")
    assert ambient is not None
    assert ambient.state == "on"  # brightness 19 > 0
    assert ambient.attributes["color_temp_kelvin"] == 4600  # 129=50 → neutral
    assert ambient.attributes["effect_list"] == [
        "very_warm", "warm", "neutral", "cool", "very_cool"
    ]

    with patch(f"{COORD}.ElicaConnectAPI.async_send_command") as mock_cmd:
        await hass.services.async_call(
            "light",
            "turn_on",
            {
                "entity_id": "light.cappa_cucina_ambient_light",
                "brightness": 255,
                "effect": "very_warm",
            },
            blocking=True,
        )

    sent = mock_cmd.call_args.args[1]
    assert sent == {128: 100, 129: 0}


async def test_ambient_light_absent_by_default(hass):
    await setup_integration(hass)
    assert hass.states.get("light.cappa_cucina_ambient_light") is None


async def test_keepalive_interval_from_options(hass):
    from datetime import timedelta
    from custom_components.elica_connect_plus.const import OPT_KEEPALIVE_MINUTES

    entry = await setup_integration(hass, options={OPT_KEEPALIVE_MINUTES: 2})
    coordinator = entry.runtime_data
    assert coordinator._mqtt_update_interval == timedelta(minutes=2)


async def test_keepalive_default_when_not_set(hass):
    from datetime import timedelta

    entry = await setup_integration(hass)
    coordinator = entry.runtime_data
    # default: previous fixed 300 s fallback
    assert coordinator._mqtt_update_interval == timedelta(seconds=300)


async def test_aggressive_keepalive_sends_noop_ping(hass):
    from custom_components.elica_connect_plus.const import (
        OPT_AGGRESSIVE_KEEPALIVE,
    )

    entry = await setup_integration(
        hass, options={OPT_AGGRESSIVE_KEEPALIVE: True}
    )
    coordinator = entry.runtime_data
    coordinator._mqtt_client = object()  # simulate active MQTT push

    with patch(
        f"{COORD}.ElicaConnectAPI.async_get_device_state",
        return_value=DEVICE_STATE,
    ), patch(f"{COORD}.ElicaConnectAPI.async_send_command") as mock_cmd:
        await coordinator.async_refresh()
        await hass.async_block_till_done()

    # No-op ping: echoes current light brightness (cap 96 = 0)
    mock_cmd.assert_awaited_once_with("HOOD123", {96: 0})
    coordinator._mqtt_client = None  # avoid unload calling disconnect on object()


async def test_no_ping_when_aggressive_disabled(hass):
    entry = await setup_integration(hass)
    coordinator = entry.runtime_data
    coordinator._mqtt_client = object()

    with patch(
        f"{COORD}.ElicaConnectAPI.async_get_device_state",
        return_value=DEVICE_STATE,
    ), patch(f"{COORD}.ElicaConnectAPI.async_send_command") as mock_cmd:
        await coordinator.async_refresh()
        await hass.async_block_till_done()

    mock_cmd.assert_not_awaited()
    coordinator._mqtt_client = None


async def test_timer_number_created_and_sets_value(hass):
    from custom_components.elica_connect_plus.const import OPT_CAP_TIMER

    state = {**DEVICE_STATE, "dataModel": {**DEVICE_STATE["dataModel"], "432": 0}}
    with patch.dict(DEVICE_STATE, state, clear=True):
        await setup_integration(hass, options={OPT_CAP_TIMER: 432})

    number = hass.states.get("number.cappa_cucina_timer")
    assert number is not None
    assert number.state == "0"

    with patch(f"{COORD}.ElicaConnectAPI.async_send_command") as mock_cmd:
        await hass.services.async_call(
            "number",
            "set_value",
            {"entity_id": "number.cappa_cucina_timer", "value": 10},
            blocking=True,
        )

    mock_cmd.assert_awaited_once_with("HOOD123", {432: 10})
    number = hass.states.get("number.cappa_cucina_timer")
    assert number.state == "10"  # optimistic


async def test_timer_number_absent_by_default(hass):
    await setup_integration(hass)
    assert hass.states.get("number.cappa_cucina_timer") is None


async def test_mqtt_host_port_from_options(hass):
    from custom_components.elica_connect_plus.const import (
        OPT_MQTT_HOST,
        OPT_MQTT_PORT,
    )

    entry = await setup_integration(
        hass,
        options={OPT_MQTT_HOST: "mqtt.example.com", OPT_MQTT_PORT: 1883},
    )
    coordinator = entry.runtime_data
    assert coordinator._mqtt_host == "mqtt.example.com"
    assert coordinator._mqtt_port == 1883


async def test_mqtt_host_port_defaults(hass):
    entry = await setup_integration(hass)
    coordinator = entry.runtime_data
    assert coordinator._mqtt_host == "cloudprodmqtt.elica.com"
    assert coordinator._mqtt_port == 8883
