# Discovering your hood's capability codes

🇮🇹 [Italiano](DISCOVERY.it.md) · 🇩🇪 [Deutsch](DISCOVERY.de.md) · 🇪🇸 [Español](DISCOVERY.es.md) · 🇫🇷 [Français](DISCOVERY.fr.md)


🇮🇹 [Versione italiana](DISCOVERY.it.md)

The Elica cloud API represents every hood function as a `code: value` pair
in the `dataModel` field. The integration works with **every Elica Connect
hood**; this page is the built-in *code finder* to enable model-specific
features. Confirmed codes for the **Elica Illusion** (dataModelIdx 8):

| Code | Function | Values |
|------|----------|--------|
| 64 | Fan mode | 1=normal, 4=boost, 16=auto (values suggest a bitmask) |
| 96 | Main light brightness | 0–100 (%; 0=off) |
| 97 | Main light color (tunable white) | 0=warm – 100=cold |
| 100 | Ambient light brightness | 0–100; the ambient light has no color control |
| 110 | Fan speed | 0=off, 1–3 (also reported while in auto) |
| 112 | Air quality | 1=excellent … 5=very poor |
| 432 | Auto-off timer | minutes; writing N starts an N-minute firmware countdown, value counts down to 0 |

Other hood models may use different codes: this integration supports them
via the Options — you only need to identify them once.

## Method 1 — Live MQTT log sniffing (recommended)

The integration receives *every* dataModel code via MQTT push, including
unknown ones. With debug logging enabled, each change appears in the HA log
in real time:

1. Add to `configuration.yaml` and restart:
   ```yaml
   logger:
     default: warning
     logs:
       custom_components.elica_connect_plus: debug
   ```
2. Watch the log (`tail -f /config/home-assistant.log | grep "Elica MQTT"`).
3. In the Elica app, change **one** thing at a time (toggle auto, move a
   slider) and wait for the matching line:
   `Elica MQTT: state update {'97': 100}`
4. The code that changed is the one you're looking for. Enter it in
   *Settings → Devices & services → Elica Connect Plus → Configure*.
5. For the air quality sensor, don't touch anything: blow at the grille or
   spray something nearby and watch which code moves on its own.

## Method 2 — Diagnostics diff

No log access needed: download the diagnostics (device page → ⋮ →
Download diagnostics), change one thing in the app, download again after
~10 seconds and diff the `state_cache` sections:
`diff <(jq .state_cache before.json) <(jq .state_cache after.json)`

## Method 3 — mitmproxy

To also see how the app *writes* commands: run mitmproxy, proxy your phone
through it (the app has no certificate pinning) and watch
`POST /eiot-api/v1/devices/{id}/commands` — the `capabilities` field
contains the exact codes and values.

## Field notes — Elica Illusion (dataModelIdx 8)

- Code **112** does not appear in the full dataModel dump at rest: it is
  published over MQTT only while the sensor is active (typically in auto
  mode). After an HA restart the sensor stays `unavailable` until the
  first value arrives.
- While in auto mode, the real speed keeps being reported in code 110:
  HA shows both the `auto` preset and the current percentage.
- REST commands use the `device_id` (e.g. `Utya8g`), the MQTT topic uses
  the `cuid` (e.g. `J2BDYM2XTVYC`): different identifiers, both correct.
- Code **5** often appears in updates as 0 alongside other changes: it
  looks like a firmware transition flag and can be ignored.

Found codes for a different model? Please open a **Capability report**
issue so they can be documented for everyone.
