"""Constants for Elica Connect integration."""

DOMAIN = "elica_connect_plus"
MANUFACTURER = "Elica S.p.A."

# Cloud API
API_BASE = "https://cloudprod.elica.com/eiot-api/v1"
API_OAUTH_TOKEN = f"{API_BASE}/oauth/token"
API_DEVICES = f"{API_BASE}/devices"
API_COMMANDS = f"{API_BASE}/devices/{{device_id}}/commands"
API_DEVICE_STATE = f"{API_BASE}/devices/{{device_id}}"

# OAuth2 client credentials (eiot platform, extracted via mitmproxy)
OAUTH_CLIENT_ID = "eiot-app"
OAUTH_CLIENT_SECRET = "VqwG1KTB77UeROu"
OAUTH_APP_UUID = "c48d13c2352cc536"

# Update interval (seconds)
SCAN_INTERVAL = 30

# Config entry keys
CONF_DEVICE_ID = "device_id"
CONF_DEVICE_NAME = "device_name"

# Hood capability codes (confirmed via mitmproxy on real device, dataModelIdx=8)
CAP_FAN_SPEED = 110    # 0=off, 1=low, 2=medium, 3=high (not used for boost)
CAP_FAN_MODE = 64      # 1=normal operation, 4=boost mode
CAP_LIGHT_BRIGHTNESS = 96  # light brightness 0–100 (%; 0=off)

# Fan speed levels (0=off, 1-3=normal, 4=boost)
FAN_SPEED_TO_PCT = {0: 0, 1: 25, 2: 50, 3: 75, 4: 100}

# Fan commands (capability payloads) as observed from app
FAN_CMD = {
    0: {64: 1, 110: 0},   # off
    1: {64: 1, 110: 1},   # low
    2: {64: 1, 110: 2},   # medium
    3: {64: 1, 110: 3},   # high
    4: {64: 4},            # boost
}

# Light
LIGHT_BRIGHTNESS_MAX_HA = 255
LIGHT_BRIGHTNESS_MAX_ELICA = 100  # capability 96: 0–100 (%)

# Command type
COMMAND_TYPE = "Hood"
COMMAND_TIMEOUT = 30000  # ms

# MQTT (cloud push, confirmed via APK reverse engineering + live capture)
MQTT_HOST = "cloudprodmqtt.elica.com"
MQTT_PORT = 8883
MQTT_TOPIC_STATE = "v1/device/{cuid}/statusjson"
# Fallback poll interval when MQTT is connected (5 min sanity check)
SCAN_INTERVAL_MQTT = 300

# Seconds to trust an optimistic (locally assumed) state before falling back
# to whatever the cloud reports. Slightly above the REST fallback interval
# is not needed: MQTT echoes commands within a couple of seconds; 40 s covers
# a slow REST round-trip.
OPTIMISTIC_TIMEOUT = 40

# ---------------------------------------------------------------------------
# Optional capabilities — codes NOT yet confirmed for dataModelIdx 8.
# These features are disabled until the real capability codes are entered in
# the integration Options (Settings → Devices & services → Elica Connect →
# Configure). See DISCOVERY.md for the procedure to find them.
# ---------------------------------------------------------------------------
OPT_CAP_AIR_QUALITY = "cap_air_quality"    # dataModel code of the AQ sensor
OPT_FAN_AUTO_VALUE = "fan_auto_value"      # value of cap 64 that means "auto"
OPT_CAP_LIGHT_COLOR = "cap_light_color"    # dataModel code of light color temp

# Tunable-white range assumed for the color capability (0–100 → warm→cold).
# Adjust after verifying real values from the app.
LIGHT_COLOR_MIN_KELVIN = 2700
LIGHT_COLOR_MAX_KELVIN = 6500

PRESET_AUTO = "auto"

# Named fan speed presets (slug → speed level 1-4); display names are
# localized via translations/ (state_attributes.preset_mode)
FAN_SPEED_PRESETS = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "boost": 4,
}

# Named color-temperature presets (exposed as light effects), warm → cold.
# Values are cap-97 percentages; kelvin equivalents with the default
# 2700–6500 K range: 2700 / 3650 / 4600 / 5550 / 6500.
# Slugs; display names localized via translations/ (state_attributes.effect)
LIGHT_EFFECTS = {
    "very_warm": 0,
    "warm": 25,
    "neutral": 50,
    "cool": 75,
    "very_cool": 100,
}

# Air quality scale (capability 112, confirmed on dataModelIdx 8):
# the Elica app shows Ottima/Buona/Media/Scarsa/Pessima for 1–5.
# Slugs; display names localized via translations/ (enum sensor states).
# Elica app labels: Ottima/Buona/Media/Scarsa/Pessima for 1-5.
AIR_QUALITY_LEVELS = {
    1: "excellent",
    2: "good",
    3: "fair",
    4: "poor",
    5: "very_poor",
}

# Ambient light (secondary light strip), codes to be confirmed — see Options
OPT_CAP_AMBIENT_BRIGHTNESS = "cap_ambient_brightness"
OPT_CAP_AMBIENT_COLOR = "cap_ambient_color"

# Keep-alive REST poll interval (minutes) once MQTT push is active.
# These hood models can drop off Wi-Fi due to aggressive power management;
# a shorter periodic cloud poll helps keep the connection alive.
OPT_KEEPALIVE_MINUTES = "keepalive_minutes"
DEFAULT_KEEPALIVE_MINUTES = 5  # matches the previous fixed 300 s fallback

# Aggressive keep-alive: on every keep-alive cycle, also send a no-op
# command (echo of the current light brightness) so the hood itself must
# wake up and ack over MQTT — not just the cloud. Off by default.
OPT_AGGRESSIVE_KEEPALIVE = "aggressive_keepalive"

# Native hood timer (auto-off countdown in minutes). Confirmed code 432 on
# Elica Illusion (dataModelIdx 8): writing N starts an N-minute countdown
# handled by the firmware; the value counts down on its own (10→9→…→0).
# 0 = timer off. Optional, enabled via Options.
OPT_CAP_TIMER = "cap_timer"
TIMER_MAX_MINUTES = 240

# The Elica cloud MQTT broker the hood publishes to. Overridable in Options
# so that, if Elica ever moves the broker, users can point the integration
# to the new host/port without waiting for a new release.
OPT_MQTT_HOST = "mqtt_host"
OPT_MQTT_PORT = "mqtt_port"
DEFAULT_MQTT_HOST = MQTT_HOST
DEFAULT_MQTT_PORT = MQTT_PORT
